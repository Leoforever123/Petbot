#!/usr/bin/env python3
import os
from pathlib import Path

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2
import numpy as np


class RGBDImageSaver(Node):
    def __init__(self):
        super().__init__('rgbd_image_saver')

        self.bridge = CvBridge()

        # ====== 路径配置（按需修改）======
        base_dir = Path('/workspace/data')
        self.color_dir = base_dir / 'color'
        self.depth_dir = base_dir / 'depth'
        self.color_dir.mkdir(parents=True, exist_ok=True)
        self.depth_dir.mkdir(parents=True, exist_ok=True)

        # 计数器
        self.color_idx = 0
        self.depth_idx = 0

        # 订阅彩色图像 (BGR8)
        self.color_sub = self.create_subscription(
            Image,
            '/camera/color/image_raw',
            self.color_callback,
            10
        )

        # 订阅深度图像 (16UC1)
        self.depth_sub = self.create_subscription(
            Image,
            '/camera/depth/image_rect_raw',
            self.depth_callback,
            10
        )

        self.get_logger().info(
            f'RGBD image saver started.\n'
            f'  Color images  -> {self.color_dir}\n'
            f'  Depth images  -> {self.depth_dir}'
        )

    # ====== 彩色图保存 ======
    def color_callback(self, msg: Image):
        try:
            # msg -> OpenCV BGR 图像
            cv_img = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')

            filename = self.color_dir / f'color_{self.color_idx:06d}.png'
            self.color_idx += 1

            # 保存成 PNG
            cv2.imwrite(str(filename), cv_img)
            self.get_logger().debug(f'Saved color image: {filename}')
        except Exception as e:
            self.get_logger().error(f'Failed to save color image: {e}')

    # ====== 深度图保存 ======
    def depth_callback(self, msg: Image):
        try:
            # 保持原始编码，不做任何转换：16UC1 -> numpy uint16
            depth_img = self.bridge.imgmsg_to_cv2(msg, desired_encoding='passthrough')

            # 确保是 uint16
            if depth_img.dtype != np.uint16:
                depth_img = depth_img.astype(np.uint16)

            filename = self.depth_dir / f'depth_{self.depth_idx:06d}.png'
            self.depth_idx += 1

            # 保存为 16-bit PNG（cv2 会根据 dtype 决定位数）
            cv2.imwrite(str(filename), depth_img)
            self.get_logger().debug(f'Saved depth image: {filename}')
        except Exception as e:
            self.get_logger().error(f'Failed to save depth image: {e}')


def main(args=None):
    rclpy.init(args=args)
    node = RGBDImageSaver()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
