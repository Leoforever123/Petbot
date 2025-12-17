# 项目结构重组完成

## 📋 完成的更改

### 1. 文件重新组织

#### 从 demo/ 移动到 nodes/
- ✅ `demo/echo_node.py` → `nodes/echo_node.py`
- ✅ `demo/chat_node.py` → `nodes/chat_node.py`

#### 从 demo/ 移动到 launch/
- ✅ `demo/start_echo_system.sh` → `launch/start_echo_system.sh`
- ✅ `demo/start_chat_system.sh` → `launch/start_chat_system.sh`

#### 新创建的文件
- ✅ `nodes/vision/face_detection_node.py` - 人脸检测节点（使用face_recognition库）
- ✅ `launch/start_face_tracking.sh` - 人脸跟踪系统启动脚本
- ✅ `nodes/vision/README_face_detection.md` - 详细使用文档
- ✅ `launch/README.md` - 启动脚本总览文档

### 2. 更新的文件

#### 启动脚本路径更新
- ✅ `launch/start_chat_system.sh` - 更新chat_node.py路径为 `../nodes/chat_node.py`
- ✅ `launch/start_echo_system.sh` - 更新echo_node.py路径为 `../nodes/echo_node.py`

#### 添加执行权限
- ✅ `launch/start_face_tracking.sh`
- ✅ `launch/start_chat_system.sh`
- ✅ `launch/start_echo_system.sh`

### 3. 删除的文件
- ✅ `launch/face_detection.launch.py` - 删除Python launch文件，改用bash脚本

---

## 📂 新的文件结构

```
Petbot/
├── launch/                          # 所有启动脚本统一放这里
│   ├── README.md                    # 启动脚本总览和使用说明
│   ├── start_face_tracking.sh       # 人脸跟踪系统（NEW）
│   ├── start_echo_system.sh         # 语音回声系统
│   └── start_chat_system.sh         # AI对话系统
│
├── nodes/                           # 所有节点文件统一放这里
│   ├── vision/
│   │   ├── face_detection_node.py   # 人脸检测节点（NEW）
│   │   └── README_face_detection.md # 详细文档（NEW）
│   ├── body_control/
│   │   ├── turn_head.py             # 头部跟随控制
│   │   └── turn_head copy.py
│   ├── asr_node.py                  # 语音识别
│   ├── tts_node.py                  # 语音合成
│   ├── echo_node.py                 # 回声节点（MOVED）
│   ├── chat_node.py                 # AI对话节点（MOVED）
│   └── ...
│
└── demo/                            # 现在为空（文件已全部移出）
```

---

## 🚀 快速开始

### 人脸跟踪系统（新功能）

```bash
cd /home/leoforever/wjd/Petbot/launch
./start_face_tracking.sh
```

**功能**：
- 实时检测人脸并在屏幕上显示方框
- 机器人头部自动跟随人脸移动
- 支持多参数配置（摄像头、分辨率、帧率等）

**自定义配置**：
```bash
CAMERA_INDEX=1 PUBLISH_RATE=15 ./start_face_tracking.sh
```

### 语音回声系统

```bash
cd /home/leoforever/wjd/Petbot/launch
./start_echo_system.sh
```

### AI对话系统

```bash
export DEEPSEEK_API_KEY='your-key-here'
cd /home/leoforever/wjd/Petbot/launch
./start_chat_system.sh
```

---

## 🎯 核心功能

### face_detection_node.py 特性

1. **使用face_recognition库进行人脸检测**
   - 高精度人脸识别
   - 支持多人脸同时检测
   - 可配置检测精度和速度平衡

2. **实时可视化**
   - 绿色方框标记人脸
   - 红色圆点显示人脸中心
   - 蓝色十字显示图像中心（对齐参考）
   - 显示人脸编号和坐标信息

3. **ROS2集成**
   - 发布到 `/face_recognition_result` 话题
   - JSON格式数据与现有body控制节点兼容
   - 支持ROS2参数和命令行参数两种配置方式

4. **性能优化**
   - 图像缩放降低计算量
   - 跳帧处理提高帧率
   - 可配置的检测频率

