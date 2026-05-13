# AI 智能问诊助手

基于 PyQt6 开发的桌面健康咨询应用，部署于飞腾派（Phytium Pi）国产开发板平台。结合 AI 大模型和生理指标监测，为用户提供智能健康咨询服务。

## ✨ 核心功能

### 🤖 双模 AI 对话
- **云端优先**：默认使用 SiliconFlow API（DeepSeek V4），提供专业详细的健康建议
- **本地降级**：网络异常时自动切换到本地 Ollama 模型（qwen3:0.6b），保障可用性
- **流式响应**：实时显示 AI 回复，支持 Markdown 格式渲染
- **上下文感知**：自动结合心率、血氧数据进行个性化分析
- **智能提示词**：云端模型采用开放式引导，本地模型使用简化指令

### 💓 健康监测
- **实时测量**：支持心率（BPM）和血氧饱和度（SpO2%）检测
- **动态可视化**：脉动心形图标，直观展示测量状态
- **数据集成**：测量结果自动关联到当前会话，供 AI 分析参考
- **硬件支持**：已实现 MAX30102 传感器驱动，支持真实硬件数据采集

### 📊 会话管理
- **多会话支持**：侧边栏快速创建、切换历史对话
- **智能清理**：自动管理会话数量（最多50个）和消息长度
- **PDF 导出**：一键生成包含时间、数据、问诊记录的 PDF 报告
- **本地存储**：JSON 格式持久化保存所有对话和测量数据

### 🎨 现代化 UI
- **简洁设计**：参考 ChatGPT/Claude Desktop 风格，清爽舒适
- **响应布局**：可折叠侧边栏，自适应窗口大小
- **流畅动画**：等待指示器、脉动心形等交互动画
- **模块化架构**：清晰的代码结构，便于维护和扩展

## 🏗️ 项目结构

```
feiteng_ai_doctor/
├── main.py                     # 应用入口
├── app/                        # 核心应用模块
│   ├── __init__.py
│   ├── main_window.py          # 主窗口控制器
│   ├── core/                   # 核心业务逻辑
│   │   ├── __init__.py
│   │   ├── data_manager.py     # 数据管理（会话 CRUD）
│   │   ├── api_client.py       # AI API 客户端（云端+本地）
│   │   └── pdf_generator.py    # PDF 报告生成器
│   ├── ui/                     # UI 组件
│   │   ├── __init__.py
│   │   ├── styles.py           # 全局样式定义
│   │   ├── widgets/            # 自定义控件
│   │   │   ├── __init__.py
│   │   │   ├── typing_indicator.py  # 等待动画
│   │   │   ├── doctor_avatar.py     # 医生头像
│   │   │   └── heart_icon.py        # 心形图标
│   │   └── pages/              # 页面组件
│   │       ├── __init__.py
│   │       ├── chat_page.py         # 聊天页面
│   │       ├── measure_page.py      # 测量页面
│   │       └── sidebar.py           # 侧边栏
│   └── hardware/               # 硬件相关
│       ├── __init__.py
│       └── sensor_worker.py    # 传感器工作线程
├── config/                     # 配置管理
│   ├── __init__.py
│   └── config.py               # 配置类（从 .env 读取）
├── max30102-master/            # MAX30102 传感器驱动库
│   ├── max30102.py             # I2C 通信驱动
│   ├── hrcalc.py               # 心率血氧计算算法
│   └── heartrate_monitor.py    # 心率监测示例
├── tests/                      # 测试目录
│   ├── pytest.ini              # pytest 配置
│   ├── run_tests.py            # 测试运行脚本
│   ├── test_software_only/     # 纯软件测试
│   └── test_with_hardware/     # 硬件相关测试
├── app/data/                   # 数据存储目录
│   └── conversations.json      # 对话历史记录
├── out/                        # PDF 报告输出目录
├── .env                        # 配置文件（敏感信息，不提交 Git）
├── .env.example                # 配置模板
├── .gitignore                  # Git 忽略规则
└── README.md                   # 项目说明文档
```

## 🚀 快速开始

### 前置要求

#### 软件依赖

  Python 3.8+
  
  PyQt6
  
  requests
  
  reportlab（PDF 生成）
  
  python-dotenv（配置管理）
  
  numpy（传感器数据处理）
  
  smbus2（I2C 总线通信，Linux 环境）

#### 硬件要求

如需使用真实传感器测量功能，需要：

  飞腾派（Phytium Pi）开发板或兼容 Linux 的开发板
  
  MAX30102 心率血氧传感器模块
  
  I2C 接口连接线缆

### 安装依赖

```bash
pip install PyQt6 requests reportlab python-dotenv numpy smbus2
```

### 配置 API Key

1. **复制配置模板**
   ```bash
   cp .env.example .env
   ```

2. **编辑 `.env` 文件**，填入真实的 API Key：
   ```ini
   SILICONFLOW_API_KEY=sk-your-api-key-here
   CLOUD_MODEL=deepseek-ai/DeepSeek-V4-Flash
   LOCAL_MODEL=qwen3:0.6b
   ```

