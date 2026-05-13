from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPainter, QColor


class TypingIndicator(QWidget):
    """三个点跳动的等待动画"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("typing_indicator")
        self.setFixedHeight(40)
        self._dot_offset = [0.0, 0.0, 0.0]
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._animate)
        self._timer.start(80)
        self._step = 0

    def _animate(self):
        self._step += 1
        for i in range(3):
            phase = self._step - i * 3
            self._dot_offset[i] = max(0, abs((phase % 12) - 6) - 3) / 3.0
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        painter.setBrush(QColor("#cccccc"))
        painter.setPen(Qt.PenStyle.NoPen)

        center_x = self.width() // 2
        base_y = self.height() // 2
        dot_r = 5
        spacing = 18

        for i in range(3):
            x = center_x + (i - 1) * spacing
            y = base_y - self._dot_offset[i] * 8
            painter.drawEllipse(int(x - dot_r), int(y - dot_r), dot_r * 2, dot_r * 2)

        painter.end()

    def stop(self):
        self._timer.stop()
