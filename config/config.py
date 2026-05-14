"""
项目配置管理
支持从 .env 文件加载配置
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv


def get_base_path():
    """获取程序运行基础路径（兼容 PyInstaller 打包）"""
    if getattr(sys, 'frozen', False):
        # PyInstaller 打包后的路径（exe 所在目录）
        return Path(sys.executable).parent
    else:
        # 开发环境路径
        return Path(__file__).parent.parent


# 加载 .env 文件（优先使用 exe 同目录下的 .env）
base_path = get_base_path()
env_path = base_path / '.env'
if env_path.exists():
    load_dotenv(env_path)
    print(f"[配置] 已加载配置文件: {env_path}")
else:
    # 尝试从当前工作目录加载
    load_dotenv()
    print("[配置] 未找到 .env 文件，使用默认配置")


class Config:
    """应用配置类"""
    
    # ==================== API 配置 ====================
    SILICONFLOW_API_KEY = os.getenv("SILICONFLOW_API_KEY", "")
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    
    # ==================== 模型配置 ====================
    CLOUD_MODEL = os.getenv("CLOUD_MODEL", "deepseek-ai/DeepSeek-V4-Flash")
    LOCAL_MODEL = os.getenv("LOCAL_MODEL", "qwen3:0.6b")
    
    # ==================== 超时配置 ====================
    CLOUD_TIMEOUT = int(os.getenv("CLOUD_TIMEOUT", "120"))
    LOCAL_TIMEOUT = int(os.getenv("LOCAL_TIMEOUT", "60"))
    
    # ==================== 数据配置 ====================
    MAX_CONVERSATIONS = int(os.getenv("MAX_CONVERSATIONS", "50"))
    
    # 数据目录（打包后使用 exe 同级目录，开发环境使用 app/data）
    if getattr(sys, 'frozen', False):
        DATA_DIR = str(get_base_path() / "data")
    else:
        DATA_DIR = os.getenv("DATA_DIR", str(Path(__file__).parent.parent / "app" / "data"))
    
    CONVERSATIONS_FILE = os.path.join(DATA_DIR, "conversations.json")
    
    # ==================== UI 配置 ====================
    WINDOW_WIDTH = int(os.getenv("WINDOW_WIDTH", "1200"))
    WINDOW_HEIGHT = int(os.getenv("WINDOW_HEIGHT", "800"))
    
    # ==================== 传感器配置 ====================
    USE_REAL_SENSOR = os.getenv("USE_REAL_SENSOR", "False").lower() == "true"
    I2C_BUS = int(os.getenv("I2C_BUS", "1"))
    MAX30102_I2C_ADDRESS = int(os.getenv("MAX30102_I2C_ADDRESS", "0x57"), 16)
    
    # ==================== PDF 导出配置 ====================
    _base_path = get_base_path()
    _pdf_dir = _base_path / "out"
    _pdf_dir.mkdir(parents=True, exist_ok=True)
    PDF_OUTPUT_DIR = str(_pdf_dir)
    
    PDF_FONT = "SimSun"
    
    @classmethod
    def validate(cls):
        """验证配置有效性"""
        if not cls.SILICONFLOW_API_KEY:
            print("[警告] SILICONFLOW_API_KEY 未配置，将仅使用本地模型")
        
        # 确保数据目录存在
        try:
            Path(cls.DATA_DIR).mkdir(parents=True, exist_ok=True)
            # PDF 目录在类加载时已创建
            print(f"[配置] 数据目录: {cls.DATA_DIR}")
            print(f"[配置] PDF输出目录: {cls.PDF_OUTPUT_DIR}")
            print(f"[配置] 使用真实传感器: {cls.USE_REAL_SENSOR}")
        except Exception as e:
            print(f"[错误] 创建目录失败: {e}")


# 初始化配置
Config.validate()