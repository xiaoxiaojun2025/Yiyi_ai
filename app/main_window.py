import os
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QStackedWidget, QInputDialog, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer

from .core import DataManager, ChatWorker, build_messages, PDFReportGenerator
from .ui.pages import SidebarWidget, ChatWidget, MeasurePage
from config.config import Config


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI 智能问诊助手")
        self.setMinimumSize(900, 600)
        self.resize(Config.WINDOW_WIDTH, Config.WINDOW_HEIGHT)

        self.data_manager = DataManager()
        self.pdf_generator = PDFReportGenerator()
        self.sidebar_visible = True
        self._worker: ChatWorker | None = None
        self._streaming_bubble = None
        self._streaming_conv_id: str | None = None
        self._streaming_content: str = ""
        self._is_measure_page = False
        self._pending_text: str = ""

        self._setup_ui()

        if self.data_manager.get_all_conversations():
            first_conv = self.data_manager.get_all_conversations()[0]
            self._switch_conversation(first_conv.id)
        else:
            self._new_conversation()

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Sidebar
        self.sidebar = SidebarWidget(self.data_manager)
        self.sidebar.conversation_selected.connect(self._switch_conversation)
        self.sidebar.new_conversation_requested.connect(self._new_conversation)
        self.sidebar.export_report_requested.connect(self._on_export_report)
        main_layout.addWidget(self.sidebar)

        # Content stack (chat + measure)
        self.content_stack = QStackedWidget()

        # Chat area
        self.chat = ChatWidget(self.data_manager)
        self.chat.send_message.connect(self._handle_send)
        self.chat.new_conversation_requested.connect(self._new_conversation)
        self.chat.toggle_sidebar.connect(self._toggle_sidebar)
        self.chat.switch_to_measure.connect(self._switch_to_measure)
        self.content_stack.addWidget(self.chat)

        # Measure page
        self.measure_page = MeasurePage()
        self.measure_page.measure_requested.connect(self._on_measure)
        self.measure_page.switch_to_chat.connect(self._switch_to_chat)
        self.measure_page.toggle_sidebar.connect(self._toggle_sidebar)
        self.measure_page.measure_completed.connect(self._on_measure_completed)
        self.content_stack.addWidget(self.measure_page)

        main_layout.addWidget(self.content_stack, stretch=1)

    def _toggle_sidebar(self):
        self.sidebar_visible = not self.sidebar_visible
        self.sidebar.setVisible(self.sidebar_visible)

    def _show_error(self, message: str):
        """根据当前页面显示红色错误提示"""
        if self._is_measure_page:
            self.measure_page.show_error_bar(message)
        else:
            self.chat.show_error(message)

    def _switch_to_measure(self):
        """切换到测量页面"""
        if self.chat.current_conv:
            self.measure_page.set_conversation(self.chat.current_conv)
            self.content_stack.setCurrentWidget(self.measure_page)
            self._is_measure_page = True

    def _switch_to_chat(self):
        """切换到对话页面"""
        self.content_stack.setCurrentWidget(self.chat)
        self._is_measure_page = False

    def _on_measure(self):
        """点击测量按钮"""
        pass

    def _on_measure_completed(self, hr: float, spo2: float):
        """测量完成，保存数据"""
        if self.chat.current_conv:
            if not self.data_manager.save():
                self._show_error("数据保存失败，请检查磁盘空间")
            self.sidebar.refresh_list()

    def _new_conversation(self):
        # 如果正在流式生成，先保存已生成的内容
        if self._worker and self._worker.isRunning():
            # 停止 worker
            self._worker.terminate()
            self._worker.wait()
            
            # 保存已生成的流式内容到当前会话
            if self._streaming_conv_id and self._streaming_content:
                self.data_manager.add_message(
                    self._streaming_conv_id, 
                    "ai", 
                    self._streaming_content
                )
                self.sidebar.refresh_list()
            
            self._worker = None
        
        # 清理流式状态
        self._streaming_bubble = None
        self._streaming_conv_id = None
        self._streaming_content = ""
        
        conv = self.data_manager.new_conversation()
        self.sidebar.refresh_list()
        self.sidebar.set_active_conversation(conv.id)
        self.chat.set_conversation(conv)

    def _switch_conversation(self, conv_id: str):
        # 如果正在流式生成，先保存已生成的内容
        if self._worker and self._worker.isRunning():
            # 停止 worker
            self._worker.terminate()
            self._worker.wait()
            
            # 保存已生成的流式内容到当前会话
            if self._streaming_conv_id and self._streaming_content:
                self.data_manager.add_message(
                    self._streaming_conv_id, 
                    "ai", 
                    self._streaming_content
                )
                self.sidebar.refresh_list()
            
            self._worker = None
        
        # 清理流式状态
        self._streaming_bubble = None
        self._streaming_conv_id = None
        self._streaming_content = ""
        
        conv = self.data_manager.get_conversation(conv_id)
        if conv:
            self.sidebar.set_active_conversation(conv_id)
            self.chat.set_conversation(conv)
            if self._is_measure_page:
                self.measure_page.set_conversation(conv)

    def _handle_send(self, text: str):
        if not self.chat.current_conv:
            return

        # 如果上一个 worker 还在运行，先停止
        if self._worker and self._worker.isRunning():
            self._worker.terminate()
            self._worker.wait()

        conv = self.chat.current_conv
        if not self.data_manager.add_message(conv.id, "user", text):
            self._show_error("消息保存失败，可能丢失数据")
        self.chat.add_message("user", text)

        # 标题可能由第一条消息更新，同步显示
        if conv.title != self.chat.title_label.text():
            self.chat.title_label.setText(conv.title)

        # 延迟创建 AI 气泡（内部包含等待动画）
        self._pending_text = text
        QTimer.singleShot(50, self._create_streaming_bubble)

        # 构建消息列表并启动 API 调用
        try:
            api_messages = build_messages(conv.messages)
        except Exception as e:
            self.chat.show_error(f"发送失败: {e}")
            self.sidebar.refresh_list()
            return

        self._worker = ChatWorker(
            api_messages,
            siliconflow_key=Config.SILICONFLOW_API_KEY,
            siliconflow_model=Config.CLOUD_MODEL,
            heart_rate=conv.heart_rate,
            blood_oxygen=conv.blood_oxygen
        )
        self._worker.chunk_received.connect(self._on_chunk_received)
        self._worker.finished.connect(self._on_stream_finished)
        self._worker.error_occurred.connect(self._on_stream_error)
        self._worker.start()

        self.sidebar.refresh_list()

    def _create_streaming_bubble(self):
        """延迟创建 AI 流式气泡（让等待动画有时间渲染）"""
        conv = self.chat.current_conv
        if not conv:
            return
        self._streaming_bubble = self.chat.create_streaming_ai_bubble()
        self._streaming_conv_id = conv.id
        self._streaming_content = ""

    def _on_chunk_received(self, chunk: str):
        """收到流式片段，更新 UI"""
        self._streaming_content += chunk
        if self._streaming_bubble:
            # 第一次收到内容时，自动隐藏等待动画并显示文本
            self._streaming_bubble.set_content(self._streaming_content, render_md=False)
            # 自动滚动到底部
            sb = self.chat.scroll_area.verticalScrollBar()
            sb.setValue(sb.maximum())

    def _on_stream_finished(self, full_response: str):
        """流式完成，保存消息"""
        if self._streaming_conv_id and full_response:
            if not self.data_manager.add_message(self._streaming_conv_id, "ai", full_response):
                self._show_error("AI 回复保存失败")
            self.sidebar.refresh_list()

        # 流式完成后用 Markdown 渲染
        if self._streaming_bubble:
            self._streaming_bubble.set_content(full_response, render_md=True)

        self._streaming_bubble = None
        self._streaming_conv_id = None
        self._streaming_content = ""
        self._worker = None

    def _on_stream_error(self, error_msg: str):
        """流式出错，显示错误信息"""
        self._show_error(error_msg)

        if self._streaming_bubble:
            self._streaming_bubble.set_content(f"抱歉，发生了错误：{error_msg}", render_md=False)

        if self._streaming_conv_id:
            self.data_manager.add_message(self._streaming_conv_id, "ai", f"[错误] {error_msg}")
            self.sidebar.refresh_list()

        self._streaming_bubble = None
        self._streaming_conv_id = None
        self._streaming_content = ""
        self._worker = None

    def _on_export_report(self, conv_id: str):
        """处理导出报告请求"""
        conv = self.data_manager.get_conversation(conv_id)
        if not conv:
            QMessageBox.warning(self, "错误", "会话不存在")
            return
        
        # 弹出对话框输入文件名
        default_name = f"{conv.title}_{conv.created_at.replace(':', '-').replace(' ', '_')}"
        file_name, ok = QInputDialog.getText(
            self,
            "导出PDF报告",
            "请输入文件名（不含扩展名）：",
            text=default_name
        )
        
        if not ok or not file_name:
            return
        
        # 确保文件名合法
        file_name = "".join(c for c in file_name if c.isalnum() or c in ('-', '_', '.'))
        file_name = file_name.strip()
        
        if not file_name:
            QMessageBox.warning(self, "错误", "文件名不能为空")
            return
        
        # 生成文件路径（使用配置中的 PDF_OUTPUT_DIR）
        from config.config import Config
        output_dir = Config.PDF_OUTPUT_DIR
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"{file_name}.pdf")
        
        print(f"[DEBUG] PDF输出目录: {output_dir}")
        print(f"[DEBUG] PDF输出路径: {output_path}")
        
        # 如果文件已存在，询问是否覆盖
        if os.path.exists(output_path):
            reply = QMessageBox.question(
                self,
                "文件已存在",
                f"文件 {file_name}.pdf 已存在，是否覆盖？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
        
        # 生成PDF（reportlab很快，不需要进度提示）
        success = self.pdf_generator.generate_report(conv, output_path)
        
        if success:
            QMessageBox.information(
                self, 
                "成功", 
                f"PDF报告已生成：\n{output_path}"
            )
            
            # 自动切换到下一个会话
            self._switch_to_next_conversation(conv_id)
        else:
            QMessageBox.critical(
                self, 
                "失败", 
                "PDF报告生成失败，请查看控制台输出"
            )

    def _switch_to_next_conversation(self, current_conv_id: str):
        """切换到下一个会话"""
        conversations = self.data_manager.get_all_conversations()
        if not conversations:
            return
        
        # 找到当前会话的索引
        current_index = -1
        for i, conv in enumerate(conversations):
            if conv.id == current_conv_id:
                current_index = i
                break
        
        if current_index == -1:
            return
        
        # 切换到下一个会话（如果是最后一个，则切换到第一个）
        next_index = (current_index + 1) % len(conversations)
        next_conv = conversations[next_index]
        
        if next_conv.id != current_conv_id:
            self._switch_conversation(next_conv.id)
