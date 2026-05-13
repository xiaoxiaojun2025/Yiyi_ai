from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QColor, QPen


class DoctorAvatar(QWidget):
    """医生头像图标"""
    def __init__(self, size: int = 120, parent=None):
        super().__init__(parent)
        self._size = size
        self.setFixedSize(size, size)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        painter.setBrush(QColor("#4a90d9"))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(2, 2, self._size - 4, self._size - 4)

        painter.setPen(QPen(QColor("white"), 4))
        center = self._size // 2
        cross_size = self._size // 4
        painter.drawLine(center - cross_size, center, center + cross_size, center)
        painter.drawLine(center, center - cross_size, center, center + cross_size)

        painter.end()
