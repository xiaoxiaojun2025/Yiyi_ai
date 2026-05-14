from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QScrollArea, QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont

from ...core.data_manager import DataManager, Conversation
from ..widgets.typing_indicator import TypingIndicator
from ..widgets.doctor_avatar import DoctorAvatar


class WelcomeWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("welcome_container")

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(16)

        avatar = DoctorAvatar(140)
        layout.addWidget(avatar, alignment=Qt.AlignmentFlag.AlignCenter)

        title = QLabel("AI 智能问诊助手")
        title.setObjectName("welcome_title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        subtitle = QLabel("您好！我是AI医生，请描述您的症状，我将为您提供专业的健康建议。\n注意：AI建议仅供参考，具体诊断请咨询专业医生。")
        subtitle.setObjectName("welcome_subtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)


class MessageBubble(QWidget):
    def __init__(self, role: str, content: str, parent=None):
        super().__init__(parent)
        self.role = role
        self._typing_indicator: TypingIndicator | None = None
        self._bubble_container: QWidget | None = None
        self._bubble_layout: QVBoxLayout | None = None
        self._bubble: QTextEdit | QLabel | None = None

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(16, 4, 16, 4)

        if role == "user":
            self._bubble = QLabel(content)
            self._bubble.setObjectName("user_message")
            self._bubble.setWordWrap(True)
            self._bubble.setTextInteractionFlags(
                Qt.TextInteractionFlag.TextSelectableByMouse
            )
            self._bubble.setCursor(Qt.CursorShape.IBeamCursor)
            self._bubble.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)
            main_layout.addStretch()
            main_layout.addWidget(self._bubble)
        else:
            # AI消息容器
            self._bubble_container = QWidget()
            self._bubble_container.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)
            self._bubble_layout = QVBoxLayout(self._bubble_container)
            self._bubble_layout.setContentsMargins(0, 0, 0, 0)
            self._bubble_layout.setSpacing(4)
            
            ai_label = QLabel("⚕ AI 医生")
            ai_label.setObjectName("ai_label")
            self._bubble_layout.addWidget(ai_label)
            
            # 如果有内容，直接显示；否则显示等待动画
            if content:
                self._bubble = QTextEdit()
                self._bubble.setObjectName("ai_message_md")
                self._bubble.setReadOnly(True)
                self._bubble.setFrameShape(QFrame.Shape.NoFrame)
                self._bubble.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
                self._bubble.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
                self._bubble.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Preferred)
                self._bubble.setMinimumWidth(0)  # 允许收缩
                # 设置文档边距，防止内容被裁剪
                doc = self._bubble.document()
                doc.setDocumentMargin(4)
                self._bubble.setMarkdown(content)
                self._bubble_layout.addWidget(self._bubble)
                QTimer.singleShot(10, self._update_size)
            else:
                # 流式消息初始显示等待动画
                self._typing_indicator = TypingIndicator()
                self._typing_indicator.setFixedWidth(200)
                self._bubble_layout.addWidget(self._typing_indicator)
            
            main_layout.addLayout(self._create_ai_column())
            main_layout.addStretch()

    def closeEvent(self, event):
        """清理资源，防止闪退"""
        if self._typing_indicator:
            self._typing_indicator.stop()
        super().closeEvent(event)

    def _create_ai_column(self):
        """创建AI消息列布局"""
        ai_col = QVBoxLayout()
        ai_col.setSpacing(4)
        ai_col.addWidget(self._bubble_container)
        return ai_col

    def set_content(self, text: str, render_md: bool = False):
        if self.role == "ai":
            # 移除等待动画
            if self._typing_indicator:
                self._typing_indicator.stop()
                self._typing_indicator.setParent(None)
                self._typing_indicator.deleteLater()
                self._typing_indicator = None
            
            # 创建或更新文本显示
            if not hasattr(self, '_bubble') or self._bubble is None:
                self._bubble = QTextEdit()
                self._bubble.setObjectName("ai_message_md")
                self._bubble.setReadOnly(True)
                self._bubble.setFrameShape(QFrame.Shape.NoFrame)
                self._bubble.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
                self._bubble.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
                self._bubble.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Preferred)
                self._bubble.setMinimumWidth(0)  # 允许收缩
                # 设置文档边距，防止内容被裁剪
                doc_margin = self._bubble.document()
                doc_margin.setDocumentMargin(4)
                if self._bubble_layout:
                    self._bubble_layout.addWidget(self._bubble)
            
            # 安全地设置内容
            if hasattr(self, '_bubble') and self._bubble:
                try:
                    if render_md:
                        self._bubble.setMarkdown(text)
                    else:
                        self._bubble.setText(text)
                    # 延迟更新尺寸，确保内容已渲染
                    QTimer.singleShot(10, self._update_size)
                    # 移除自动滚动，避免卡顿
                    # QTimer.singleShot(20, self._scroll_to_bottom)
                except RuntimeError:
                    # 对象已被删除，忽略
                    pass
        else:
            if hasattr(self, '_bubble') and self._bubble:
                try:
                    self._bubble.setText(text)
                except RuntimeError:
                    pass
    
    def _scroll_to_bottom(self):
        """滚动到消息底部"""
        if hasattr(self, '_bubble') and self._bubble:
            try:
                from PyQt6.QtWidgets import QTextEdit
                if isinstance(self._bubble, QTextEdit):
                    # 将光标移动到最后并滚动
                    cursor = self._bubble.textCursor()
                    cursor.movePosition(cursor.MoveOperation.End)
                    self._bubble.setTextCursor(cursor)
                    self._bubble.ensureCursorVisible()
            except RuntimeError:
                pass

    def _update_size(self):
        """更新气泡的尺寸（宽度和高度）"""
        if hasattr(self, '_bubble') and self._bubble and self.parent():
            try:
                # 确保是QTextEdit（只有它才有document方法）
                from PyQt6.QtWidgets import QTextEdit
                if not isinstance(self._bubble, QTextEdit):
                    return
                
                # 获取父容器宽度，计算最大宽度
                pw = self.parent().width()
                max_w = int(pw * 0.75)
                
                # 先设置一个较大的临时宽度来计算内容
                self._bubble.setMaximumWidth(max_w)
                self._bubble.setMinimumWidth(0)
                
                # 计算文档实际需要的宽度
                doc = self._bubble.document()
                doc.setTextWidth(max_w - 30)  # 留出边距
                
                # 获取实际内容宽度（idealWidth返回的是最优宽度）
                content_width = int(doc.idealWidth()) + 30
                
                # 限制在合理范围内
                actual_width = max(200, min(content_width, max_w))
                
                # 设置宽度
                self._bubble.setMinimumWidth(actual_width)
                self._bubble.setMaximumWidth(actual_width)
                
                # 更新高度（增加充足余量确保最后一行完全可见）
                h = int(doc.size().height()) + 20
                self._bubble.setMinimumHeight(h)
                self._bubble.setMaximumHeight(h)
                
                # 更新容器尺寸（只设置宽度，高度由布局自动管理）
                if self._bubble_container:
                    self._bubble_container.setFixedWidth(actual_width)
                    # 不要设置固定高度，让布局自动管理
                
                # 触发布局更新
                self.updateGeometry()
                self.update()
            except RuntimeError:
                pass

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.parent() and hasattr(self, '_bubble') and self._bubble:
            try:
                # 窗口大小改变时重新计算尺寸
                QTimer.singleShot(10, self._update_size)
            except RuntimeError:
                pass


