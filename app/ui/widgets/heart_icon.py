from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPainter, QColor, QPen, QPainterPath
from datetime import datetime


class HeartIcon(QWidget):
    """自定义心形图标"""
    def __init__(self, size: int = 180, parent=None):
        super().__init__(parent)
        self._size = size
        self.setFixedSize(size, size)
        self._pulse = False
        self._pulse_timer = QTimer(self)
        self._pulse_timer.timeout.connect(self._toggle_pulse)
        self._pulse_timer.setInterval(500)

    def set_pulse(self, enable: bool):
        self._pulse = enable
        if enable:
            self._pulse_timer.start()
        else:
            self._pulse_timer.stop()
            self.update()

    def _toggle_pulse(self):
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 根据脉动状态调整大小
        scale = 1.0
        if self._pulse:
            import math
            scale = 1.0 + 0.08 * abs(math.sin(datetime.now().timestamp() * 3))

        size = int(self._size * scale)
        offset = (self._size - size) // 2

        # 绘制心形
        painter.setBrush(QColor("#e74c3c"))
        painter.setPen(Qt.PenStyle.NoPen)

        # 减小边距，让心形更饱满
        margin = size // 10

        path = QPainterPath()
        path.moveTo(size / 2 + offset, size - margin + offset)

        # 左半心（调整控制点，让心形更宽更饱满）
        path.cubicTo(
            offset + margin * 0.5, size * 0.65 + offset,  # 左侧控制点更靠左
            offset + margin * 0.5, offset + margin * 0.5,  # 顶部控制点更高
            size / 2 + offset, offset + margin + size // 6  # 中间凹陷更深
        )

        # 右半心（对称调整）
        path.cubicTo(
            size - margin * 0.5 + offset, offset + margin * 0.5,  # 顶部控制点更高
            size - margin * 0.5 + offset, size * 0.65 + offset,  # 右侧控制点更靠右
            size / 2 + offset, size - margin + offset
        )

        painter.drawPath(path)
        painter.end()
