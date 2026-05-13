"""
数据管理器测试
测试会话创建、消息添加、数据持久化、自动清理等功能
"""
import pytest
import json
import os
from pathlib import Path
from app.core.data_manager import DataManager, Conversation


class TestDataManager:
    """DataManager测试类"""

    def test_create_data_manager(self, tmp_path):
        """测试创建DataManager实例"""
        data_dir = tmp_path / "test_data"
        dm = DataManager(str(data_dir))
        
        assert dm.data_dir == str(data_dir)
        # 数据目录应该被创建
        assert os.path.exists(dm.data_dir)
        # conversations.json 文件在首次保存前可能不存在
        assert dm.conversations == []

    def test_new_conversation(self, tmp_path):
        """测试创建新会话"""
        dm = DataManager(str(tmp_path / "test_data"))
        
        conv = dm.new_conversation()
        
        assert conv is not None
        assert conv.id is not None
        assert conv.title == "新对话"
        assert conv.messages == []
        assert len(dm.conversations) == 1

    def test_get_conversation(self, tmp_path):
        """测试获取指定会话"""
        dm = DataManager(str(tmp_path / "test_data"))
        
        conv = dm.new_conversation()
        retrieved = dm.get_conversation(conv.id)
        
        assert retrieved is not None
        assert retrieved.id == conv.id
        
        # 测试获取不存在的会话
        non_existent = dm.get_conversation("non_existent_id")
        assert non_existent is None

    def test_add_message(self, tmp_path):
        """测试添加消息到会话"""
        dm = DataManager(str(tmp_path / "test_data"))
        
        conv = dm.new_conversation()
        success = dm.add_message(conv.id, "user", "你好，我最近有点胸闷")
        
        assert success is True
        assert len(conv.messages) == 1
        assert conv.messages[0]["role"] == "user"
        assert conv.messages[0]["content"] == "你好，我最近有点胸闷"
        
        # 测试用户消息自动更新标题
        assert conv.title != "新对话"
        assert "胸闷" in conv.title

    def test_delete_conversation(self, tmp_path):
        """测试删除会话"""
        dm = DataManager(str(tmp_path / "test_data"))
        
        conv = dm.new_conversation()
        assert len(dm.conversations) == 1
        
        dm.delete_conversation(conv.id)
        assert len(dm.conversations) == 0
        assert dm.get_conversation(conv.id) is None

    def test_save_and_load(self, tmp_path):
        """测试数据保存和加载"""
        data_dir = tmp_path / "test_data"
        
        # 创建并保存数据
        dm1 = DataManager(str(data_dir))
        conv = dm1.new_conversation()
        dm1.add_message(conv.id, "user", "测试消息")
        dm1.add_message(conv.id, "assistant", "这是回复")
        
        # 创建新的DataManager实例，应该能加载之前的数据
        dm2 = DataManager(str(data_dir))
        assert len(dm2.conversations) == 1
        
        loaded_conv = dm2.get_conversation(conv.id)
        assert loaded_conv is not None
        assert len(loaded_conv.messages) == 2
        assert loaded_conv.messages[0]["content"] == "测试消息"

    def test_smart_cleanup(self, tmp_path):
        """测试会话数量超过限制时的自动清理"""
        dm = DataManager(str(tmp_path / "test_data"))
        
        # 创建超过限制的会话数
        for i in range(DataManager.MAX_CONVERSATIONS + 5):
            dm.new_conversation()
        
        # 应该只保留MAX_CONVERSATIONS个会话
        assert len(dm.conversations) == DataManager.MAX_CONVERSATIONS

    def test_message_limit(self, tmp_path):
        """测试单个会话消息数量限制"""
        dm = DataManager(str(tmp_path / "test_data"))
        
        conv = dm.new_conversation()
        
        # 添加超过限制的消息数
        for i in range(DataManager.MAX_MESSAGES_PER_CONV + 10):
            dm.add_message(conv.id, "user", f"消息 {i}")
        
        # 应该只保留MAX_MESSAGES_PER_CONV条消息
        assert len(conv.messages) == DataManager.MAX_MESSAGES_PER_CONV

    def test_invalid_json_recovery(self, tmp_path):
        """测试损坏的JSON文件恢复"""
        data_dir = tmp_path / "test_data"
        data_dir.mkdir()
        data_file = data_dir / "conversations.json"
        
        # 写入无效的JSON
        with open(data_file, "w", encoding="utf-8") as f:
            f.write("{ invalid json }")
        
        # DataManager应该能处理这种情况
        dm = DataManager(str(data_dir))
        assert dm.conversations == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])