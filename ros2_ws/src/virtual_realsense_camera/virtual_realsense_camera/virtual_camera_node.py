#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image, CameraInfo
from cv_bridge import CvBridge
import cv2
import numpy as np


class VirtualRealsenseCamera(Node):
    def __init__(self):
        super().__init__('virtual_realsense_camera')

        self.bridge = CvBridge()

        # 发布 RealSense 风格的颜色图和相机内参
        self.color_pub = self.create_publisher(Image, '/camera/color/image_raw', 10)
        self.color_info_pub = self.create_publisher(CameraInfo, '/camera/color/camera_info', 10)

        # 30 FPS 定时器
        self.timer = self.create_timer(1.0 / 30.0, self.timer_callback)

        # 构造一个简单的 CameraInfo（示例）
        self.color_info = CameraInfo()
        self.color_info.width = 640
        self.color_info.height = 480
        fx = 525.0
        fy = 525.0
        cx = 319.5
        cy = 239.5
        self.color_info.k = [fx, 0.0, cx,
                             0.0, fy, cy,
                             0.0, 0.0, 1.0]
        self.color_info.d = [0.0, 0.0, 0.0, 0.0, 0.0]
        self.color_info.distortion_model = 'plumb_bob'
        self.color_info.r = [1.0, 0.0, 0.0,
                             0.0, 1.0, 0.0,
                             0.0, 0.0, 1.0]
        self.color_info.p = [fx, 0.0, cx, 0.0,
                             0.0, fy, cy, 0.0,
                             0.0, 0.0, 1.0, 0.0]

        self.color_frame_id = 'camera_color_optical_frame'
        self.get_logger().info('Virtual RealSense camera node started.')

    def timer_callback(self):
        # 1. 生成一张测试图像
        h, w = 480, 640
        img = np.zeros((h, w, 3), dtype=np.uint8)
        cv2.putText(img, 'Virtual RealSense RGB', (50, 240),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)

        t = self.get_clock().now().nanoseconds // 10**7
        x = int((t % (w - 100)))
        cv2.rectangle(img, (x, 100), (x + 50, 150), (255, 0, 0), -1)

        # 2. 转成 ROS Image
        img_msg = self.bridge.cv2_to_imgmsg(img, encoding='bgr8')
        now = self.get_clock().now().to_msg()
        img_msg.header.stamp = now
        img_msg.header.frame_id = self.color_frame_id

        # 3. CameraInfo 对齐
        self.color_info.header.stamp = now
        self.color_info.header.frame_id = self.color_frame_id

        # 4. 发布
        self.color_pub.publish(img_msg)
        self.color_info_pub.publish(self.color_info)


def main(args=None):
    rclpy.init(args=args)
    node = VirtualRealsenseCamera()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
