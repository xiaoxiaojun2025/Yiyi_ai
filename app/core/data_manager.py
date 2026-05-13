import os
import json
from datetime import datetime
from typing import Optional, List
from config.config import Config


class Conversation:
    """会话数据模型"""
    
    def __init__(self, conv_id: str = None, title: str = "新对话",
                 messages: list = None, created_at: str = None, updated_at: str = None,
                 heart_rate: float = None, blood_oxygen: float = None,
                 last_measured_at: str = None):
        self.id = conv_id or datetime.now().strftime("%Y%m%d%H%M%S")[:8]
        self.title = title
        self.messages = messages or []
        self.created_at = created_at or datetime.now().strftime("%Y-%m-%d %H:%M")
        self.updated_at = updated_at or self.created_at
        self.heart_rate = heart_rate
        self.blood_oxygen = blood_oxygen
        self.last_measured_at = last_measured_at
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "messages": self.messages,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "heart_rate": self.heart_rate,
            "blood_oxygen": self.blood_oxygen,
            "last_measured_at": self.last_measured_at
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Conversation':
        return cls(
            conv_id=data.get("id"),
            title=data.get("title", "新对话"),
            messages=data.get("messages", []),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
            heart_rate=data.get("heart_rate"),
            blood_oxygen=data.get("blood_oxygen"),
            last_measured_at=data.get("last_measured_at"),
        )


class DataManager:
    MAX_CONVERSATIONS = Config.MAX_CONVERSATIONS  # 最多保留的会话数
    MAX_MESSAGES_PER_CONV = 50  # 每个会话最多保留的消息数

    def __init__(self, data_dir: str = None):
        if data_dir is None:
            data_dir = Config.DATA_DIR
        self.data_dir = data_dir
        self.data_file = os.path.join(self.data_dir, "conversations.json")
        # 取消启动时自动创建目录，改为在保存数据时按需创建
        self.conversations: list[Conversation] = []
        self.load()
        self._cleanup_conversations()

    def load(self):
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.conversations = [Conversation.from_dict(d) for d in data]
            except (json.JSONDecodeError, IOError):
                self.conversations = []
        else:
            self.conversations = []

    def save(self) -> bool:
        try:
            # 保存时按需创建目录
            os.makedirs(self.data_dir, exist_ok=True)
            with open(self.data_file, "w", encoding="utf-8") as f:
                json.dump([c.to_dict() for c in self.conversations], f, ensure_ascii=False, indent=2)
            return True
        except (IOError, OSError, TypeError) as e:
            print(f"[DataManager] 保存失败: {e}")
            return False

    def new_conversation(self) -> Conversation:
        conv = Conversation()
        self.conversations.insert(0, conv)
        self._cleanup_conversations()
        self.save()
        return conv

    def get_conversation(self, conv_id: str) -> Optional[Conversation]:
        for c in self.conversations:
            if c.id == conv_id:
                return c
        return None

    def add_message(self, conv_id: str, role: str, content: str) -> bool:
        conv = self.get_conversation(conv_id)
        if conv:
            conv.messages.append({"role": role, "content": content})
            conv.updated_at = datetime.now().strftime("%Y-%m-%d %H:%M")
            if role == "user" and conv.title == "新对话":
                conv.title = content[:20] + ("..." if len(content) > 20 else "")
            self._cleanup_messages(conv)
            return self.save()
        return False

    def delete_conversation(self, conv_id: str) -> bool:
        self.conversations = [c for c in self.conversations if c.id != conv_id]
        self.save()
        return True

    def update_vitals(self, conv_id: str, heart_rate: float, blood_oxygen: float) -> bool:
        conv = self.get_conversation(conv_id)
        if conv:
            conv.heart_rate = heart_rate
            conv.blood_oxygen = blood_oxygen
            conv.last_measured_at = datetime.now().strftime("%Y-%m-%d %H:%M")
            self.save()
            return True
        return False

    def get_all_conversations(self) -> List[Conversation]:
        return self.conversations

    def _cleanup_conversations(self):
        if len(self.conversations) > self.MAX_CONVERSATIONS:
            self.conversations = self.conversations[:self.MAX_CONVERSATIONS]
            self.save()

    def _cleanup_messages(self, conv: Conversation):
        if len(conv.messages) > self.MAX_MESSAGES_PER_CONV:
            conv.messages = conv.messages[-self.MAX_MESSAGES_PER_CONV:]