### 数据格式（与turn_head.py兼容）

```json
[
    {
        "location": [top, left, bottom, right],
        "center": [center_x, center_y],
        "width": width,
        "height": height
    }
]
```

---

## 📖 文档

### 详细文档位置

- **人脸检测系统**：`nodes/vision/README_face_detection.md`
- **启动脚本说明**：`launch/README.md`
- **本次更改说明**：本文件

### 话题说明

| 话题名 | 消息类型 | 说明 |
|--------|----------|------|
| `/face_recognition_result` | String | 人脸检测结果（JSON） |
| `/asr_result` | String | 语音识别结果 |
| `/ai_thinking` | String | AI思考状态信号 |
| `tts_service_wait` | SetString | TTS服务（阻塞式） |

---

## ⚙️ 配置说明

### 人脸跟踪系统环境变量

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `CAMERA_INDEX` | 0 | 摄像头索引 |
| `FRAME_WIDTH` | 640 | 图像宽度 |
| `FRAME_HEIGHT` | 480 | 图像高度 |
| `PUBLISH_RATE` | 10 | 发布频率(Hz) |
| `DISPLAY_WINDOW` | true | 是否显示窗口 |
| `DETECTION_SCALE` | 0.25 | 检测缩放因子 |

### 示例用法

```bash
# 使用高帧率和高精度
PUBLISH_RATE=20 DETECTION_SCALE=0.5 ./start_face_tracking.sh

# 无头模式运行（服务器环境）
DISPLAY_WINDOW=false ./start_face_tracking.sh

# 使用外接USB摄像头
CAMERA_INDEX=1 ./start_face_tracking.sh
```

---

## 🔧 依赖安装

### 人脸检测依赖

```bash
# 系统依赖
sudo apt-get install -y build-essential cmake libopenblas-dev liblapack-dev libx11-dev libgtk-3-dev

# Python依赖
pip install face_recognition opencv-python
```

### 其他依赖（如已安装可跳过）

```bash
# ROS2相关
# (根据实际ROS2发行版安装)

# Python包
pip install openai python-dotenv rclpy std_msgs
```

---

## ✅ 测试建议

### 1. 测试人脸检测节点

```bash
# 启动节点
cd /home/leoforever/wjd/Petbot
python3 nodes/vision/face_detection_node.py

# 另一个终端查看发布的数据
ros2 topic echo /face_recognition_result
```

### 2. 测试完整系统

```bash
cd launch
./start_face_tracking.sh
```

应该看到：
- 摄像头窗口显示实时画面
- 人脸被绿色方框标记
- 机器人头部跟随人脸移动

### 3. 检查节点状态

```bash
# 查看所有节点
ros2 node list

# 查看所有话题
ros2 topic list

# 查看特定话题
ros2 topic info /face_recognition_result
```

---

## 🐛 常见问题

### Q: 摄像头无法打开

**A:** 检查摄像头索引

```bash
ls /dev/video*
CAMERA_INDEX=1 ./start_face_tracking.sh
```

### Q: 检测速度慢

**A:** 降低检测精度

```bash
DETECTION_SCALE=0.1 ./start_face_tracking.sh
```

### Q: 检测不到人脸

**A:** 提高检测精度

```bash
DETECTION_SCALE=0.5 ./start_face_tracking.sh
```

### Q: face_recognition库安装失败

**A:** 先安装系统依赖

```bash
sudo apt-get install build-essential cmake libopenblas-dev liblapack-dev
pip install face_recognition
```

---

## 📝 后续建议

1. **性能优化**：
   - 如有NVIDIA GPU，可以使用CNN模型（修改代码中的`model='hog'`为`model='cnn'`）
   - 调整跳帧参数提高帧率

2. **功能扩展**：
   - 添加人脸识别功能（识别特定人物）
   - 添加表情检测
   - 记录人脸轨迹

3. **集成改进**：
   - 添加人脸丢失时的默认行为
   - 添加多人脸时的优先级选择逻辑

---

## 📄 许可证

根据项目许可证使用。

---

**更新日期**: 2025-12-17
**作者**: AI Assistant
**版本**: 1.0.0

