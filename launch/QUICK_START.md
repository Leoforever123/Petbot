# 🚀 快速启动指南

## 人脸跟踪系统 - 三选一

### 🟢 选项1：基础版（推荐新手）
```bash
cd /home/leoforever/wjd/Petbot/launch
./start_face_tracking.sh
```
**功能**: 只做人脸跟踪  
**节点**: 2个（检测 + 跟踪）

---

### 🔵 选项2：完整版（功能分离）
```bash
cd /home/leoforever/wjd/Petbot/launch
./start_face_tracking_full.sh
```
**功能**: 人脸跟踪 + 手势控制  
**节点**: 3个（检测 + 跟踪 + 手势）

---

### 🟣 选项3：集成版（一体化）
```bash
cd /home/leoforever/wjd/Petbot/launch
./start_face_tracking_integrated.sh
```
**功能**: 人脸跟踪 + 手势 + 转头指令  
**节点**: 2个（检测 + 集成控制）

---

## 其他系统

### 🔊 语音回声
```bash
./start_echo_system.sh
```

### 💬 AI对话
```bash
export DEEPSEEK_API_KEY='your-key'
./start_chat_system.sh
```

---

## ⚙️ 快速配置

```bash
# 使用外接摄像头
CAMERA_INDEX=1 ./start_face_tracking.sh

# 高帧率模式
PUBLISH_RATE=20 ./start_face_tracking.sh

# 高精度模式（慢）
DETECTION_SCALE=0.5 ./start_face_tracking.sh

# 高速模式（低精度）
DETECTION_SCALE=0.1 ./start_face_tracking.sh

# 无头模式
DISPLAY_WINDOW=false ./start_face_tracking.sh
```

---

## 🛑 停止系统

所有脚本：按 `Ctrl+C` 停止

---

**需要帮助？** 查看 `launch/README.md` 或 `FACE_TRACKING_FIX.md`

