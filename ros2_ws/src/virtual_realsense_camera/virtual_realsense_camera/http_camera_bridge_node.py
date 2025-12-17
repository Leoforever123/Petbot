#!/usr/bin/env python3
import os
import time
from datetime import datetime

import cv2
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge


class HTTPCameraBridge(Node):
    def __init__(self):
        super().__init__('http_camera_bridge')

        self.bridge = CvBridge()

        # 输出话题：标准彩色图像
        self.pub = self.create_publisher(Image, '/camera/color/image_raw', 10)

        # === 保存路径设置 ===
        # 假设 data 目录在：
        # /workspace/ros2_ws/src/virtual_realsense_camera/data
        # 你可以根据实际情况改这一行
        pkg_root = '/workspace/ros2_ws/src/virtual_realsense_camera'
        self.save_dir = os.path.join(pkg_root, 'data', 'rgb_from_mac')

        os.makedirs(self.save_dir, exist_ok=True)
        self.get_logger().info(f'Images will be saved to: {self.save_dir}')

        # 保存计数器（用于文件名）
        self.frame_idx = 0

        # HTTP MJPEG 流地址（宿主机），注意端口要和 mac 脚本一致
        self.stream_url = 'http://host.docker.internal:5012/video'

        # OpenCV 打开视频流
        self.cap = cv2.VideoCapture(self.stream_url)
        if not self.cap.isOpened():
            self.get_logger().error(f'Failed to open stream: {self.stream_url}')
        else:
            self.get_logger().info(f'Opened HTTP stream: {self.stream_url}')

        # 控制发布频率为 30 FPS
        self.target_fps = 30.0
        self.timer = self.create_timer(1.0 / self.target_fps, self.timer_callback)

        self.last_time = time.time()

    def timer_callback(self):
        if not self.cap.isOpened():
            return

        # 尽量在每个 timer tick 取一帧，近似 30fps
        ret, frame = self.cap.read()
        if not ret:
            self.get_logger().warn('Failed to read frame from stream')
            return

        # === 发布 ROS 图像（BGR8） ===
        msg = self.bridge.cv2_to_imgmsg(frame, encoding='bgr8')
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = 'camera_color_optical_frame'
        self.pub.publish(msg)

        # === 同步保存图像到 data/ 目录 ===
        self.frame_idx += 1

        # 文件名：timestamp_idx.jpg，便于排序和查找
        stamp_str = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        filename = f"rgb_{stamp_str}_{self.frame_idx:06d}.jpg"
        filepath = os.path.join(self.save_dir, filename)

        # OpenCV BGR8 直接保存即可
        success = cv2.imwrite(filepath, frame)
        if not success:
            self.get_logger().warn(f'Failed to save image: {filepath}')


def main(args=None):
    rclpy.init(args=args)
    node = HTTPCameraBridge()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    if node.cap.isOpened():
        node.cap.release()
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
