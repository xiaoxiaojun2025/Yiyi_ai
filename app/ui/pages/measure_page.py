from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSizePolicy, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from datetime import datetime

from ...core.data_manager import Conversation
from ...hardware.sensor_worker import SensorWorker
from ..widgets.heart_icon import HeartIcon


class MeasurePage(QWidget):
    """测量页面"""
    measure_requested = pyqtSignal()
    switch_to_chat = pyqtSignal()
    toggle_sidebar = pyqtSignal()
    measure_completed = pyqtSignal(float, float)  # 心率, 血氧

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_conv: Conversation | None = None
        self._worker: SensorWorker | None = None
        self._is_measuring = False

        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Header
        header = QWidget()
        header.setObjectName("chat_header")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(8, 8, 16, 8)
        header_layout.setSpacing(8)

        # 侧边栏按钮
        self.menu_btn = QPushButton("\u2630")
        self.menu_btn.setObjectName("menu_btn")
        self.menu_btn.setFixedSize(36, 36)
        self.menu_btn.setToolTip("展开/收起侧边栏")
        self.menu_btn.clicked.connect(self.toggle_sidebar.emit)
        header_layout.addWidget(self.menu_btn)

        self.title_label = QLabel("健康测量")
        self.title_label.setObjectName("chat_title")
        header_layout.addWidget(self.title_label)

        header_layout.addStretch()

        # 切换到对话页面按钮
        self.chat_btn = QPushButton("💬 对话")
        self.chat_btn.setObjectName("switch_measure_btn")
        self.chat_btn.setFixedHeight(36)
        self.chat_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.chat_btn.clicked.connect(self.switch_to_chat.emit)
        header_layout.addWidget(self.chat_btn)

        main_layout.addWidget(header)

        # Content area
        content = QWidget()
        content.setObjectName("measure_content")
        content_layout = QVBoxLayout(content)
        content_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content_layout.setSpacing(40)

        # 心形图标
        self.heart_icon = HeartIcon(100)
        content_layout.addWidget(self.heart_icon, alignment=Qt.AlignmentFlag.AlignCenter)

        # 数据卡片容器
        data_container = QWidget()
        data_container.setMaximumWidth(500)
        data_layout = QHBoxLayout(data_container)
        data_layout.setSpacing(30)
        data_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # 心率卡片
        hr_card = self._create_data_card("heart_rate", "心率", "BPM")
        data_layout.addWidget(hr_card)

        # 血氧卡片
        spo2_card = self._create_data_card("blood_oxygen", "血氧", "%")
        data_layout.addWidget(spo2_card)

        content_layout.addWidget(data_container, alignment=Qt.AlignmentFlag.AlignCenter)

        # 状态标签
        self.status_label = QLabel("尚未测量")
        self.status_label.setObjectName("measure_status")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content_layout.addWidget(self.status_label)

        # 测量时间
        self.time_label = QLabel("")
        self.time_label.setObjectName("measure_time")
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content_layout.addWidget(self.time_label)

        # 测量按钮
        self.measure_btn = QPushButton("开始测量")
        self.measure_btn.setObjectName("measure_btn")
        self.measure_btn.setFixedSize(200, 60)
        self.measure_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.measure_btn.clicked.connect(self._on_measure_click)
        content_layout.addWidget(self.measure_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        content_layout.addStretch()

        main_layout.addWidget(content, stretch=1)

        # Error bar (hidden by default)
        self.error_bar = QLabel()
        self.error_bar.setObjectName("error_bar")
        self.error_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.error_bar.setWordWrap(True)
        self.error_bar.setMaximumHeight(60)
        self.error_bar.hide()
        main_layout.addWidget(self.error_bar)

    def _create_data_card(self, attr_name: str, title: str, unit: str) -> QFrame:
        """创建数据卡片"""
        card = QFrame()
        card.setObjectName("measure_card")
        card.setFixedSize(200, 160)

        card_layout = QVBoxLayout(card)
        card_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.setSpacing(8)

        # 标题
        title_label = QLabel(title)
        title_label.setObjectName("measure_card_title")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(title_label)

        # 数值
        value_label = QLabel("--")
        value_label.setObjectName("measure_card_value")
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(value_label)
        setattr(self, f"{attr_name}_label", value_label)

        # 单位
        unit_label = QLabel(unit)
        unit_label.setObjectName("measure_card_unit")
        unit_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(unit_label)

        return card

    def set_conversation(self, conv: Conversation):
        """设置当前会话并显示数据"""
        self.current_conv = conv
        self._update_display()

    def _update_display(self):
        """更新显示数据"""
        if self.current_conv:
            hr = self.current_conv.heart_rate
            spo2 = self.current_conv.blood_oxygen
            time_str = self.current_conv.last_measured_at

            self.heart_rate_label.setText(f"{hr:.0f}" if hr else "--")
            self.blood_oxygen_label.setText(f"{spo2:.0f}" if spo2 else "--")
            self.time_label.setText(f"上次测量: {time_str}" if time_str else "")
        else:
            self.heart_rate_label.setText("--")
            self.blood_oxygen_label.setText("--")
            self.time_label.setText("")

    def _on_measure_click(self):
        """点击测量/中止按钮"""
        if self._is_measuring:
            self._stop_measure()
        else:
            self._start_measure()

    def _start_measure(self):
        """开始测量"""
        self._is_measuring = True
        self.measure_btn.setText("中止测量")
        self.measure_btn.setObjectName("measure_btn_stop")
        self.measure_btn.style().polish(self.measure_btn)

        self.status_label.setText("正在初始化传感器...")
        self.heart_rate_label.setText("--")
        self.blood_oxygen_label.setText("--")
        self.heart_icon.set_pulse(False)

        # 启动传感器线程
        try:
            self._worker = SensorWorker()
            self._worker.finger_detected.connect(self._on_finger_detected)
            self._worker.finger_lost.connect(self._on_finger_lost)
            self._worker.data_updated.connect(self._on_data_updated)
            self._worker.measure_finished.connect(self._on_measure_finished)
            self._worker.measure_error.connect(self._on_measure_error)
            self._worker.measure_timeout.connect(self._on_measure_timeout)
            self._worker.start()
        except Exception as e:
            self._is_measuring = False
            self.measure_btn.setText("开始测量")
            self.measure_btn.setObjectName("measure_btn")
            self.measure_btn.style().polish(self.measure_btn)
            self.status_label.setText("传感器初始化失败")
            self.show_error_bar(f"传感器初始化失败: {e}")

    def _stop_measure(self):
        """中止测量"""
        if self._worker:
            self._worker.stop()
            self._worker = None

        self._is_measuring = False
        self.measure_btn.setText("开始测量")
        self.measure_btn.setObjectName("measure_btn")
        self.measure_btn.style().polish(self.measure_btn)
        self.heart_icon.set_pulse(False)
        self.status_label.setText("测量已中止")

    def _on_finger_detected(self):
        """检测到手指"""
        self.status_label.setText("检测到手指，正在测量...")
        self.heart_icon.set_pulse(True)

    def _on_finger_lost(self):
        """手指丢失"""
        self.status_label.setText("未检测到手指，请将手指放在传感器上")
        self.heart_icon.set_pulse(False)

    def _on_data_updated(self, hr: float, spo2: float):
        """数据更新"""
        self.heart_rate_label.setText(f"{hr:.0f}")
        if spo2 > 0:
            self.blood_oxygen_label.setText(f"{spo2:.1f}")
        self.status_label.setText("测量中...")

    def _on_measure_finished(self, hr: float, spo2: float):
        """测量完成"""
        self._is_measuring = False
        self.measure_btn.setText("开始测量")
        self.measure_btn.setObjectName("measure_btn")
        self.measure_btn.style().polish(self.measure_btn)
        self.heart_icon.set_pulse(False)

        # 显示最终数据
        self.heart_rate_label.setText(f"{hr:.0f}")
        self.blood_oxygen_label.setText(f"{spo2:.1f}")
        self.time_label.setText(f"测量时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        self.status_label.setText("测量完成")

        # 保存到会话
        if self.current_conv:
            self.current_conv.heart_rate = hr
            self.current_conv.blood_oxygen = spo2
            self.current_conv.last_measured_at = datetime.now().strftime('%Y-%m-%d %H:%M')
            self.measure_completed.emit(hr, spo2)

        self._worker = None

    def _on_measure_error(self, error_msg: str):
        """测量错误"""
        self._is_measuring = False
        self.measure_btn.setText("开始测量")
        self.measure_btn.setObjectName("measure_btn")
        self.measure_btn.style().polish(self.measure_btn)
        self.heart_icon.set_pulse(False)
        self.status_label.setText("测量失败")

        self.show_error_bar(f"传感器错误: {error_msg}")
        self._worker = None

    def _on_measure_timeout(self):
        """测量超时"""
        self._is_measuring = False
        self.measure_btn.setText("开始测量")
        self.measure_btn.setObjectName("measure_btn")
        self.measure_btn.style().polish(self.measure_btn)
        self.heart_icon.set_pulse(False)
        self.status_label.setText("测量超时，请重试")

        self.show_error_bar("测量超时，请确保手指放在传感器上")
        self._worker = None

    def show_error_bar(self, message: str, duration: int = 5000):
        """显示红色错误提示条，duration 毫秒后自动隐藏"""
        self.error_bar.setText(f"\u26a0 {message}")
        self.error_bar.show()
        QTimer.singleShot(duration, self.error_bar.hide)
