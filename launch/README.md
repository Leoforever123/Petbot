# 启动脚本说明

本文件夹包含所有系统的启动脚本。所有脚本均为bash格式，可直接执行。

## 可用启动脚本

### 1. 人脸跟踪系统 🤖

人脸跟踪系统提供**三个版本**，根据需求选择：

#### 1a. 基础版（推荐新手）

**`start_face_tracking.sh`**

最简单的人脸跟踪，只关注人脸跟随功能。

```bash
./start_face_tracking.sh
```

**包含的节点**：
- Face Detection Node - 使用face_recognition库检测人脸
- Turn Head Node (Simple) - 控制机器人头部跟随人脸

#### 1b. 完整版（分离式）

**`start_face_tracking_full.sh`**

人脸跟踪 + 独立的手势控制节点，功能分离更清晰。

```bash
./start_face_tracking_full.sh
```

**包含的节点**：
- Face Detection Node - 人脸检测
- Turn Head Node (Simple) - 人脸跟踪
- Gesture Node - 手势控制（订阅 `/gesture` 话题）

#### 1c. 集成版（一体化）

**`start_face_tracking_integrated.sh`**

使用集成节点，一个节点处理多种功能。

```bash
./start_face_tracking_integrated.sh
```

**包含的节点**：
- Face Detection Node - 人脸检测
- Integrated Turn Head Node - 集成人脸跟踪、手势控制、转头指令

**订阅的话题**：
- `/face_recognition_result` - 人脸数据
- `/gesture` - 手势命令
- `/turn_head_instruction` - 转头指令

#### 环境变量配置（适用于所有版本）

```bash
CAMERA_INDEX=0 PUBLISH_RATE=15 ./start_face_tracking.sh
```

**详细文档**：参见 `nodes/vision/README_face_detection.md`

---

### 2. 语音回声系统 🔊

**`start_echo_system.sh`**

启动语音回声系统，将你说的话重复播放出来。

```bash
./start_echo_system.sh
```

**包含的节点**：
- ASR Node - 语音识别
- TTS Node - 语音合成
- Echo Node - 桥接ASR和TTS

---

### 3. AI对话系统 💬

**`start_chat_system.sh`**

启动AI对话系统，使用Deepseek LLM进行智能对话。

```bash
./start_chat_system.sh
```

**包含的节点**：
- ASR Node - 语音识别
- TTS Node - 语音合成
- Chat Node - AI对话（Deepseek）

**前置要求**：需要设置 `DEEPSEEK_API_KEY` 环境变量

```bash
export DEEPSEEK_API_KEY='sk-your-key-here'
./start_chat_system.sh
```

或在项目根目录创建 `.env` 文件：
```
DEEPSEEK_API_KEY=sk-your-key-here
```

---

## 通用使用说明

### 添加执行权限

如果脚本无法执行，需要添加执行权限：

```bash
chmod +x *.sh
```

### 停止系统

所有脚本都支持 `Ctrl+C` 优雅退出，会自动停止所有相关节点。

### 检查运行状态

启动后会显示所有节点的PID（进程ID），可以用于监控：

```bash
# 查看进程是否运行
ps aux | grep python3

# 查看ROS2话题
ros2 topic list

# 监听话题数据
ros2 topic echo /topic_name
```

### 日志输出

所有节点的日志会直接输出到终端。如需保存日志：

```bash
./start_face_tracking.sh 2>&1 | tee face_tracking.log
```

---

## 开发提示

### 添加新的启动脚本

参考现有脚本的格式：

1. **头部声明**：`#!/bin/bash`
2. **脚本目录定位**：`SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"`
3. **环境配置**：Source ROS2环境和虚拟环境
4. **参数配置**：使用环境变量或命令行参数
5. **启动节点**：使用后台运行并保存PID
6. **信号处理**：使用trap捕获Ctrl+C并清理进程

### 调试技巧

**单独运行节点**：
```bash
cd /home/leoforever/wjd/Petbot
python3 nodes/节点名.py
```

**检查依赖**：
```bash
# 检查Python包
python3 -c "import face_recognition; print('OK')"

# 检查ROS2话题
ros2 topic list
ros2 topic info /topic_name
```

**查看节点信息**：
```bash
ros2 node list
ros2 node info /node_name
```

---

## 文件结构

```
launch/
├── README.md                    # 本文件
├── start_face_tracking.sh       # 人脸跟踪系统
├── start_echo_system.sh         # 语音回声系统
└── start_chat_system.sh         # AI对话系统

nodes/
├── vision/
│   ├── face_detection_node.py   # 人脸检测节点
│   └── README_face_detection.md # 详细文档
├── body_control/
│   ├── turn_head.py             # 头部控制节点
│   └── turn_head copy.py
├── asr_node.py                  # 语音识别节点
├── tts_node.py                  # 语音合成节点
├── echo_node.py                 # 回声节点
└── chat_node.py                 # AI对话节点
```

---

## 许可证

根据项目许可证使用。

