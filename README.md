# Petbot - 智能桌面机器人系统

<div align="center">

**一个集成语音交互、人脸识别、表情控制和智能对话的桌面机器人系统**

[功能特性](#功能特性) • [系统架构](#系统架构) • [快速开始](#快速开始) • [详细原理](#详细原理) • [使用方法](#使用方法)

</div>

---

## 📋 目录

- [功能特性](#功能特性)
- [系统架构](#系统架构)
- [项目结构](#项目结构)
- [系统流程图](#系统流程图)
- [详细原理](#详细原理)
- [环境要求](#环境要求)
- [快速开始](#快速开始)
- [使用方法](#使用方法)
- [配置说明](#配置说明)
- [故障排除](#故障排除)
- [开发指南](#开发指南)

---

## ✨ 功能特性

### 核心功能

#### 🎤 语音交互系统
- **ASR（语音识别）**: 实时将语音转换为文字，支持中文
- **TTS（语音合成）**: 将文字转换为自然语音输出
- **回声消除**: 支持实时语音交互

#### 🤖 AI 对话系统（LangGraph Agent v2.0）
- **LangGraph Agent**: 基于状态图的智能状态管理和工具调用框架
- **Deepseek LLM**: 提供强大的中文对话能力
- **工具扩展**: 支持天气查询、人脸记忆等工具
- **上下文记忆**: 保持对话连贯性，支持多轮对话
- **可扩展框架**: 轻松添加新工具和功能

#### 👤 人脸识别与记忆
- **实时人脸检测**: 使用 face_recognition 库进行高精度检测
- **人脸识别**: 识别已知人物并显示名字
- **语音记忆功能**: 说"记住我的脸，我是XXX"自动记录
- **自动截图保存**: 将人脸照片保存到本地数据库
- **动态刷新**: 支持运行时自动检测并重新加载人脸数据库

#### 🎭 智能表情控制
- **自动表情切换**: 根据识别结果智能改变表情
  - 看到认识的人 → 😊 开心 (happy)
  - 看到陌生人 → 😲 惊讶 (surprised)
  - 没有人 → 😐 中性 (neutral)
- **防抖机制**: 避免频繁切换，提升体验
- **可自定义**: 支持多种表情和场景模式
- **独立窗口显示**: 全屏显示表情动画

#### 🎯 身体控制
- **头部跟踪**: 自动转头面向检测到的人脸
- **手势控制**: 支持预定义的动作和姿态
- **表情显示**: 通过屏幕显示丰富的表情动画

---

## 🏗️ 系统架构

### 整体架构

Petbot 采用**分布式 ROS2 节点架构**，各模块通过话题（Topic）和服务（Service）进行通信：

```
┌─────────────────────────────────────────────────────────────────┐
│                        Petbot 系统架构                           │
└─────────────────────────────────────────────────────────────────┘

┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   用户语音    │────▶│   ASR Node   │────▶│  识别文本     │
└──────────────┘     └──────────────┘     └──────────────┘
                                                  │
                                                  ▼
                          ┌───────────────────────────────────┐
                          │        Chat Node (LangGraph)      │
                          │  ┌──────────────────────────────┐ │
                          │  │   LangGraph Agent            │ │
                          │  │  ┌────────────┬───────────┐  │ │
                          │  │  │ Deepseek   │  Tools    │  │ │
                          │  │  │    LLM     │  - 天气   │  │ │
                          │  │  │            │  - 记忆   │  │ │
                          │  │  └────────────┴───────────┘  │ │
                          │  └──────────────────────────────┘ │
                          └───────────────────────────────────┘
                                  │              │
                    ┌─────────────┴──────┐       │
                    ▼                    ▼       ▼
          ┌──────────────┐    ┌──────────────┐  │
          │   TTS Node   │    │ 特殊命令处理  │  │
          │  (语音输出)   │    │ "记住我的脸" │  │
          └──────────────┘    └──────────────┘  │
                    │                    │       │
                    ▼                    ▼       │
          ┌──────────────┐         ┌────▼──────────────┐
          │  AI 语音回复  │         │ Face Capture Svc  │
          └──────────────┘         └───────────────────┘

┌──────────────────────────────────────────────────────────┐
│             Face Detection Node (人脸识别)                │
│                                                           │
│  摄像头 → 人脸检测 → 人脸识别 → 状态判断                  │
│              │          │          │                      │
│              │          │          └─────┐                │
│              │          │                ▼                │
│              │          │      ┌─────────────────┐       │
│              │          │      │  表情控制逻辑    │       │
│              │          │      │ - 全认识:happy   │       │
│              │          │      │ - 陌生人:surprised│      │
│              │          │      │ - 无人:neutral   │       │
│              │          │      └─────────────────┘       │
│              │          │                │                │
│              │          ▼                ▼                │
│              │   ┌────────────┐  ┌────────────┐         │
│              │   │ 发布识别    │  │ HTTP请求   │         │
│              │   │   结果      │  │ 表情服务器  │         │
│              │   └────────────┘  └────────────┘         │
│              │          │                                 │
│              ▼          ▼                                 │
│      ┌─────────────────────────┐                        │
│      │   显示窗口（人脸框+名字） │                        │
│      └─────────────────────────┘                        │
└──────────────────────────────────────────────────────────┘
                             │
                             ▼
                 ┌────────────────────┐
                 │  Turn Head Node    │
                 │   (头部跟踪)        │
                 │  订阅人脸位置       │
                 │  控制头部转向       │
                 └────────────────────┘

┌──────────────────────────────────────────────────────────┐
│           Expression Server (表情服务器)                  │
│                                                           │
│  HTTP API (8001端口)                                     │
│  接收表情切换请求 → 播放对应视频                          │
│  全屏显示表情动画                                         │
└──────────────────────────────────────────────────────────┘
```

### ROS2 通信机制

#### 话题 (Topics)

| 话题名称 | 类型 | 发布者 | 订阅者 | 说明 |
|---------|------|--------|--------|------|
| `/asr_result` | String | ASR Node | Chat Node | ASR识别结果 |
| `/face_recognition_result` | String | Face Detection Node | Chat Node, Turn Head Node | 人脸识别结果（JSON格式） |
| `/ai_thinking` | String | Chat Node | Interactive Monitor | AI思考状态信号 |
| `/chat_response` | String | Chat Node | TTS Node, Interactive Monitor | AI回复文本 |
| `/tts_life` | String | TTS Node | Interactive Monitor | TTS播放状态 |

#### 服务 (Services)

| 服务名称 | 类型 | 提供者 | 调用者 | 说明 |
|---------|------|--------|--------|------|
| `/tts_service_wait` | SetString | TTS Node | Chat Node | TTS语音合成服务（阻塞式） |
| `/capture_face` | SetString | Face Detection Node | Chat Node | 人脸截图服务（用于"记住我的脸"） |
| `/reload_faces` | SetString | Face Detection Node | 外部调用 | 手动刷新人脸数据库 |

---

## 📁 项目结构

```
Petbot/
├── nodes/                      # ROS2 节点
│   ├── chat/                   # 对话系统
│   │   ├── chat_node.py       # Chat节点（主文件）
│   │   ├── agent.py           # LangGraph Agent实现
│   │   ├── weather_tool.py    # 天气查询工具
│   │   └── __init__.py
│   ├── vision/                 # 视觉系统
│   │   └── face_detection_node.py  # 人脸识别节点
│   ├── body_control/          # 身体控制
│   │   ├── turn_head.py       # 头部跟踪（完整版）
│   │   ├── turn_head copy.py  # 头部跟踪（简化版）
│   │   ├── gestures_node.py   # 手势控制
│   │   └── body_controller.py # 身体控制器
│   ├── expression/            # 表情视频资源
│   │   ├── happy.mp4
│   │   ├── surprised.mp4
│   │   ├── neutral.mp4
│   │   └── ...                # 18个表情视频
│   ├── expression_server.py   # 表情服务器（FastAPI）
│   ├── asr_node.py            # 语音识别节点
│   └── tts_node.py            # 语音合成节点
│
├── images/                    # 图像资源
│   └── known_faces/          # 已知人脸数据库（不提交到Git）
│       └── {人名}.jpg        # 人脸照片（文件名即人名）
│
├── test/                      # 测试脚本
│   ├── test_agent_interactive.py # 交互式测试AI对话
│   ├── test_chat_agent.py    # 测试AI对话
│   ├── test_video.py         # 测试摄像头
│   └── test_face_recognition.py # 测试人脸识别
│
├── ros2_ws/                   # ROS2 工作空间
│   └── src/                   # ROS2 包源码
│
├── service_define/            # ROS2 服务定义
│   └── srv/                   # 服务接口定义
│
├── setup.sh                  # 一键环境配置脚本（从头开始配置）
├── start_all.sh              # 一键启动脚本（启动完整系统）
├── activate.sh               # 快速环境激活脚本
├── interactive_monitor.py    # 交互式监控界面
├── .env                      # 配置文件（不提交到Git）
├── env.example              # 配置示例
├── requirements.txt          # Python依赖（统一依赖文件）
└── README.md                # 本文档
```

---

## 🔄 系统流程图

### 1. 语音对话流程

```
用户说话
    ↓
[ASR Node] 语音识别
    ↓
发布 /asr_result 话题
    ↓
[Chat Node] 接收识别文本
    ↓
[LangGraph Agent] 处理对话
    ├─→ 调用工具（如天气查询）
    └─→ 生成回复文本
    ↓
发布 /chat_response 话题
    ↓
[TTS Node] 接收回复文本
    ↓
语音合成并播放
    ↓
用户听到回复
```

### 2. 人脸记忆流程

```
用户说："记住我的脸，我是张三"
    ↓
[ASR Node] 识别语音
    ↓
[Chat Node] 检测特殊命令
    ↓
调用 /capture_face 服务
    ↓
[Face Detection Node] 处理请求
    ├─→ 检测当前画面中的人脸
    ├─→ 验证只有1张人脸
    ├─→ 保存照片到 images/known_faces/张三.jpg
    └─→ 重新加载人脸数据库
    ↓
返回成功/失败结果
    ↓
[Chat Node] 生成回复
    ↓
[TTS Node] 播放："好的，我已经记住张三的脸了！"
```

### 3. 智能表情切换流程

```
[Face Detection Node] 持续检测人脸
    ↓
每帧进行人脸识别
    ├─→ 检测到人脸位置
    ├─→ 与已知人脸数据库比对
    └─→ 判断识别结果
    ↓
判断状态：
    ├─→ 全是认识的人 → all_known
    ├─→ 有陌生人 → has_unknown
    └─→ 没有人脸 → no_face
    ↓
状态变化检测（防抖机制）
    ↓
HTTP POST 请求 Expression Server
    POST /expression/{表情名}
    ↓
[Expression Server] 切换表情视频
    ├─→ 停止当前视频
    ├─→ 加载新表情视频
    └─→ 在独立窗口播放
    ↓
用户看到表情变化
```

### 4. 头部跟踪流程

```
[Face Detection Node] 检测到人脸
    ↓
发布 /face_recognition_result 话题
    ├─→ 包含人脸位置信息
    └─→ 包含人脸中心坐标
    ↓
[Turn Head Node] 订阅话题
    ↓
计算头部转向角度
    ├─→ 根据人脸中心位置
    └─→ 计算目标角度
    ↓
控制头部舵机
    ├─→ 平滑转向
    └─→ 面向人脸
```

### 5. 完整交互流程（综合）

```
┌─────────────────────────────────────────────────────────┐
│ 用户进入视野                                              │
└─────────────────────────────────────────────────────────┘
            ↓
┌─────────────────────────────────────────────────────────┐
│ [Face Detection] 检测到人脸                              │
│   - 识别：认识/陌生人                                     │
│   - 发布识别结果                                          │
└─────────────────────────────────────────────────────────┘
            ↓
┌─────────────────────────────────────────────────────────┐
│ [Expression Server] 根据识别结果切换表情                  │
│   - 认识的人 → happy                                      │
│   - 陌生人 → surprised                                    │
└─────────────────────────────────────────────────────────┘
            ↓
┌─────────────────────────────────────────────────────────┐
│ [Turn Head Node] 头部转向人脸                             │
└─────────────────────────────────────────────────────────┘
            ↓
┌─────────────────────────────────────────────────────────┐
│ 用户说话："你好"                                           │
└─────────────────────────────────────────────────────────┘
            ↓
┌─────────────────────────────────────────────────────────┐
│ [ASR Node] 识别语音 → "你好"                              │
└─────────────────────────────────────────────────────────┘
            ↓
┌─────────────────────────────────────────────────────────┐
│ [Chat Node] 处理对话                                      │
│   - LangGraph Agent 理解意图                              │
│   - 生成回复："你好！有什么可以帮你的吗？"                 │
└─────────────────────────────────────────────────────────┘
            ↓
┌─────────────────────────────────────────────────────────┐
│ [TTS Node] 语音合成并播放                                 │
└─────────────────────────────────────────────────────────┘
            ↓
┌─────────────────────────────────────────────────────────┐
│ 用户听到回复，继续对话...                                  │
└─────────────────────────────────────────────────────────┘
```

---

## 🔬 详细原理

### 1. LangGraph Agent 架构

#### 1.1 核心概念

**LangGraph** 是一个基于状态图的 Agent 框架，用于构建复杂的 AI 应用。Petbot 使用 LangGraph 实现智能对话系统。

#### 1.2 状态定义

```python
class AgentState(TypedDict):
    """Agent的状态定义"""
    messages: Annotated[Sequence[BaseMessage], operator.add]
```

- **messages**: 对话历史列表，包含用户消息、AI回复和工具调用结果
- **自动累积**: 使用 `operator.add` 自动将新消息添加到历史中

#### 1.3 状态图结构

```
┌─────────────┐
│   START     │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│  should_continue│  ← 判断是否继续
└──────┬──────────┘
       │
   ┌───┴───┐
   │       │
   ▼       ▼
┌─────┐ ┌──────┐
│ END │ │ call │  ← 调用LLM或工具
└─────┘ └───┬──┘
            │
            ▼
      ┌─────────┐
      │  tools  │  ← 执行工具
      └────┬────┘
           │
           ▼
      ┌─────────┐
      │  call   │  ← 继续对话
      └─────────┘
```

#### 1.4 工作流程

1. **接收用户输入**: Chat Node 将 ASR 识别结果传入 Agent
2. **状态更新**: 将用户消息添加到 `messages` 状态中
3. **LLM 调用**: 
   - 将对话历史发送给 Deepseek LLM
   - LLM 分析意图，决定是否需要调用工具
4. **工具调用**（如需要）:
   - LLM 返回工具调用请求
   - ToolNode 执行对应工具（如天气查询）
   - 工具结果添加到 `messages` 中
5. **生成回复**: LLM 基于工具结果生成最终回复
6. **返回结果**: 将回复文本返回给 Chat Node

#### 1.5 工具系统

**工具定义**:

```python
@tool
def query_weather(city: str) -> str:
    """查询指定城市的天气信息"""
    return weather_query_func(city)

@tool
def remember_face(person_name: str) -> str:
    """记住用户的脸部特征"""
    return f"__REMEMBER_FACE_REQUEST__|{person_name}"
```

**工具注册**:

```python
self.tools = [query_weather, remember_face]
self.llm_with_tools = self.llm.bind_tools(self.tools)
```

**工具调用流程**:

1. LLM 分析用户意图
2. 如果识别到需要工具（如"北京天气"），LLM 返回工具调用请求
3. ToolNode 执行工具函数
4. 工具结果作为 ToolMessage 添加到对话历史
5. LLM 基于工具结果生成最终回复

#### 1.6 上下文记忆

- **自动管理**: LangGraph 自动维护对话历史
- **多轮对话**: 支持上下文相关的对话
- **内存存储**: 对话历史保存在内存中（不持久化）

### 2. 人脸识别系统

#### 2.1 技术栈

- **face_recognition**: 基于 dlib 的人脸识别库
- **OpenCV**: 图像处理和摄像头控制
- **HOG 检测器**: 用于人脸检测

#### 2.2 人脸检测原理

1. **图像预处理**:
   - 缩放图像（默认 0.25 倍）以提高检测速度
   - 转换为 RGB 格式（face_recognition 要求）

2. **人脸定位**:
   ```python
   face_locations = face_recognition.face_locations(
       small_frame, 
       model='hog'  # 使用 HOG 模型
   )
   ```
   - 返回人脸边界框坐标 `(top, right, bottom, left)`

3. **性能优化**:
   - 降低检测分辨率（`detection_scale=0.25`）
   - 每 N 帧检测一次（可配置）
   - 使用 HOG 模型（比 CNN 快）

#### 2.3 人脸识别原理

1. **编码提取**:
   ```python
   face_encodings = face_recognition.face_encodings(
       image, 
       known_face_locations
   )
   ```
   - 使用深度神经网络提取 128 维特征向量

2. **特征比对**:
   ```python
   matches = face_recognition.compare_faces(
       known_face_encodings,  # 已知人脸编码列表
       face_encoding,         # 当前人脸编码
       tolerance=0.6          # 相似度阈值
   )
   ```
   - 计算欧氏距离
   - 阈值越小，要求越严格

3. **识别结果**:
   - 找到匹配 → 返回对应人名
   - 无匹配 → 返回 "Unknown"

#### 2.4 人脸记忆功能

**工作流程**:

1. **命令识别**: Chat Node 检测"记住我的脸"命令
2. **服务调用**: 调用 `/capture_face` 服务
3. **人脸验证**:
   - 检查画面中是否有且仅有 1 张人脸
   - 防止误操作
4. **图像保存**:
   - 保存当前帧到 `images/known_faces/{人名}.jpg`
   - 支持中文文件名
5. **数据库重载**:
   - 重新扫描 `known_faces` 目录
   - 提取所有人脸编码
   - 更新识别数据库

**动态刷新机制**:

- **文件哈希检测**: 每 5 秒检查一次文件变化
- **自动重载**: 检测到变化后自动重新加载
- **手动刷新**: 提供 `/reload_faces` 服务接口

#### 2.5 表情控制联动

**状态判断逻辑**:

```python
if len(face_names) == 0:
    state = "no_face"           # 无人
elif "Unknown" in face_names:
    state = "has_unknown"       # 有陌生人
else:
    state = "all_known"         # 全是认识的人
```

**表情映射**:

- `all_known` → `happy` (开心)
- `has_unknown` → `surprised` (惊讶)
- `no_face` → `neutral` (中性)

**防抖机制**:

- 状态变化后等待 2 秒再切换表情
- 避免频繁切换，提升体验

### 3. 表情控制系统

#### 3.1 架构设计

**Expression Server** 是一个独立的 FastAPI HTTP 服务器，负责管理表情视频播放。

#### 3.2 技术实现

1. **视频播放线程**:
   ```python
   def play_video_continuously():
       while True:
           # 循环播放当前表情视频
           cap = cv2.VideoCapture(current_video_path)
           while not stop_event.is_set():
               ret, frame = cap.read()
               if not ret:
                   cap.set(cv2.CAP_PROP_POS_FRAMES, 0)  # 重新开始
                   continue
               cv2.imshow("PetBot 表情显示", frame)
               cv2.waitKey(int(1000/fps))
   ```

2. **表情切换机制**:
   - 接收 HTTP POST 请求: `/expression/{表情名}`
   - 设置 `stop_event` 标志，停止当前视频
   - 更新 `current_expression` 和视频路径
   - 播放线程检测到变化，自动加载新视频

3. **独立窗口显示**:
   - 使用 OpenCV 创建独立窗口
   - 全屏显示表情动画
   - 窗口可调整大小和位置

#### 3.3 HTTP API

**获取所有表情**:
```bash
GET /expressions
```

**切换表情**:
```bash
POST /expression/{表情名}
# 例如: POST /expression/happy
```

**获取当前表情**:
```bash
GET /current_expression
```

#### 3.4 表情资源

- 存储在 `nodes/expression/` 目录
- 支持 MP4 格式视频
- 18 种表情：happy, surprised, neutral, angry, sad 等

### 4. 语音交互系统

#### 4.1 ASR（语音识别）

**技术栈**:
- **VAD（语音活动检测）**: 检测是否有语音输入
- **ASR 模型**: 将语音转换为文字

**工作流程**:

1. **音频采集**: 从麦克风持续采集音频流
2. **VAD 检测**: 检测到语音活动
3. **语音识别**: 将音频片段送入 ASR 模型
4. **结果发布**: 通过 `/asr_result` 话题发布识别结果

**ROS2 话题**:
- 发布: `/asr_result` (String) - 识别到的文本

#### 4.2 TTS（语音合成）

**技术栈**:
- TTS 引擎（如 pyttsx3 或其他）

**工作流程**:

1. **接收文本**: 订阅 `/chat_response` 话题
2. **语音合成**: 将文本转换为语音
3. **音频播放**: 通过扬声器播放
4. **状态发布**: 发布播放状态到 `/tts_life` 话题

**ROS2 服务**:
- `/tts_service_wait` (SetString) - 阻塞式语音合成服务

**ROS2 话题**:
- 订阅: `/chat_response` (String) - AI 回复文本
- 发布: `/tts_life` (String) - 播放状态

### 5. 头部跟踪系统

#### 5.1 原理

**订阅人脸位置**:
- 订阅 `/face_recognition_result` 话题
- 解析 JSON 格式的人脸位置信息

**角度计算**:
```python
# 计算人脸中心相对于画面中心的角度
face_center_x = (left + right) / 2
image_center_x = frame_width / 2
angle = atan2(face_center_x - image_center_x, focal_length)
```

**舵机控制**:
- 根据计算的角度控制头部舵机
- 平滑转向，避免抖动

#### 5.2 异步控制

使用 `asyncio` 实现异步控制，不阻塞主线程。

---

## 💻 环境要求

### 系统要求

- **操作系统**: Ubuntu 20.04+ / WSL2 Ubuntu / Docker Ubuntu
- **Python**: 3.8+
- **ROS2**: Jazzy（可选，仅 body control 需要）
- **摄像头**: USB摄像头或笔记本内置摄像头
- **麦克风**: 支持音频输入设备

### 依赖包

所有依赖都包含在统一的 `requirements.txt` 文件中：

```bash
# 核心依赖（必需）
opencv-python         # 图像处理
face-recognition      # 人脸识别
numpy                 # 数值计算
langgraph             # Agent 框架
langchain-openai      # LLM 集成
langchain-core        # LangChain 核心
requests              # HTTP 请求
python-dotenv         # 环境变量管理
fastapi               # 表情服务器
uvicorn               # ASGI 服务器
Pillow                # 图像处理（中文支持）
dlib                  # 人脸识别底层库

# 可选依赖（ASR/TTS，需要 GitHub 访问）
# 如果网络不通可能安装失败，但不影响核心功能
easy-asr-server       # 语音识别
easy-tts-server       # 语音合成
ten-vad               # 语音活动检测
```

**注意：** 如果 GitHub 依赖安装失败，核心功能（人脸识别、AI对话、表情控制）仍然可用，只是语音交互功能不可用。

---

## 🚀 快速开始

### 1. 一键环境配置（推荐）

```bash
# 进入项目目录
cd /home/leoforever/wjd/Petbot

# 运行统一配置脚本（自动完成所有配置）
./setup.sh
```

**这个脚本会自动完成：**
- ✅ 检查系统依赖（Python、ROS2、cmake等）
- ✅ 创建并激活虚拟环境
- ✅ 安装所有 Python 依赖包（从 requirements.txt）
- ✅ 构建 ROS2 服务定义
- ✅ 配置 API 密钥（交互式输入）
- ✅ 创建必要的目录结构
- ✅ 生成快速环境激活脚本

### 2. 激活环境（新终端需要）

```bash
# 方法1: 使用快速激活脚本（推荐）
source activate.sh

# 方法2: 手动激活
source .venv/bin/activate
source /opt/ros/jazzy/setup.bash  # 如果使用 ROS2
source install/setup.bash          # 如果使用 ROS2
```

### 3. 配置 API 密钥

如果在 `setup.sh` 时跳过了 API 密钥配置，可以手动编辑 `.env` 文件：

```bash
# 编辑配置文件
nano .env
```

添加以下内容：

```bash
# 必需：Deepseek API Key（用于 AI 对话）
DEEPSEEK_API_KEY=sk-your-deepseek-key-here

# 可选：高德地图 API Key（用于天气查询）
AMAP_API_KEY=your-amap-key-here

# 表情映射配置
EXPRESSION_ALL_KNOWN=happy        # 认识的人 → 开心
EXPRESSION_HAS_UNKNOWN=surprised  # 陌生人 → 惊讶
EXPRESSION_NO_FACE=neutral        # 无人 → 中性
```

**获取 API 密钥：**
- Deepseek: https://platform.deepseek.com/
- 高德地图: https://lbs.amap.com/ (选择"Web服务"类型)

### 4. 启动系统

使用统一的启动脚本启动完整系统：

```bash
# 启动所有组件（默认）
./start_all.sh

# 不启动头部跟踪
./start_all.sh --no-head

# 不启动TTS（静默模式，用于测试）
./start_all.sh --no-tts

# 不启动ASR（手动输入模式）
./start_all.sh --no-asr

# 不启动表情控制
./start_all.sh --no-expression

# 组合使用
./start_all.sh --no-head --no-expression
```

**启动的组件：**
```
[1/7] 表情服务器
[2/7] 人脸识别
[3/7] 语音识别 (ASR)
[4/7] 语音合成 (TTS)
[5/7] 对话系统 (Chat Agent)
[6/7] 头部跟踪（可选）
[7/7] 交互式界面
```

**特点：**
- 🔧 功能完整，支持所有模块
- ⚙️ 灵活配置，可选择启动的组件
- 📊 详细的环境检查和状态报告
- 🎮 支持头部跟踪等高级功能

### 5. 测试功能

**测试对话（无需ROS2）：**
```bash
python3 test/test_chat_agent.py
```

**测试人脸识别：**
```bash
python3 nodes/vision/face_detection_node.py
```

---

## 📖 使用方法

### 基础对话

直接对着麦克风说话：

```
你: 你好
AI: 你好！有什么可以帮你的吗？

你: 北京天气怎么样
AI: 北京当前天气晴，气温25度，南风3级

你: 谢谢
AI: 不客气！
```

### 记住人脸

对着摄像头说：

```
你: 记住我的脸，我是张三
AI: 好的，我已经记住张三的脸了！
```

**支持的命令格式：**
- 记住我的脸，我是XXX
- 记住我的脸我是XXX
- 记住我，我是XXX
- 记住我叫XXX
- 帮我记住我，我叫XXX
- 你能记住我吗？我的名字是XXX

**注意事项：**
- 画面中只能有1张人脸
- 面对摄像头，保持正面
- 光线充足

### 表情变化

系统会自动根据识别结果改变表情：

- **无人时**: 😐 显示中性表情（neutral）
- **认识的人出现**: 😊 切换到开心表情（happy）
- **陌生人出现**: 😲 切换到惊讶表情（surprised）

### 人脸数据管理

```bash
# 查看已记住的人脸
ls -la images/known_faces/

# 删除某个人的数据
rm images/known_faces/张三.jpg

# 批量导入照片
cp ~/photos/*.jpg images/known_faces/
# 照片命名格式：人名.jpg（如：张三.jpg、李四.jpg）

# 手动刷新人脸数据库（运行时）
ros2 service call /reload_faces service_define/srv/SetString "{data: ''}"
```

### 交互式界面

启动后，您将看到类似这样的界面：

```
╔══════════════════════════════════════════════════════════╗
║              🤖 PetBot 交互式界面                        ║
╚══════════════════════════════════════════════════════════╝

============================================================
🎤 系统已就绪，请开始说话...
============================================================

[14:23:15] 👤 收到语音: 你好
[14:23:15] 🤔 AI正在思考中...
[14:23:17] 🤖 AI回复: 你好！有什么可以帮你的吗？
[14:23:17] 🔊 正在播放语音...
[14:23:20] ✅ 语音播放完成

💬 继续说话或按 Ctrl+C 退出
============================================================
```

### 查看详细日志

如果需要查看详细的系统日志（用于调试），可以打开另一个终端：

```bash
# 查看所有日志
tail -f /tmp/petbot_*.log

# 或者查看特定节点的日志
tail -f /tmp/petbot_asr.log        # 语音识别
tail -f /tmp/petbot_tts.log        # 语音合成
tail -f /tmp/petbot_chat.log       # 对话系统
tail -f /tmp/petbot_face.log       # 人脸识别
tail -f /tmp/petbot_expression.log # 表情控制
```

---

## ⚙️ 配置说明

### 配置文件说明

所有配置都可以通过 `.env` 文件或环境变量设置：

```bash
# ==========================================
# AI 对话配置
# ==========================================
DEEPSEEK_API_KEY=sk-xxx         # Deepseek API密钥（必需）
AMAP_API_KEY=xxx                # 高德地图API密钥（可选）

# ==========================================
# 表情控制配置
# ==========================================
EXPRESSION_SERVER_HOST=0.0.0.0  # 服务器地址
EXPRESSION_SERVER_PORT=8001     # 服务器端口

# 表情映射
EXPRESSION_ALL_KNOWN=happy      # 全是认识的人
EXPRESSION_HAS_UNKNOWN=surprised # 有陌生人
EXPRESSION_NO_FACE=neutral      # 无人

# 表情显示参数
EXPRESSION_DEFAULT=neutral      # 默认表情
EXPRESSION_FRAME_DELAY=0.04     # 帧延迟
EXPRESSION_VIDEO_WIDTH=1024    # 视频宽度
EXPRESSION_VIDEO_HEIGHT=600    # 视频高度
```

### 人脸识别配置

```bash
# 启动参数
python3 nodes/vision/face_detection_node.py \
    --camera_index 0 \                    # 摄像头索引
    --known_faces_dir images/known_faces \# 人脸数据库目录
    --frame_width 640 \                   # 分辨率
    --frame_height 480 \
    --publish_rate 10.0 \                 # 发布频率(Hz)
    --display_window true \               # 显示窗口
    --detection_scale 0.25 \               # 检测缩放因子
    --enable_expression true \            # 启用表情控制
    --expression_server_url http://localhost:8001
```

### 表情场景模式

在 `.env` 中选择一种场景：

**家庭模式（温馨）：**
```bash
EXPRESSION_ALL_KNOWN=happy
EXPRESSION_HAS_UNKNOWN=surprised
EXPRESSION_NO_FACE=neutral
```

**办公模式（专业）：**
```bash
EXPRESSION_ALL_KNOWN=say_hallo
EXPRESSION_HAS_UNKNOWN=neutral
EXPRESSION_NO_FACE=sleep
```

**安防模式（警惕）：**
```bash
EXPRESSION_ALL_KNOWN=neutral
EXPRESSION_HAS_UNKNOWN=angry
EXPRESSION_NO_FACE=neutral
```

---

## 🐛 故障排除

### 常见问题

#### Q1: "未找到 DEEPSEEK_API_KEY"

**解决方案：**
```bash
# 方法1: 运行配置脚本（推荐）
./setup.sh

# 方法2: 在 .env 文件中添加
echo "DEEPSEEK_API_KEY=sk-your-key" >> .env

# 方法3: 临时环境变量
export DEEPSEEK_API_KEY=sk-your-key
```

#### Q2: 摄像头无法打开

**解决方案：**
```bash
# 测试摄像头
python3 test/test_video.py

# 检查摄像头设备
ls -la /dev/video*

# 尝试不同索引
python3 nodes/vision/face_detection_node.py --camera_index 1
```

#### Q3: 表情不会改变

**解决方案：**
```bash
# 1. 检查表情服务器是否运行
ps aux | grep expression_server

# 2. 启动表情服务器
python3 nodes/expression_server.py

# 3. 测试表情服务器
curl http://localhost:8001/expressions
curl -X POST http://localhost:8001/expression/happy

# 4. 检查日志
# 应该看到 "✅ 表情服务器连接成功"
```

#### Q4: "记住我的脸"不工作

**可能原因：**
- Face Detection Node 未运行
- 画面中有多个人脸
- 没有面对摄像头

**解决方案：**
```bash
# 1. 启动 Face Detection Node
python3 nodes/vision/face_detection_node.py

# 2. 确保只有一个人在画面中
# 3. 面对摄像头，保持正面
```

#### Q5: 天气查询不工作

**解决方案：**
```bash
# 在 .env 中添加高德地图 API Key（Web服务类型）
echo "AMAP_API_KEY=your-key" >> .env

# 测试天气工具
cd nodes/chat
python3 weather_tool.py
```

#### Q6: 节点启动超时

**解决方案：**
```bash
# 查看详细日志
tail -f /tmp/petbot_*.log

# 检查是否有错误
grep -i error /tmp/petbot_*.log

# 手动测试节点
python3 nodes/asr_node.py  # 应该能看到 PETBOT_ASR_READY
```

---

## 👨‍💻 开发指南

### 添加新功能

#### 添加新的 LangGraph 工具

1. **创建工具文件**（如 `nodes/chat/new_tool.py`）:
```python
from langchain_core.tools import tool

@tool
def new_tool(param: str) -> str:
    """工具描述"""
    # 实现工具逻辑
    return result
```

2. **在 `agent.py` 中注册工具**:
```python
from new_tool import new_tool

class ChatAgent:
    def __init__(self):
        ...
        self.tools = [query_weather, remember_face, new_tool]  # 添加新工具
        self.llm_with_tools = self.llm.bind_tools(self.tools)
```

3. **更新系统提示词**（如需要）:
```python
self.system_prompt = """...
工具使用规则：
7. 当用户需要XXX时，使用 new_tool 工具
...
"""
```

#### 添加新的表情

1. **将表情视频放入 `nodes/expression/`**:
```bash
cp new_expression.mp4 nodes/expression/
```

2. **在 `expression_server.py` 中添加映射**:
```python
expressions = {
    ...
    "new_expression": f"{VIDEO_BASE_PATH}new_expression.mp4",
}
```

3. **通过 API 调用新表情**:
```bash
curl -X POST http://localhost:8001/expression/new_expression
```

### 测试

```bash
# 测试对话系统（无需ROS2）
python3 test/test_chat_agent.py

# 测试天气工具
cd nodes/chat && python3 weather_tool.py

# 测试Agent
cd nodes/chat && python3 agent.py

# 测试摄像头
python3 test/test_video.py

# 测试人脸识别
python3 test/test_face_recognition.py
```

### 性能优化

#### 人脸识别优化

```python
# 在 face_detection_node.py 中调整参数

# 提高速度（降低精度）
--detection_scale 0.15  # 更小的缩放因子
--process_every_n_frames 3  # 每3帧处理一次

# 提高精度（降低速度）
--detection_scale 0.5   # 更大的缩放因子
--process_every_n_frames 1  # 每帧都处理
```

#### LLM 优化

```python
# 在 agent.py 中调整

# 更快速的响应
temperature=0.5      # 更确定性
max_tokens=100       # 更短的回复

# 更有创造性
temperature=0.9      # 更随机
max_tokens=200       # 更长的回复
```

---

## 🔒 隐私和安全

### 数据存储

- **人脸照片**: 存储在本地 `images/known_faces/`，不会上传到云端
- **对话历史**: 仅保存在内存中，不持久化
- **API密钥**: 存储在 `.env` 文件（已添加到 .gitignore）

### 网络通信

- **表情服务器**: 默认仅监听本地（0.0.0.0:8001）
- **API调用**: 仅发送文本，不传输图像或音频
- **LLM API**: 通过 HTTPS 加密传输

### 建议

- 定期清理 `images/known_faces/` 中不需要的照片
- 不要将 `.env` 文件提交到版本控制
- 在公共网络中使用时考虑添加认证

---

## 📊 系统性能

### 资源占用

| 组件 | CPU | 内存 | 说明 |
|------|-----|------|------|
| Expression Server | 低 | ~50MB | 视频播放 |
| Face Detection | 中 | ~200MB | 人脸识别 |
| ASR Node | 高 | ~300MB | 模型加载 |
| TTS Node | 中 | ~150MB | 语音合成 |
| Chat Agent | 低 | ~100MB | LLM调用 |
| **总计** | **中-高** | **~800MB** | |

### 响应时间

| 操作 | 响应时间 | 说明 |
|------|---------|------|
| 语音识别 | 0.5-2秒 | 取决于语音长度 |
| AI 对话 | 1-3秒 | 取决于LLM响应 |
| 人脸识别 | 实时 | 10-30 FPS |
| 表情切换 | <0.1秒 | 即时响应 |
| 头部跟踪 | 实时 | 平滑跟随 |

---

## 📝 更新日志

### v2.0.0 (2025-12-17)
- ✅ 升级到 LangGraph Agent
- ✅ 添加天气查询工具
- ✅ 实现"记住我的脸"功能（LLM工具方式）
- ✅ 添加智能表情控制
- ✅ 实现人脸数据库动态刷新
- ✅ 完善文档和启动脚本
- ✅ 添加 READY Flag 启动检测系统
- ✅ 优化交互式界面

### v1.0.0
- 基础语音交互
- 简单人脸识别
- 表情显示

---

## 📚 相关资源

- **LangGraph**: https://langchain-ai.github.io/langgraph/
- **Deepseek API**: https://platform.deepseek.com/docs
- **face_recognition**: https://face-recognition.readthedocs.io/
- **高德地图API**: https://lbs.amap.com/
- **ROS2**: https://docs.ros.org/en/jazzy/

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

## 📄 许可证

[根据你的项目选择合适的许可证]

---

<div align="center">

**Petbot - 让机器人更智能、更有情感** 🤖✨

Made with ❤️

</div>