class ChatWidget(QWidget):
    send_message = pyqtSignal(str)
    new_conversation_requested = pyqtSignal()
    toggle_sidebar = pyqtSignal()
    switch_to_measure = pyqtSignal()

    def __init__(self, data_manager: DataManager, parent=None):
        super().__init__(parent)
        self.data_manager = data_manager
        self.current_conv: Conversation | None = None
        self._welcome_widget: WelcomeWidget | None = None
        self._loading_label: QLabel | None = None
        self._typing_indicator: TypingIndicator | None = None

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Header
        self.header = QWidget()
        self.header.setObjectName("chat_header")
        header_layout = QHBoxLayout(self.header)
        header_layout.setContentsMargins(8, 8, 16, 8)
        header_layout.setSpacing(8)

        self.menu_btn = QPushButton("\u2630")
        self.menu_btn.setObjectName("menu_btn")
        self.menu_btn.setFixedSize(36, 36)
        self.menu_btn.setToolTip("展开/收起侧边栏")
        self.menu_btn.clicked.connect(self.toggle_sidebar.emit)
        header_layout.addWidget(self.menu_btn)

        self.title_label = QLabel("新对话")
        self.title_label.setObjectName("chat_title")
        header_layout.addWidget(self.title_label)

        header_layout.addStretch()

        # 切换到测量页面按钮
        self.measure_btn = QPushButton("\u2665 测量")
        self.measure_btn.setObjectName("switch_measure_btn")
        self.measure_btn.setFixedHeight(36)
        self.measure_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.measure_btn.clicked.connect(self.switch_to_measure.emit)
        header_layout.addWidget(self.measure_btn)

        main_layout.addWidget(self.header)

        # Message scroll area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setObjectName("message_area")

        self.message_container = QWidget()
        self.message_layout = QVBoxLayout(self.message_container)
        self.message_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        self.message_layout.setSpacing(8)
        self.message_layout.setContentsMargins(0, 16, 0, 16)

        self.scroll_area.setWidget(self.message_container)
        main_layout.addWidget(self.scroll_area, stretch=1)

        # Error bar (hidden by default)
        self.error_bar = QLabel()
        self.error_bar.setObjectName("error_bar")
        self.error_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.error_bar.setWordWrap(True)
        self.error_bar.setMaximumHeight(60)
        self.error_bar.hide()
        main_layout.addWidget(self.error_bar)

        # Input area
        input_container = QWidget()
        input_container.setObjectName("input_area")
        input_layout = QHBoxLayout(input_container)
        input_layout.setContentsMargins(16, 8, 16, 8)
        input_layout.setSpacing(8)

        self.input_field = QTextEdit()
        self.input_field.setObjectName("input_field")
        self.input_field.setPlaceholderText("请描述您的症状...")
        self.input_field.setMaximumHeight(80)
        self.input_field.setMinimumHeight(44)
        self.input_field.setAcceptRichText(False)
        # 确保支持输入法切换
        self.input_field.setInputMethodHints(Qt.InputMethodHint.ImhNone)
        input_layout.addWidget(self.input_field, stretch=1)

        self.send_btn = QPushButton("发送")
        self.send_btn.setObjectName("send_btn")
        self.send_btn.setFixedSize(80, 44)
        self.send_btn.clicked.connect(self._on_send)
        input_layout.addWidget(self.send_btn)

        main_layout.addWidget(input_container)

        self.input_field.installEventFilter(self)

        self._show_welcome()

    def eventFilter(self, obj, event):
        if obj == self.input_field and event.type() == event.Type.KeyPress:
            if event.key() == Qt.Key.Key_Return and not event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                self._on_send()
                return True
        return super().eventFilter(obj, event)

    def _on_send(self):
        text = self.input_field.toPlainText().strip()
        if not text or not self.current_conv:
            return
        self.input_field.clear()
        self.send_message.emit(text)

    def set_conversation(self, conv: Conversation):
        self.current_conv = conv
        self.title_label.setText(conv.title)
        self._refresh_messages()

    def _clear_message_area(self):
        while self.message_layout.count():
            item = self.message_layout.takeAt(0)
            w = item.widget()
            if w:
                w.setParent(None)
                w.deleteLater()
            sub = item.layout()
            if sub:
                self._clear_sub_layout(sub)

    def _clear_sub_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            w = item.widget()
            if w:
                w.setParent(None)
                w.deleteLater()
            sub = item.layout()
            if sub:
                self._clear_sub_layout(sub)

    def _refresh_messages(self):
        self._clear_message_area()
        self._welcome_widget = None

        if not self.current_conv or not self.current_conv.messages:
            self._show_welcome()
        else:
            for msg in self.current_conv.messages:
                bubble = MessageBubble(msg["role"], msg["content"])
                self.message_layout.addWidget(bubble)
            self.message_layout.addStretch()
            QTimer.singleShot(50, self._scroll_to_bottom)

    def _show_welcome(self):
        self._clear_message_area()
        self._welcome_widget = WelcomeWidget()
        self.message_layout.addWidget(self._welcome_widget)

    def add_message(self, role: str, content: str):
        if self._welcome_widget:
            self._clear_message_area()
            self._welcome_widget = None

        bubble = MessageBubble(role, content)
        self.message_layout.addWidget(bubble)
        self.message_layout.addStretch()
        QTimer.singleShot(50, self._scroll_to_bottom)

    def create_streaming_ai_bubble(self) -> MessageBubble:
        """创建一个空的 AI 消息气泡，用于流式填充内容（内部已包含等待动画）"""
        if self._welcome_widget:
            self._clear_message_area()
            self._welcome_widget = None

        bubble = MessageBubble("ai", "")
        self.message_layout.addWidget(bubble)
        self.message_layout.addStretch()
        QTimer.singleShot(50, self._scroll_to_bottom)
        return bubble

    def finalize_streaming_bubble(self, bubble: MessageBubble, content: str):
        """流式结束后，更新气泡内容并保存到数据"""
        if bubble and bubble._bubble:
            if bubble.role == "ai":
                bubble._bubble.setMarkdown(content)
            else:
                bubble._bubble.setText(content)
            QTimer.singleShot(50, self._scroll_to_bottom)

    def _scroll_to_bottom(self):
        sb = self.scroll_area.verticalScrollBar()
        sb.setValue(sb.maximum())

    def show_typing(self):
        """显示等待动画"""
        if self._welcome_widget:
            self._clear_message_area()
            self._welcome_widget = None

        if self._typing_indicator is None:
            self._typing_indicator = TypingIndicator()
            self.message_layout.addWidget(self._typing_indicator)
            self.message_layout.addStretch()
            self._scroll_to_bottom()

    def hide_typing(self):
        """隐藏等待动画"""
        if self._typing_indicator:
            self._typing_indicator.stop()
            self._typing_indicator.setParent(None)
            self._typing_indicator.deleteLater()
            self._typing_indicator = None

    def show_error(self, message: str, duration: int = 5000):
        """显示错误提示条，duration 毫秒后自动隐藏"""
        self.error_bar.setText(f"\u26a0 {message}")
        self.error_bar.show()
        QTimer.singleShot(duration, self.error_bar.hide)

    def show_loading(self) -> QLabel:
        self._loading_label = QLabel("\u23f3 AI 正在思考...")
        self._loading_label.setObjectName("ai_label")
        self._loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._loading_label.setStyleSheet("padding: 16px; font-size: 14px; color: #999;")
        self.message_layout.addWidget(self._loading_label)
        self.message_layout.addStretch()
        self._scroll_to_bottom()
        return self._loading_label

    def remove_loading(self, loading_widget):
        if loading_widget and loading_widget.parent():
            loading_widget.setParent(None)
            loading_widget.deleteLater()
        self._loading_label = None
