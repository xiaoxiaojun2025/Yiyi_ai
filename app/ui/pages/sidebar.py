from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QFrame, QInputDialog
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QFont

from ...core.data_manager import DataManager


class ConversationItemWidget(QWidget):
    export_requested = pyqtSignal(str)  # 导出请求信号
    
    def __init__(self, conv_id: str, title: str, time_str: str, is_active: bool = False, parent=None):
        super().__init__(parent)
        self.conv_id = conv_id
        self.is_active = is_active

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 8, 8)
        layout.setSpacing(8)
        
        # 左侧：文本信息
        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        
        self.title_label = QLabel(title)
        self.title_label.setObjectName("conversation_title")
        font = QFont()
        font.setPointSize(10)
        font.setBold(True)
        self.title_label.setFont(font)
        self.title_label.setWordWrap(True)
        
        self.time_label = QLabel(time_str)
        self.time_label.setObjectName("conversation_time")
        
        text_layout.addWidget(self.title_label)
        text_layout.addWidget(self.time_label)
        
        layout.addLayout(text_layout, stretch=1)
        
        # 右侧：导出按钮
        self.export_btn = QPushButton("⬇️")
        self.export_btn.setObjectName("export_btn")
        self.export_btn.setFixedSize(28, 28)
        self.export_btn.setToolTip("导出PDF报告")
        self.export_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.export_btn.clicked.connect(self._on_export_clicked)
        layout.addWidget(self.export_btn)

        self._update_style(is_active)
    
    def _on_export_clicked(self):
        """点击导出按钮"""
        self.export_requested.emit(self.conv_id)

    def _update_style(self, active: bool):
        if active:
            self.setStyleSheet("""
                #conversation_title { color: #4a90d9; }
                #conversation_time { color: #4a90d9; }
            """)
        else:
            self.setStyleSheet("")

    def set_active(self, active: bool):
        self.is_active = active
        self._update_style(active)


class SidebarWidget(QWidget):
    conversation_selected = pyqtSignal(str)
    new_conversation_requested = pyqtSignal()
    export_report_requested = pyqtSignal(str)  # 导出报告信号

    def __init__(self, data_manager: DataManager, parent=None):
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.setFixedWidth(280)
        self.data_manager = data_manager
        self.current_conv_id = None
        self.item_widgets: dict[str, ConversationItemWidget] = {}
        self._blocking_signals = False

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Header
        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(12, 8, 12, 8)

        self.title_label = QLabel("历史对话")
        self.title_label.setObjectName("sidebar_title")

        header_layout.addWidget(self.title_label)
        header_layout.addStretch()

        main_layout.addWidget(header)

        # New chat button
        btn_container = QWidget()
        btn_layout = QHBoxLayout(btn_container)
        btn_layout.setContentsMargins(8, 4, 8, 8)

        self.new_chat_btn = QPushButton("+ 新对话")
        self.new_chat_btn.setObjectName("new_chat_btn")
        self.new_chat_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.new_chat_btn.clicked.connect(self.new_conversation_requested.emit)

        btn_layout.addWidget(self.new_chat_btn)
        main_layout.addWidget(btn_container)

        # Separator
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("color: #e0e0e0;")
        main_layout.addWidget(line)

        # Conversation list
        self.list_widget = QListWidget()
        self.list_widget.setObjectName("conversation_list")
        self.list_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.list_widget.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.list_widget.setSpacing(4)
        self.list_widget.setContentsMargins(0, 4, 0, 4)
        self.list_widget.currentRowChanged.connect(self._on_item_clicked)

        main_layout.addWidget(self.list_widget)

        self.refresh_list()

    def refresh_list(self):
        self._blocking_signals = True
        self.list_widget.blockSignals(True)
        self.list_widget.clear()
        self.item_widgets.clear()

        conversations = self.data_manager.get_all_conversations()
        for conv in conversations:
            item_widget = ConversationItemWidget(
                conv_id=conv.id,
                title=conv.title,
                time_str=conv.updated_at,
                is_active=(conv.id == self.current_conv_id),
            )
            # 连接导出信号
            item_widget.export_requested.connect(self._on_export_requested)
            self.item_widgets[conv.id] = item_widget

            list_item = QListWidgetItem()
            list_item.setSizeHint(QSize(0, 60))
            list_item.setData(Qt.ItemDataRole.UserRole, conv.id)
            self.list_widget.addItem(list_item)
            self.list_widget.setItemWidget(list_item, item_widget)

        self.list_widget.blockSignals(False)
        self._blocking_signals = False
    
    def _on_export_requested(self, conv_id: str):
        """处理导出请求"""
        self.export_report_requested.emit(conv_id)

    def _on_item_clicked(self, row: int):
        if self._blocking_signals:
            return
        if row < 0:
            return
        item = self.list_widget.item(row)
        if item:
            conv_id = item.data(Qt.ItemDataRole.UserRole)
            if conv_id:
                self.set_active_conversation(conv_id)
                self.conversation_selected.emit(conv_id)

    def set_active_conversation(self, conv_id: str):
        old_id = self.current_conv_id
        self.current_conv_id = conv_id

        if old_id and old_id in self.item_widgets:
            self.item_widgets[old_id].set_active(False)
        if conv_id in self.item_widgets:
            self.item_widgets[conv_id].set_active(True)