3. **启动 Ollama 服务**（可选，用于本地模型）
   ```bash
   ollama serve
   ollama pull qwen3:0.6b
   ```

### 硬件配置（如使用真实传感器）

1. **连接 MAX30102 传感器**
   ```
   MAX30102    飞腾派
   VCC      →  3.3V
   GND      →  GND
   SDA      →  SDA (I2C)
   SCL      →  SCL (I2C)
   ```

2. **验证 I2C 设备**
   ```bash
   sudo apt-get install i2c-tools
   sudo i2cdetect -y 1
   # 应该能看到地址 0x57 的设备
   ```

3. **修改 `.env` 配置**
   ```ini
   USE_REAL_SENSOR=True
   I2C_BUS=1
   MAX30102_I2C_ADDRESS=0x57
   ```

4. **设置 I2C 权限**
   ```bash
   sudo usermod -aG i2c $USER
   # 或临时使用 sudo 运行
   sudo python main.py
   ```

### 运行应用

```bash
python main.py
```

## 📖 使用说明

### 1. AI 对话问诊

1. 点击左侧 **"新对话"** 按钮创建会话
2. 在底部输入框描述症状（如："我最近胸闷，有点担心"）
3. 按 **Enter** 或点击 **"发送"** 按钮
4. AI 医生会实时返回分析和建议
5. 云端模型失败时自动降级到本地模型，并在消息开头显示提示

### 2. 健康数据测量

#### 模拟模式（默认）

1. 点击右上角 **"♥ 测量"** 按钮进入测量页面
2. 点击 **"开始测量"** 按钮
3. 系统自动生成模拟的心率和血氧数据
4. 等待约 3-5 秒完成测量
5. 测量完成后自动返回对话页面，数据将用于 AI 分析

#### 真实传感器模式

1. 确保已完成硬件配置步骤
2. 将手指轻放在 MAX30102 传感器上
3. 保持手指稳定，避免移动
4. 等待 3-5 秒采集足够数据
5. 测量完成后自动返回对话页面

### 3. 导出 PDF 报告

1. 在侧边栏找到目标会话
2. 点击会话右侧的 **📄 导出图标**
3. 输入文件名（默认：标题_时间）
4. 确认后自动生成 PDF 到 `out/` 目录
5. PDF 包含：基本信息、检测数据、完整问诊记录、免责声明

### 4. 会话管理

- **切换会话**：点击左侧列表中的历史对话
- **删除会话**：系统自动清理超过50个的旧会话
- **折叠侧边栏**：点击左上角菜单按钮 ☰

## 🧪 测试

项目包含完整的测试套件，覆盖核心业务逻辑和硬件交互。

### 运行测试

```bash
cd tests

# 运行纯软件测试（推荐，无需硬件）
python run_tests.py

# 运行所有测试（包括硬件测试）
python run_tests.py all

# 运行特定测试文件
python run_tests.py test_data_manager.py
```

### 测试结果

- ✅ **35个核心测试通过** - 数据管理、API 客户端、PDF 生成、集成测试
- ⏭️ **13个UI测试跳过** - Windows 环境限制（在飞腾派 Linux 环境可正常运行）
- 📊 **覆盖率**：核心业务逻辑 100%

## 🔧 技术架构

### 核心模块

| 模块 | 文件 | 职责 |
|------|------|------|
| 配置管理 | `config/config.py` | 从 .env 文件读取配置，统一管理 API Key、模型、超时等参数 |
| 主窗口 | `main_window.py` | 协调各组件，管理页面切换和信号连接 |
| 聊天页面 | `chat_page.py` | 消息气泡、流式显示、Markdown 渲染、动态尺寸调整 |
| 测量页面 | `measure_page.py` | 传感器控制、数据可视化、心形图标动画 |
| 侧边栏 | `sidebar.py` | 会话列表、新建/切换/导出功能 |
| 数据管理 | `data_manager.py` | 会话 CRUD、JSON 持久化、智能清理 |
| API 客户端 | `api_client.py` | SiliconFlow/Ollama 流式请求、自动降级机制 |
| PDF 生成 | `pdf_generator.py` | Markdown 渲染、HTML 格式化、PDF 导出 |
| 传感器 | `sensor_worker.py` | 后台线程采集数据（支持模拟和真实传感器） |
| MAX30102驱动 | `max30102-master/max30102.py` | I2C 通信、原始数据采集 |
| 心率算法 | `max30102-master/hrcalc.py` | PPG 信号处理、心率血氧计算 |

### 数据流

```
用户输入 → DataManager (保存) → ChatWorker (API 请求) 
         → 流式响应 → UI 更新 → DataManager (保存 AI 回复)
         
测量数据 → SensorWorker → MeasurePage (显示) 
         → Conversation (存储) → AI 分析时读取

导出请求 → PDFGenerator → Markdown 解析 → HTML 格式化 → PDF 文件
```

### AI 模型配置

