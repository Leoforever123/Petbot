# 人脸识别测试程序使用指南

## 📋 目录
1. [环境配置](#环境配置)
2. [准备已知人脸图片](#准备已知人脸图片)
3. [运行程序](#运行程序)
4. [功能说明](#功能说明)
5. [常见问题](#常见问题)

---

## 🔧 环境配置

### 步骤 1: 激活虚拟环境

```bash
cd /home/leoforever/wjd/Petbot
source .venv/bin/activate
```

### 步骤 2: 安装系统依赖

在安装 Python 包之前，需要先安装一些系统级依赖：

```bash
# 安装编译工具和依赖库
sudo apt update
sudo apt install -y build-essential cmake pkg-config
sudo apt install -y libx11-dev libatlas-base-dev
sudo apt install -y libgtk-3-dev libboost-python-dev
```

### 步骤 3: 安装 Python 依赖

```bash
# 升级 pip
pip install --upgrade pip

# 安装依赖（这一步可能需要 5-10 分钟，dlib 编译较慢）
pip install face-recognition dlib cmake

# 或者从 requirements.txt 安装所有依赖
pip install -r requirements.txt
```

**注意**：
- `dlib` 的安装可能需要较长时间（5-15分钟），因为需要编译
- 如果安装失败，可能需要安装更多系统依赖
- 在虚拟机中编译可能会比较慢，请耐心等待

---

## 📸 准备已知人脸图片

### 步骤 1: 准备照片文件

将需要识别的人物照片放入以下目录：

```bash
/home/leoforever/wjd/Petbot/images/known_faces/
```

### 步骤 2: 照片命名规则

**文件名即为识别时显示的名字**

示例：
- `张三.jpg` → 识别时显示 "张三"
- `李四.png` → 识别时显示 "李四"
- `wang_wu.jpeg` → 识别时显示 "wang_wu"

### 步骤 3: 照片要求

✅ **好的照片**：
- 清晰的正面照
- 光线充足
- 人脸占据图片较大比例
- 单人照片（首选）

❌ **不好的照片**：
- 模糊不清
- 侧脸或低头
- 戴口罩、墨镜
- 光线太暗

### 示例文件结构

```
images/known_faces/
├── 张三.jpg
├── 李四.png
├── 王五.jpeg
└── README.md
```

---

## 🚀 运行程序

### 快速开始

```bash
cd /home/leoforever/wjd/Petbot
source .venv/bin/activate
cd test
python3 test_face_recognition.py
```

### 程序菜单

运行后会看到以下菜单：

```
============================================================
请选择功能:
  1. 从摄像头识别人脸 (实时)
  2. 从视频文件识别人脸
  3. 从图片文件识别人脸
  4. 重新加载已知人脸数据
  0. 退出
============================================================
```

---

## 📖 功能说明

### 功能 1: 从摄像头识别人脸（实时）

- **用途**：实时识别摄像头中的人脸
- **操作**：
  - 选择选项 `1`
  - 程序会打开默认摄像头
  - 实时显示识别结果
- **控制**：
  - 按 `q` 键退出
  - 按 `s` 键保存当前截图

**注意**：如果没有摄像头，会显示错误提示

### 功能 2: 从视频文件识别人脸

- **用途**：识别视频文件中的人脸
- **操作**：
  - 选择选项 `2`
  - 输入视频文件路径（如：`/home/user/video.mp4`）
  - 程序会逐帧处理并显示结果
- **控制**：
  - 按 `q` 键退出
  - 按 `s` 键保存当前截图

### 功能 3: 从图片文件识别人脸

- **用途**：识别单张图片中的人脸
- **操作**：
  - 选择选项 `3`
  - 输入图片文件路径（如：`/home/user/photo.jpg`）
  - 程序会处理并显示结果
  - 按任意键关闭结果窗口
- **输出**：会在原图片同目录生成 `*_result.jpg` 文件

### 功能 4: 重新加载已知人脸数据

- **用途**：添加新的已知人脸照片后，无需重启程序即可重新加载
- **操作**：
  - 添加新照片到 `images/known_faces/` 目录
  - 选择选项 `4`
  - 程序会重新扫描并加载所有照片

---

## 🔍 代码中的关键函数说明

### face_recognition 库主要函数：

1. **`face_recognition.load_image_file(path)`**
   - 加载图片文件
   - 返回 numpy 数组（RGB 格式）

2. **`face_recognition.face_locations(image, model="hog")`**
   - 检测图片中所有人脸的位置
   - 返回：`[(top, right, bottom, left), ...]`
   - model 参数：
     - `"hog"`: 较快，CPU 友好（推荐）
     - `"cnn"`: 更准确，需要 GPU

3. **`face_recognition.face_encodings(image, known_face_locations)`**
   - 获取人脸的 128 维特征编码
   - 这是识别的核心：将人脸转换为数字向量

4. **`face_recognition.compare_faces(known_encodings, face_encoding, tolerance=0.6)`**
   - 比较人脸编码
   - 返回布尔值列表，表示是否匹配
   - tolerance 参数：
     - 越小越严格（0.4-0.6 之间较合适）
     - 默认 0.6

5. **`face_recognition.face_distance(known_encodings, face_encoding)`**
   - 计算人脸之间的距离（欧氏距离）
   - 距离越小表示越相似
   - 配合 compare_faces 使用，找到最佳匹配

### OpenCV 相关函数：

1. **`cv2.VideoCapture(source)`**
   - 打开视频源
   - source=0: 默认摄像头
   - source="path": 视频文件

2. **`cv2.rectangle(image, pt1, pt2, color, thickness)`**
   - 绘制矩形框

3. **`cv2.putText(image, text, position, font, size, color, thickness)`**
   - 在图像上绘制文字

---

## ❓ 常见问题

### Q1: dlib 安装失败怎么办？

**方案 1**: 安装预编译版本
```bash
pip install dlib --no-cache-dir
```

**方案 2**: 安装系统依赖后重试
```bash
sudo apt install -y build-essential cmake
sudo apt install -y libopenblas-dev liblapack-dev
pip install dlib
```

**方案 3**: 使用清华镜像源
```bash
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple dlib
```

### Q2: 提示找不到摄像头？

这是因为 VMware 虚拟机中没有摄像头设备。解决方案：

1. **使用视频文件测试**（推荐）
   - 下载或准备一个测试视频
   - 选择功能 2，输入视频文件路径

2. **使用图片测试**
   - 准备一些包含人脸的照片
   - 选择功能 3，输入图片路径

3. **配置 VMware 摄像头**（参考之前的讨论）

### Q3: 识别准确率不高？

**改进建议**：

1. **提高照片质量**
   - 使用高清、正面、光线好的照片
   - 每个人准备 2-3 张不同角度的照片

2. **调整 tolerance 参数**
   - 在代码第 154 行修改：
   ```python
   matches = face_recognition.compare_faces(
       self.known_face_encodings, 
       face_encoding,
       tolerance=0.5  # 改小更严格，改大更宽松
   )
   ```

3. **使用 CNN 模型**（需要更多计算资源）
   - 在代码第 144 行修改：
   ```python
   face_locations = face_recognition.face_locations(rgb_small_frame, model="cnn")
   ```

### Q4: 程序运行很慢？

**优化建议**：

1. **降低处理频率**
   - 代码第 251 行已设置为每隔一帧处理
   - 可以改为每隔 3 帧：`if frame_count % 3 == 0:`

2. **降低图像分辨率**
   - 代码第 133 行已缩小到 1/4
   - 可以改为 1/8：`fx=0.125, fy=0.125`

3. **减少已知人脸数量**
   - 仅保留需要识别的人脸照片

### Q5: 中文名字显示乱码？

确保：
1. 图片文件名使用 UTF-8 编码
2. 终端支持中文显示
3. 如果还是乱码，建议使用英文或拼音命名

---

## 📝 测试建议

### 第一次运行测试流程：

1. **不添加任何已知人脸照片**
   - 直接运行程序
   - 测试人脸检测功能（会标记为 "Unknown"）
   - 验证程序是否正常工作

2. **添加一张自己的照片**
   - 命名为 `test.jpg`
   - 选择功能 4 重新加载
   - 选择功能 3，测试同一张照片识别

3. **测试实时识别**（如果有摄像头或视频）
   - 选择功能 1 或 2
   - 观察识别效果

---

## 🎯 下一步

程序可以继续扩展：

1. **保存识别记录**
   - 记录识别到的人物和时间
   - 保存到数据库或日志文件

2. **人脸注册功能**
   - 通过摄像头直接注册新人脸
   - 无需手动添加照片文件

3. **多线程处理**
   - 分离识别和显示线程
   - 提高实时性能

4. **集成到 ROS 系统**
   - 创建 ROS 节点
   - 发布识别结果到话题

---

祝使用愉快！ 🎉

