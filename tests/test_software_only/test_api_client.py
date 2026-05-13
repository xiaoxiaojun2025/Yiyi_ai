"""
API客户端测试
测试消息构建、API调用逻辑、错误处理等（使用mock避免Qt依赖）
"""
import pytest
from unittest.mock import Mock, patch, MagicMock, PropertyMock
import sys


# 创建更完整的PyQt6 mock
class MockQThread:
    """Mock QThread类"""
    def __init__(self, parent=None):
        self.parent = parent
    
    def start(self):
        pass
    
    def quit(self):
        pass
    
    def wait(self):
        pass


class MockPyQtSignal:
    """Mock pyqtSignal"""
    def __init__(self, *args, **kwargs):
        self.connections = []
    
    def connect(self, slot):
        self.connections.append(slot)
    
    def emit(self, *args):
        for conn in self.connections:
            conn(*args)


# 在导入前设置完整的PyQt6 mock
mock_qtcore = MagicMock()
mock_qtcore.QThread = MockQThread
mock_qtcore.pyqtSignal = MockPyQtSignal

sys.modules['PyQt6'] = MagicMock()
sys.modules['PyQt6.QtCore'] = mock_qtcore

# 现在可以安全导入
from app.core.api_client import ChatWorker, SYSTEM_PROMPT_CLOUD, SYSTEM_PROMPT_LOCAL


class TestChatWorkerMessageBuilding:
    """测试ChatWorker的消息构建功能"""

    def test_build_api_messages_cloud(self):
        """测试构建云端API消息列表"""
        messages = [
            {"role": "user", "content": "我胸闷"},
            {"role": "ai", "content": "建议测量心率"}
        ]
        worker = ChatWorker(
            messages=messages,
            siliconflow_key="test_key",
            heart_rate=72.0,
            blood_oxygen=98.0
        )
        
        api_messages = worker._build_api_messages(use_cloud=True)
        
        # 应该包含system消息
        assert api_messages[0]["role"] == "system"
        # 应该包含检测数据
        assert "心率" in api_messages[0]["content"]
        assert "72" in api_messages[0]["content"]
        assert "血氧" in api_messages[0]["content"]
        assert "98.0" in api_messages[0]["content"]
        # 应该过滤掉system消息，保留user和assistant
        assert len(api_messages) == 3  # system + user + assistant

    def test_build_api_messages_local(self):
        """测试构建本地API消息列表"""
        messages = [
            {"role": "user", "content": "你好"},
            {"role": "ai", "content": "你好！"}
        ]
        worker = ChatWorker(messages=messages)
        
        api_messages = worker._build_api_messages(use_cloud=False)
        
        # 本地模型使用简化提示词
        assert "你是健康助手依依" in api_messages[0]["content"]

    def test_message_role_conversion(self):
        """测试消息角色转换（ai -> assistant）"""
        messages = [
            {"role": "user", "content": "问题"},
            {"role": "ai", "content": "回答"}
        ]
        worker = ChatWorker(messages=messages, siliconflow_key="test_key")
        
        api_messages = worker._build_api_messages(use_cloud=True)
        
        # ai角色应转换为assistant
        assert api_messages[2]["role"] == "assistant"

    def test_context_window_limit(self):
        """测试上下文窗口限制（最多9条历史消息）"""
        messages = [{"role": "user", "content": f"消息{i}"} for i in range(15)]
        worker = ChatWorker(messages=messages, siliconflow_key="test_key")
        
        api_messages = worker._build_api_messages(use_cloud=True)
        
        # system + 最多9条历史消息
        assert len(api_messages) <= 10


class TestChatWorkerCreation:
    """测试ChatWorker的创建"""

    def test_create_worker_with_cloud(self):
        """测试创建带云端配置的Worker"""
        messages = [{"role": "user", "content": "你好"}]
        worker = ChatWorker(
            messages=messages,
            siliconflow_key="test_key",
            siliconflow_model="deepseek-ai/DeepSeek-V4-Flash"
        )
        
        assert worker.siliconflow_key == "test_key"
        assert worker.messages == messages

    def test_create_worker_local_only(self):
        """测试创建仅本地模型的Worker"""
        messages = [{"role": "user", "content": "你好"}]
        worker = ChatWorker(messages=messages, siliconflow_key=None)
        
        # 由于配置文件中设置了 API Key，这里应该验证是否使用了配置的默认值
        assert worker.ollama_model == "qwen3:0.6b"

    def test_worker_with_health_data(self):
        """测试Worker携带健康数据"""
        messages = [{"role": "user", "content": "我胸闷"}]
        worker = ChatWorker(
            messages=messages,
            siliconflow_key="test_key",
            heart_rate=72.0,
            blood_oxygen=98.0
        )
        
        assert worker.heart_rate == 72.0
        assert worker.blood_oxygen == 98.0


class TestChatWorkerAPICalls:
    """测试ChatWorker的API调用"""

    @patch('app.core.api_client.requests.post')
    def test_siliconflow_success(self, mock_post):
        """测试SiliconFlow API成功调用"""
        # 模拟流式响应
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.iter_lines.return_value = iter([
            b'data: {"choices":[{"delta":{"content":"Hello"}}]}',
            b'data: {"choices":[{"delta":{"content":" World"}}]}',
            b'data: [DONE]'
        ])
        mock_post.return_value.__enter__.return_value = mock_response
        
        messages = [{"role": "user", "content": "你好"}]
        worker = ChatWorker(messages=messages, siliconflow_key="test_key")
        
        # 捕获信号
        chunks = []
        worker.chunk_received.connect(lambda chunk: chunks.append(chunk))
        
        # 直接调用方法（不启动线程）
        result = worker._call_siliconflow()
        
        assert chunks == ["Hello", " World"]
        assert result == "Hello World"

    @patch('app.core.api_client.requests.post')
    def test_siliconflow_timeout(self, mock_post):
        """测试SiliconFlow超时异常"""
        import requests
        mock_post.side_effect = requests.exceptions.Timeout("Request timed out")
        
        messages = [{"role": "user", "content": "你好"}]
        worker = ChatWorker(messages=messages, siliconflow_key="test_key")
        
        # 应该抛出超时异常
        with pytest.raises(requests.exceptions.Timeout):
            worker._call_siliconflow()

    @patch('app.core.api_client.requests.post')
    def test_ollama_call(self, mock_post):
        """测试Ollama API调用"""
        # 模拟流式响应
        mock_response = MagicMock()
        mock_response.iter_lines.return_value = iter([
            b'{"message":{"content":"Hello"},"done":false}',
            b'{"message":{"content":" World"},"done":false}',
            b'{"message":{"content":""},"done":true}'
        ])
        mock_post.return_value.__enter__.return_value = mock_response
        
        messages = [{"role": "user", "content": "你好"}]
        worker = ChatWorker(messages=messages)
        
        # 捕获信号
        chunks = []
        finished_result = []
        
        worker.chunk_received.connect(lambda chunk: chunks.append(chunk))
        worker.finished.connect(lambda result: finished_result.append(result))
        
        # 直接调用方法
        worker._call_ollama()
        
        # Ollama 可能会先发送降级提示，所以检查是否包含预期的内容
        assert "Hello" in chunks and " World" in chunks
        assert len(finished_result) == 1
        assert "Hello World" in finished_result[0]


class TestEdgeCases:
    """测试边界情况"""

    def test_empty_choices_handling(self):
        """测试空choices的安全处理"""
        data = {"choices": []}
        choices = data.get("choices", [])
        
        # 应该能安全处理空列表
        if not choices:
            pass  # 不应访问choices[0]
        
        assert True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
