考虑到我这次基本算是从零开始配环境而其他同学可能已经或多或少配置了一些环境，为了防止大家因为环境原因跑不了我的代码，我就把从配置ros2环境的步骤也写进去...

**基本环境**
mac m1芯片 arm64架构上起的原生Ubuntu24.04 docker容器

**根据教程一步步安装ros2的环境**
参考[助教给的Ubuntu配置环境官方教程](https://docs.ros.org/en/jazzy/Installation/Ubuntu-Install-Debs.html)

注意：执行`export ROS_APT_SOURCE_VERSION=$(curl -s https://api.github.com/repos/ros-infrastructure/ros-apt-source/releases/latest | grep -F "tag_name" | awk -F\" '{print $4}')`的时候可能实际上并没有返回版本号，你最好执行一下`echo $ROS_APT_SOURCE_VERSION`来确认一下是否拿到了正确的版本号，如果没有的话你在本机上再次执行以上两个命令后，在docker容器中export即可

---
现在开始进入容器


**安装必要工具**
```bash
apt-get update
apt-get install -y \
  git \
  python3-pip \
  python3-colcon-common-extensions \
  build-essential \
  cmake

apt-get update
apt-get install -y \
  ros-jazzy-cv-bridge \
  ros-jazzy-image-transport \
  ros-jazzy-message-filters

apt-get install -y software-properties-common

# 添加 RealSense apt 源
apt-key adv --keyserver keyserver.ubuntu.com --recv-key F6B0FC61 || true
add-apt-repository "deb http://realsense-hw-public.s3.amazonaws.com/Debian/apt-repo focal main"

apt-get update
apt-get install -y \
  librealsense2-utils \
  librealsense2-dev \
  librealsense2-dbg


# 我在执行这些指令的时候好像是报了错，具体原因是Intel 官方的 librealsense apt 仓库已经基本废了 / 禁用了，在 Ubuntu 24.04（noble）下用 focal 源直接 403，所以 apt 装不了 librealsense2-*，然后直接执行了下面这个就可以了，大家看看是不是会和我遇到一样的问题，
apt-get install -y \
  ros-jazzy-cv-bridge \
  ros-jazzy-image-transport \
  ros-jazzy-message-filters \
  libssl-dev \
  libusb-1.0-0-dev \
  pkg-config \
  libgtk-3-dev \
  libglfw3-dev \
  libgl1-mesa-dev \
  libglu1-mesa-dev \
  python3-colcon-common-extensions \
  build-essential cmake git
```




**建立ros2工作空间**
```bash
# 1. 创建工作空间
mkdir -p ~/workspace/ros2_ws/src
cd ~/workspace/ros2_ws/src

# 2. 拉取 intel 仓库代码
git clone https://github.com/intel/ros2_intel_realsense.git

# 3. 编译
source /opt/ros/jazzy/setup.bash
cd /workspace/ros2_ws
colcon build --packages-select realsense_camera_msgs realsense_ros2_camera
```

到此为止基本上成功了
注意以后打开任何一个终端想要使用ros2的时候都需要执行
```bash
source /opt/ros/jazzy/setup.bash
source /workspace/ros2_ws/install/local_setup.bash

# 或者用下面这段命令直接追加到 ~/.bashrc，省得每次手打
echo "source /opt/ros/jazzy/setup.bash" >> ~/.bashrc
echo "source /workspace/ros2_ws/install/local_setup.bash" >> ~/.bashrc
```

**尝试跑起来**
```bash
source /opt/ros/jazzy/setup.bash
source /workspace/ros2_ws/install/local_setup.bash

ros2 run realsense_ros2_camera realsense_ros2_camera
# 如果没接 RealSense 相机：节点可能启动后报“没发现设备”，这是正常的，说明环境和代码都工作了
```

**创建虚拟相机节点**
```bash
cd /workspace/ros2_ws/src
# 创建一个 Python 包 virtual_realsense_camera
ros2 pkg create virtual_realsense_camera --build-type ament_python
cd /workspace/ros2_ws/src/virtual_realsense_camera/virtual_realsense_camera
# 直接在该目录下创建.py脚本
...
# 编辑setup.py
# 只需要在entry_points 里加入这些行
entry_points={
    'console_scripts': [
        'virtual_camera_node = virtual_realsense_camera.virtual_camera_node:main',
        'virtual_color_camera_node = virtual_realsense_camera.virtual_color_camera_node:main',
        'virtual_depth_camera_node = virtual_realsense_camera.virtual_depth_camera_node:main',
        'rgbd_image_saver = virtual_realsense_camera.image_saver_node:main',
        'http_camera_bridge = virtual_realsense_camera.http_camera_bridge_node:main',
    ],
}

# 编译virtual_realsense_camera
source /opt/ros/jazzy/setup.bash
colcon build --packages-select virtual_realsense_camera
source install/local_setup.bash

# 运行刚刚的节点
ros2 run virtual_realsense_camera virtual_camera_node #虚拟相机节点（最基础）
ros2 run virtual_realsense_camera virtual_color_camera_node # rgb节点
ros2 run virtual_realsense_camera virtual_depth_camera_node # depth节点
ros2 run virtual_realsense_camera rgbd_image_saver # RGBD 图像保存节点，用于接收前俩节点生成的fake图片数据
ros2 run virtual_realsense_camera http_camera_bridge # HTTP → ROS 桥接节点（从 HTTP 摄像头流转成 ROS 图像）（需配合docker外主机的代码）
```

**额外一些工作**
mac的docker-desktop不支持直接获取硬件摄像头的数据，但是用http转发到docker容器里现在可以了接收到了