**云端模型（SiliconFlow）**：
- 默认模型：`deepseek-ai/DeepSeek-V4-Flash`
- 超时时间：120 秒
- 优势：智能度高，回复详细专业
- 降级策略：失败时自动切换到本地模型

**本地模型（Ollama）**：
- 默认模型：`qwen3:0.6b`
- 超时时间：60 秒
- 优势：隐私保护，离线可用，响应快速
- 限制：模型较小，回复相对简洁

**提示词策略**：
- 云端：开放式引导，鼓励自然对话和深度分析
- 本地：简化指令，聚焦核心功能，适配小模型能力

### 传感器工作原理

**MAX30102 传感器**：
- 采用光电容积脉搏波描记法（PPG）
- 红光 LED（660nm）和红外光 LED（940nm）交替照射皮肤
- 光电二极管接收反射光信号
- 通过 I2C 总线传输原始数据

**心率计算**：
- 采集 100 个红外光样本
- 去直流分量，提取交流信号
- 峰值检测算法识别心跳周期
- 根据采样率计算心率（BPM）

**血氧计算**：
- 同时采集红光和红外光数据
- 计算 AC/DC 比值（R = (AC_red/DC_red) / (AC_ir/DC_ir)）
- 使用经验公式转换：SpO2 = -45.060×R² + 30.054×R + 94.845
- 有效范围：70%-100%

### 容错机制

1. **网络异常处理**：云端 API 超时时自动降级到本地模型
2. **空数据处理**：API 返回空 choices 时跳过，避免崩溃
3. **错误提示**：红色警告条显示问题，不中断用户体验
4. **资源清理**：Widget 关闭时正确释放定时器和信号
5. **传感器异常**：捕获 I2C 通信错误，提示检查硬件连接

## 📝 开发指南

### 添加新功能

1. **新增页面**：在 `app/ui/pages/` 下创建新的 Widget 类
2. **注册路由**：在 `MainWindow._setup_ui()` 中添加页面到 `QStackedWidget`
3. **数据持久化**：在 `Conversation` 类中添加新字段，更新序列化方法
4. **样式定义**：在 `app/ui/styles.py` 中添加 QSS 样式

### 配置管理

所有配置项集中在 `config/config.py` 中，通过 `.env` 文件管理：

```python
from config.config import Config

# 访问配置
api_key = Config.SILICONFLOW_API_KEY
model = Config.CLOUD_MODEL
timeout = Config.CLOUD_TIMEOUT
use_sensor = Config.USE_REAL_SENSOR
```

### 传感器数据优化

如需调整传感器采样参数：

1. **修改采样率**：在 `max30102.py` 中调整 `REG_SPO2_CONFIG`
   - 0x27 = 100Hz（默认）
   - 0x23 = 50Hz（降低 CPU 占用）

2. **调整样本数量**：在 `sensor_worker.py` 中修改 `read_sequential(amount=100)`
   - 减少样本数可提高响应速度
   - 增加样本数可提高准确性

3. **优化滤波算法**：在 `hrcalc.py` 中调整移动平均窗口大小

### 自定义样式

所有样式定义在 `app/ui/styles.py` 中，采用 Qt 样式表（QSS）语法。主要配色：

- 主色：`#4A90D9`（品牌蓝）
- 辅助色：`#E74C3C`（测量红）
- 背景：`#F5F5F5` / `#FFFFFF`
- 文本：`#333333` / `#666666`

### PDF 报告定制

修改 `app/core/pdf_generator.py` 中的 `_format_ai_message()` 方法，可调整：
- Markdown 渲染规则（标题、加粗、列表等）
- 字体大小和颜色
- 页面边距和布局
- 添加公司 Logo 或水印

## 📚 相关文档

- [HARDWARE_DEPLOY.md](HARDWARE_DEPLOY.md) - 详细的硬件部署指南
- [CONFIG.md](CONFIG.md) - 配置项详细说明
- [系统设计文档.docx](系统设计文档.docx) - 校赛设计文档

## ⚠️ 免责声明

本应用提供的健康建议仅供参考，**不能替代专业医疗诊断**。如有严重不适，请立即就医或拨打急救电话（120）。

## 📄 许可证

本项目仅供学习和个人使用。

## 🙏 致谢

- [MAX30102 Raspberry Pi Driver](https://github.com/vrano714/max30102-tutorial-raspberrypi) - 传感器驱动基础代码
- [PyQt6](https://www.riverbankcomputing.com/software/pyqt/) - GUI 框架
- [SiliconFlow](https://siliconflow.cn/) - 云端 AI API 服务
- [Ollama](https://ollama.ai/) - 本地大模型运行平台
- [ReportLab](https://www.reportlab.com/) - PDF 生成库
- [pytest](https://docs.pytest.org/) - 测试框架
- [python-dotenv](https://pypi.org/project/python-dotenv/) - 配置管理
- [NumPy](https://numpy.org/) - 科学计算库
- [smbus2](https://pypi.org/project/smbus2/) - I2C 通信库