"""
App package initialization
导出主要模块供外部使用
"""
from .main_window import MainWindow
from .ui.styles import MAIN_STYLE

__all__ = ['MainWindow', 'MAIN_STYLE']