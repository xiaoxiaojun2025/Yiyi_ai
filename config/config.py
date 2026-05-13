"""
项目配置管理
从环境变量或 .env 文件读取配置，避免硬编码敏感信息
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# 加载 .env 文件（如果存在）
load_dotenv()


class Config:
    """应用配置类"""
    
    # ==================== API 配置 ====================
    # SiliconFlow API Key（云端模型）
    SILICONFLOW_API_KEY = os.getenv("SILICONFLOW_API_KEY", "")
    
    # Ollama 本地服务地址
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    
    # ==================== 模型配置 ====================
    # 云端模型名称
    CLOUD_MODEL = os.getenv("CLOUD_MODEL", "deepseek-ai/DeepSeek-V4-Flash")
    
    # 本地模型名称
    LOCAL_MODEL = os.getenv("LOCAL_MODEL", "qwen3:0.6b")
    
    # ==================== 超时配置 ====================
    # 云端 API 超时时间（秒）
    CLOUD_TIMEOUT = int(os.getenv("CLOUD_TIMEOUT", "120"))
    
    # 本地模型超时时间（秒）
    LOCAL_TIMEOUT = int(os.getenv("LOCAL_TIMEOUT", "60"))
    
    # ==================== 数据配置 ====================
    # 最大会话数量
    MAX_CONVERSATIONS = int(os.getenv("MAX_CONVERSATIONS", "50"))
    
    # 数据目录（相对于项目根目录）
    DATA_DIR = os.getenv("DATA_DIR", str(Path(__file__).parent.parent / "app" / "data"))
    
    # 会话数据文件
    CONVERSATIONS_FILE = os.path.join(DATA_DIR, "conversations.json")
    
    # ==================== UI 配置 ====================
    # 窗口尺寸
    WINDOW_WIDTH = int(os.getenv("WINDOW_WIDTH", "1200"))
    WINDOW_HEIGHT = int(os.getenv("WINDOW_HEIGHT", "800"))
    
    # ==================== 传感器配置 ====================
    # 是否使用真实传感器（False 为模拟模式）
    USE_REAL_SENSOR = os.getenv("USE_REAL_SENSOR", "False").lower() == "true"
    
    # I2C 总线号
    I2C_BUS = int(os.getenv("I2C_BUS", "1"))
    
    # MAX30102 I2C 地址
    MAX30102_I2C_ADDRESS = int(os.getenv("MAX30102_I2C_ADDRESS", "0x57"), 16)
    
    # ==================== PDF 导出配置 ====================
    # PDF 输出目录
    PDF_OUTPUT_DIR = os.getenv("PDF_OUTPUT_DIR", str(Path(__file__).parent.parent / "out"))
    
    # PDF 字体（中文字体）
    PDF_FONT = os.getenv("PDF_FONT", "SimSun")  # 宋体
    
    @classmethod
    def validate(cls):
        """验证配置有效性"""
        if not cls.SILICONFLOW_API_KEY:
            print("[警告] SILICONFLOW_API_KEY 未配置，将仅使用本地模型")
        
        # 确保数据目录存在
        Path(cls.DATA_DIR).mkdir(parents=True, exist_ok=True)
        Path(cls.PDF_OUTPUT_DIR).mkdir(parents=True, exist_ok=True)


# 初始化配置
Config.validate()