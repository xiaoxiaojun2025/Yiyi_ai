import json
import requests
from PyQt6.QtCore import QThread, pyqtSignal
from config.config import Config


# 网络模型提示词（智能版）
SYSTEM_PROMPT_CLOUD = """你是依依，一位专业、温和的健康咨询助手。

## 核心原则
- 你不是医生，不能诊断疾病或开药，回复时用"可能""建议""倾向于"等措辞
- 基于用户描述和检测数据（心率、血氧）提供分析和建议
- 紧急情况（胸痛+出汗/呼吸困难/意识模糊）立即建议就医或拨打120

## 你的工作方式

收到用户消息后，自然地进行以下思考：

1. **症状识别**：用户是否提到不适（胸闷、头晕、心慌等）
2. **数据解读**：如果有检测数据，结合正常范围分析
   - 心率：60-100 BPM正常，<60偏慢，>100偏快
   - 血氧：95-100%正常，90-94%偏低，<90%危险
3. **关联分析**：症状与数据的关系，可能的原因
4. **个性化回应**：根据具体情况给出针对性建议

## 回复风格

- **自然对话**：像朋友聊天一样，避免机械的清单格式
- **具体可操作**：不说空话，给出实际可行的建议
- **温和专业**：既不过度恐吓，也不轻描淡写
- **灵活应变**：
  - 有症状+有数据：深入分析关联性
  - 有症状+无数据：说明局限性，建议测量
  - 只有数据：解读并主动询问感受
  - 闲聊问题：友好回应，不必强行关联健康
  - 紧急情况：第一句话强调立即就医

## 重要提醒

- 不要说"作为AI""根据我的知识"这类废话
- 不要模板化回复，每次都要针对用户具体情况
- 正常数据不代表没问题，异常数据也不一定很严重
- 建议要具体，比如"记录胸闷发作时间"而非"注意观察"

现在请自然地回应用户。"""

SYSTEM_PROMPT_LOCAL = """你是健康助手依依。请用简短友好的话回答用户问题。

注意：
- 你不是医生，不能诊断或开药
- 如果用户问健康问题，给简单建议并建议就医
- 心率正常范围60-100，血氧正常95-100%
- 紧急情况（胸痛/呼吸困难）建议立即就医
- 其他问题正常聊天即可"""


