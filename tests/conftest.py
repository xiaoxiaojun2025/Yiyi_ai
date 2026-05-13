"""
pytest 配置文件
提供全局 fixtures 和测试配置
"""
import pytest
import sys
import os
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture
def test_data_dir(tmp_path):
    """创建临时测试数据目录"""
    data_dir = tmp_path / "test_data"
    data_dir.mkdir()
    return data_dir


@pytest.fixture
def sample_conversation():
    """示例会话数据"""
    return {
        "id": "test_conv_001",
        "title": "测试会话",
        "created_at": "2026-05-13 10:00:00",
        "updated_at": "2026-05-13 10:05:00",
        "messages": [
            {
                "role": "user",
                "content": "我最近有点胸闷",
                "timestamp": "2026-05-13 10:00:00"
            },
            {
                "role": "ai",
                "content": "心率64次/分在正常范围，血氧97%也是正常的。",
                "timestamp": "2026-05-13 10:00:05"
            }
        ],
        "heart_rate": 64.0,
        "blood_oxygen": 97.0
    }


@pytest.fixture
def mock_siliconflow_response():
    """模拟 SiliconFlow API 响应"""
    return {
        "choices": [
            {
                "delta": {
                    "content": "这是AI的回复内容"
                }
            }
        ]
    }


@pytest.fixture
def mock_sensor_data():
    """模拟传感器数据"""
    return {
        "heart_rate": 72.0,
        "blood_oxygen": 98.5
    }