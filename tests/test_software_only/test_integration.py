"""
集成测试
测试完整流程：用户输入 → AI回复 → 数据存储 → PDF导出
"""
import pytest
from pathlib import Path
from app.core.data_manager import DataManager, Conversation
from app.core.pdf_generator import PDFReportGenerator


class TestIntegration:
    """集成测试类"""

    def test_full_conversation_flow(self, tmp_path):
        """测试完整对话流程"""
        # 1. 创建数据管理器
        data_dir = tmp_path / "test_data"
        dm = DataManager(str(data_dir))
        
        # 2. 创建会话
        conv = dm.new_conversation()
        conv.title = "集成测试"
        
        # 3. 添加用户消息
        dm.add_message(conv.id, "user", "我最近有点胸闷，心率72，血氧98")
        
        # 4. 添加AI回复（模拟）
        ai_response = """心率72次/分在正常范围，血氧98%也是正常的。

胸闷可能的原因：
• 焦虑或压力
• 胃食管反流
• 肋间神经问题

建议记录胸闷发作时间，如果持续不缓解请就医。"""
        
        dm.add_message(conv.id, "assistant", ai_response)
        
        # 5. 更新健康数据
        conv = dm.get_conversation(conv.id)
        conv.heart_rate = 72.0
        conv.blood_oxygen = 98.0
        dm.save()
        
        # 6. 验证数据保存
        dm2 = DataManager(str(data_dir))
        conv2 = dm2.get_conversation(conv.id)
        
        assert len(conv2.messages) == 2
        assert conv2.heart_rate == 72.0
        assert conv2.blood_oxygen == 98.0

    def test_pdf_export_after_conversation(self, tmp_path):
        """测试对话后导出PDF"""
        # 1. 创建会话和数据
        data_dir = tmp_path / "test_data"
        dm = DataManager(str(data_dir))
        
        conv = dm.new_conversation()
        conv.title = "PDF导出测试"
        dm.add_message(conv.id, "user", "头痛怎么办")
        dm.add_message(conv.id, "assistant", "建议休息，多喝水，如持续请就医")
        
        conv = dm.get_conversation(conv.id)
        conv.heart_rate = 68.0
        conv.blood_oxygen = 97.5
        
        # 2. 导出PDF
        output_dir = tmp_path / "pdf_output"
        output_dir.mkdir()
        output_path = str(output_dir / "test_report.pdf")
        
        generator = PDFReportGenerator()
        success = generator.generate_report(conv, output_path)
        
        # 3. 验证PDF生成
        assert success is True
        assert Path(output_path).exists()
        assert Path(output_path).stat().st_size > 0

    def test_multiple_conversations_management(self, tmp_path):
        """测试多会话管理"""
        data_dir = tmp_path / "test_data"
        dm = DataManager(str(data_dir))
        
        # 创建多个会话
        conv_ids = []
        for i in range(5):
            conv = dm.new_conversation()
            conv.title = f"会话{i}"
            dm.add_message(conv.id, "user", f"问题{i}")
            dm.add_message(conv.id, "assistant", f"回答{i}")
            conv_ids.append(conv.id)
        
        # 验证所有会话都存在
        assert len(dm.conversations) == 5
        
        # 删除其中一个
        dm.delete_conversation(conv_ids[2])
        assert len(dm.conversations) == 4
        
        # 保存并重新加载
        dm.save()
        
        dm2 = DataManager(str(data_dir))
        assert len(dm2.conversations) == 4

    def test_api_fallback_simulation(self, tmp_path):
        """模拟API降级流程"""
        from unittest.mock import Mock, patch, MagicMock
        import sys
        
        # 创建更完整的PyQt6 mock
        class MockQThread:
            def __init__(self, parent=None):
                self.parent = parent
        
        class MockPyQtSignal:
            def __init__(self):
                self.connections = []
            
            def connect(self, slot):
                self.connections.append(slot)
            
            def emit(self, *args):
                for conn in self.connections:
                    conn(*args)
        
        mock_qtcore = MagicMock()
        mock_qtcore.QThread = MockQThread
        mock_qtcore.pyqtSignal = MockPyQtSignal
        
        sys.modules['PyQt6'] = MagicMock()
        sys.modules['PyQt6.QtCore'] = mock_qtcore
        
        from app.core.api_client import ChatWorker
        import requests
        
        # 1. 创建Worker（带云端配置）
        messages = [{"role": "user", "content": "测试降级"}]
        worker = ChatWorker(
            messages=messages,
            siliconflow_key="invalid_key"  # 无效key会失败
        )
        
        # 2. 模拟云端API失败
        with patch('app.core.api_client.requests.post') as mock_post:
            mock_post.side_effect = requests.exceptions.Timeout("Timeout")
            
            # 应该抛出异常，触发降级逻辑
            try:
                worker._call_siliconflow()
                assert False, "应该抛出超时异常"
            except requests.exceptions.Timeout:
                pass  # 预期行为

    def test_data_persistence_across_sessions(self, tmp_path):
        """测试跨会话数据持久化"""
        data_dir = tmp_path / "test_data"
        
        # 第一次运行：创建数据
        dm1 = DataManager(str(data_dir))
        conv = dm1.new_conversation()
        conv.title = "持久化测试"
        dm1.add_message(conv.id, "user", "第一条消息")
        dm1.save()
        
        # 第二次运行：加载数据
        dm2 = DataManager(str(data_dir))
        conv = dm2.get_conversation(conv.id)
        
        assert conv is not None
        assert len(conv.messages) == 1
        assert conv.messages[0]["content"] == "第一条消息"
        
        # 第三次运行：追加数据
        dm2.add_message(conv.id, "assistant", "第一条回复")
        dm2.save()
        
        # 第四次运行：验证追加
        dm3 = DataManager(str(data_dir))
        conv = dm3.get_conversation(conv.id)
        
        assert len(conv.messages) == 2

    def test_error_handling_in_pipeline(self, tmp_path):
        """测试错误处理流程"""
        # 1. 损坏的JSON文件
        data_dir = tmp_path / "test_data"
        data_dir.mkdir()
        data_file = data_dir / "conversations.json"
        
        with open(data_file, 'w', encoding='utf-8') as f:
            f.write("{broken json")
        
        # DataManager应该能恢复
        dm = DataManager(str(data_dir))
        assert dm.conversations == []
        
        # 2. 继续正常使用
        conv = dm.new_conversation()
        conv.title = "恢复测试"
        assert conv.id is not None

    def test_edge_cases(self, tmp_path):
        """测试边界情况"""
        data_dir = tmp_path / "test_data"
        dm = DataManager(str(data_dir))
        
        # 空消息列表
        conv = dm.new_conversation()
        conv.title = "空会话"
        assert conv.id is not None
        
        # 超长消息
        long_message = "A" * 10000
        dm.add_message(conv.id, "user", long_message)
        conv = dm.get_conversation(conv.id)
        assert len(conv.messages[0]["content"]) == 10000
        
        # 特殊字符
        special_chars = "你好！@#$%^&*()_+-=[]{}|;':\",./<>?"
        dm.add_message(conv.id, "user", special_chars)
        
        # 表情符号
        emojis = "😊🎉❤️👍"
        dm.add_message(conv.id, "user", emojis)
        
        # 验证都能正常保存和加载
        dm.save()
        dm2 = DataManager(str(data_dir))
        conv = dm2.get_conversation(conv.id)
        assert len(conv.messages) == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])