class ChatWorker(QThread):
    """后台线程：调用 AI API 流式获取回复，支持网络+本地回退"""

    chunk_received = pyqtSignal(str)
    finished = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self, messages: list[dict],
                 siliconflow_key: str = None,
                 siliconflow_model: str = None,
                 ollama_model: str = None,
                 ollama_url: str = None,
                 heart_rate: float = None,
                 blood_oxygen: float = None,
                 parent=None):
        super().__init__(parent)
        self.messages = messages
        self.siliconflow_key = siliconflow_key or Config.SILICONFLOW_API_KEY
        self.siliconflow_model = siliconflow_model or Config.CLOUD_MODEL
        self.ollama_model = ollama_model or Config.LOCAL_MODEL
        self.ollama_url = (ollama_url or Config.OLLAMA_BASE_URL).rstrip("/")
        self.heart_rate = heart_rate
        self.blood_oxygen = blood_oxygen

    def _build_api_messages(self, use_cloud: bool) -> list[dict]:
        """构建 API 请求的消息列表"""
        system_prompt = SYSTEM_PROMPT_CLOUD if use_cloud else SYSTEM_PROMPT_LOCAL

        data_suffix = ""
        if self.heart_rate is not None and self.blood_oxygen is not None:
            data_suffix = f"\n\n[当前用户检测到的数据] 心率: {self.heart_rate:.0f} BPM，血氧: {self.blood_oxygen:.1f}%"

        messages = [{"role": "system", "content": system_prompt + data_suffix}]

        # 过滤掉已有的system消息，只保留user和assistant消息
        recent = [m for m in self.messages if m.get("role") in ("user", "assistant", "ai")]
        
        # 将"ai"角色统一转换为"assistant"（SiliconFlow API要求）
        for msg in recent:
            if msg.get("role") == "ai":
                msg["role"] = "assistant"
        
        if len(recent) > 9:
            recent = recent[-9:]
        
        print(f"[DEBUG] 过滤后的消息数量: {len(recent)}")
        messages.extend(recent)
        return messages

    def run(self):
        try:
            # 优先尝试 SiliconFlow
            if self.siliconflow_key:
                try:
                    result = self._call_siliconflow()
                    if result:  # 成功获取结果
                        self.finished.emit(result)
                        return
                except Exception as e:
                    print(f"[DEBUG] SiliconFlow调用失败: {e}，降级到本地Ollama")
                    # 不发送error_occurred，直接继续执行本地模型
                    # 这样本地模型的输出可以正常显示

            # 回退到本地 Ollama
            self._call_ollama()
        except requests.exceptions.ConnectionError:
            self.error_occurred.emit("无法连接到服务，请检查网络或 Ollama 是否启动")
        except requests.exceptions.Timeout:
            self.error_occurred.emit("请求超时，请稍后再试")
        except requests.exceptions.HTTPError as e:
            detail = ""
            if e.response is not None:
                try:
                    detail = e.response.json().get("message", "")
                except Exception:
                    detail = e.response.text[:200]
            self.error_occurred.emit(f"请求失败({e.response.status_code}): {detail}")
        except Exception as e:
            self.error_occurred.emit(f"发生错误: {str(e)}")

    def _call_siliconflow(self):
        """调用 SiliconFlow API"""
        url = "https://api.siliconflow.cn/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.siliconflow_key}"
        }
        
        messages = self._build_api_messages(use_cloud=True)
        print(f"[DEBUG] 发送的消息数量: {len(messages)}")
        for i, msg in enumerate(messages):
            print(f"[DEBUG] 消息[{i}]: role={msg.get('role')}, content长度={len(msg.get('content', ''))}")
        
        payload = {
            "model": self.siliconflow_model,
            "messages": messages,
            "stream": True,
            "temperature": 0.8,  # 提高创造性
            "top_p": 0.95,       # 增加多样性
            "max_tokens": 4096,  # 允许更长的回复
        }

        full_response = ""
        try:
            with requests.post(url, json=payload, headers=headers, stream=True, timeout=60) as resp:
                print(f"[DEBUG] HTTP状态码: {resp.status_code}")
                if resp.status_code != 200:
                    print(f"[DEBUG] 响应内容: {resp.text[:500]}")
                resp.raise_for_status()
                for line in resp.iter_lines():
                    if not line:
                        continue
                    line_str = line.decode("utf-8")
                    if line_str.startswith("data: "):
                        line_str = line_str[6:]
                    if line_str.strip() == "[DONE]":
                        break
                    data = json.loads(line_str)
                    choices = data.get("choices", [])
                    if not choices:
                        continue
                    delta = choices[0].get("delta", {})
                    content = delta.get("content", "")
                    if content:
                        full_response += content
                        self.chunk_received.emit(content)
            return full_response  # 成功返回结果
        except Exception as e:
            print(f"[DEBUG] SiliconFlow请求异常: {e}")
            raise  # 抛出异常，让run方法捕获并降级到本地

    def _call_ollama(self):
        """调用本地 Ollama API"""
        # 如果是从云端降级过来的，先发送一个提示
        if self.siliconflow_key:
            # 通过发送一个特殊的chunk来显示降级提示
            self.chunk_received.emit("【已切换到本地模型】\n\n")
        
        url = f"{self.ollama_url}/api/chat"
        payload = {
            "model": self.ollama_model,
            "messages": self._build_api_messages(use_cloud=False),
            "stream": True,
            "options": {
                "temperature": 0.8,    # 提高创造性
                "top_p": 0.95,         # 增加多样性
                "num_ctx": 4096,
                "num_predict": 2048,   # 允许更长的回复（从1024增加到2048）
            }
        }

        full_response = ""
        with requests.post(url, json=payload, stream=True, timeout=60) as resp:
            resp.raise_for_status()
            for line in resp.iter_lines():
                if not line:
                    continue
                data = json.loads(line)
                if data.get("done"):
                    break
                content = data.get("message", {}).get("content", "")
                if content:
                    full_response += content
                    self.chunk_received.emit(content)

        self.finished.emit(full_response)



def build_messages(conv_messages: list[dict], max_context: int = 20) -> list[dict]:
    """
    构建发送给 AI 的历史消息列表（不含 system prompt，由 worker 构建）。
    """
    recent = [m for m in conv_messages if m.get("role") != "system"]
    if len(recent) > max_context:
        recent = recent[-max_context:]
    return recent
