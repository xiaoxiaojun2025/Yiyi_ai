"""
Core package initialization
导出核心业务逻辑模块
"""
from .data_manager import DataManager, Conversation
from .api_client import ChatWorker, build_messages
from .pdf_generator import PDFReportGenerator

__all__ = [
    'DataManager',
    'Conversation',
    'ChatWorker',
    'build_messages',
    'PDFReportGenerator'
]