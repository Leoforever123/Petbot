# 人脸跟踪系统修复说明

## 🐛 发现的问题

**错误信息**: `no module body_controller_can`

**原因分析**：
- `turn_head.py` 文件中导入了 `from body_controller_can import global_body_controller`
- 但项目中只有 `body_controller.py`，不存在 `body_controller_can.py`
- 导致启动脚本运行失败

## ✅ 解决方案

### 修复内容

1. **修复了 `turn_head.py` 的导入**
   ```python
   # 修改前（错误）
   from body_controller_can import global_body_controller
   
   # 修改后（正确）
   from body_controller import global_body_controller
   ```

2. **创建了三个版本的启动脚本**，适应不同使用场景

## 🚀 现在可用的启动选项

### 选项1：基础版（推荐初学者）⭐

**文件**: `launch/start_face_tracking.sh`

**特点**：最简单，只关注人脸跟踪

```bash
cd /home/leoforever/wjd/Petbot/launch
./start_face_tracking.sh
```

**启动的节点**：
- ✅ Face Detection Node (`face_detection_node.py`)
- ✅ Turn Head Node (`turn_head copy.py`) - 简化版，只做人脸跟踪

**适用场景**：
- 只需要机器人跟随人脸
- 简单测试
- 学习基础功能

---

### 选项2：完整版（功能分离）

**文件**: `launch/start_face_tracking_full.sh`

**特点**：功能完整，节点分离，易于调试

```bash
cd /home/leoforever/wjd/Petbot/launch
./start_face_tracking_full.sh
```

**启动的节点**：
- ✅ Face Detection Node (`face_detection_node.py`)
- ✅ Turn Head Node (`turn_head copy.py`) - 人脸跟踪
- ✅ Gesture Node (`gestures_node.py`) - 手势控制

**适用场景**：
- 需要人脸跟踪 + 手势控制
- 希望功能模块分离
- 方便调试单个功能

**可用功能**：
- 人脸跟踪（自动）
- 发送手势命令到 `/gesture` 话题

---

### 选项3：集成版（一体化）

**文件**: `launch/start_face_tracking_integrated.sh`

**特点**：一个节点处理所有功能

```bash
cd /home/leoforever/wjd/Petbot/launch
./start_face_tracking_integrated.sh
```

**启动的节点**：
- ✅ Face Detection Node (`face_detection_node.py`)
- ✅ Integrated Turn Head Node (`turn_head.py`) - 集成版

**适用场景**：
- 需要完整功能
- 减少节点数量
- 生产环境

**可用功能**：
- 人脸跟踪（通过 `/face_recognition_result`）
- 手势控制（通过 `/gesture`）
- 转头指令（通过 `/turn_head_instruction`）

## 📊 节点对比

| 节点文件 | 导入模块 | 订阅话题 | 功能 | 状态 |
|---------|---------|---------|------|------|
| `turn_head copy.py` | `body_controller` ✅ | `face_recognition_result` | 人脸跟踪 | 可用 |
| `turn_head.py` | ~~`body_controller_can`~~ → `body_controller` ✅ | `face_recognition_result`<br>`gesture`<br>`turn_head_instruction` | 集成多功能 | 已修复 |
| `gestures_node.py` | `body_controller` ✅ | `gesture` | 手势控制 | 可用 |

## 🎯 推荐使用方式

### 场景1：快速测试人脸跟踪
```bash
./start_face_tracking.sh
```

### 场景2：需要手势控制
```bash
# 方式A：分离式（推荐调试）
./start_face_tracking_full.sh

# 方式B：集成式（推荐生产）
./start_face_tracking_integrated.sh
```

## 📝 配置参数

所有启动脚本都支持相同的环境变量：

```bash
# 使用不同摄像头
CAMERA_INDEX=1 ./start_face_tracking.sh

# 调整分辨率和帧率
FRAME_WIDTH=1280 FRAME_HEIGHT=720 PUBLISH_RATE=15 ./start_face_tracking.sh

# 调整检测精度和速度
DETECTION_SCALE=0.5 ./start_face_tracking.sh  # 高精度
DETECTION_SCALE=0.1 ./start_face_tracking.sh  # 高速度

# 无头模式（不显示窗口）
DISPLAY_WINDOW=false ./start_face_tracking.sh

# 组合使用
CAMERA_INDEX=1 PUBLISH_RATE=20 DETECTION_SCALE=0.3 ./start_face_tracking_full.sh
```

## 🔍 测试验证

### 1. 测试人脸检测数据发布

```bash
# 启动系统后，在另一个终端运行：
ros2 topic echo /face_recognition_result
```

### 2. 测试手势控制（仅完整版和集成版）

```bash
# 发送手势命令
ros2 topic pub /gesture std_msgs/String "data: 'wave_right_hand'"

# 带参数的手势
ros2 topic pub /gesture std_msgs/String "data: 'head_left(30)'"
```

### 3. 测试转头指令（仅集成版）

```bash
ros2 topic pub /turn_head_instruction std_msgs/Float32 "data: 45.0"
```

## 📂 修改的文件

### 新增文件
- ✅ `launch/start_face_tracking_full.sh` - 完整版启动脚本
- ✅ `launch/start_face_tracking_integrated.sh` - 集成版启动脚本

### 修改文件
- ✅ `nodes/body_control/turn_head.py` - 修复导入错误
- ✅ `launch/start_face_tracking.sh` - 改用 `turn_head copy.py`
- ✅ `launch/README.md` - 更新文档

### 文件权限
```bash
# 所有启动脚本已添加执行权限
chmod +x launch/*.sh
```

## 🔧 故障排除

### Q: 仍然报错 "no module body_controller"

**A**: 确保在正确的目录运行，或设置PYTHONPATH：

```bash
cd /home/leoforever/wjd/Petbot
export PYTHONPATH=$PYTHONPATH:/home/leoforever/wjd/Petbot/nodes/body_control
./launch/start_face_tracking.sh
```

### Q: LifecycleNode 相关错误

**A**: `turn_head.py` 和 `turn_head copy.py` 使用 LifecycleNode，可能需要手动激活：

```bash
# 在另一个终端
ros2 lifecycle set /turn_head configure
ros2 lifecycle set /turn_head activate
```

### Q: 想切换回原来的节点

**A**: 编辑启动脚本，替换节点路径即可。

## 📖 相关文档

- **人脸检测详细说明**: `nodes/vision/README_face_detection.md`
- **启动脚本总览**: `launch/README.md`
- **项目结构变更**: `CHANGES.md`

## ✨ 下一步建议

1. **测试所有三个版本**，选择最适合你的
2. **根据机器人硬件调整参数**（摄像头索引、分辨率等）
3. **如需自定义功能**，可以基于这些节点进行修改
4. **性能调优**：调整 `DETECTION_SCALE` 和 `PUBLISH_RATE`

---

**修复日期**: 2025-12-17  
**问题**: ModuleNotFoundError: No module named 'body_controller_can'  
**状态**: ✅ 已解决

