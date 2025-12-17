#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image, CameraInfo
from cv_bridge import CvBridge
import numpy as np


class VirtualDepthCamera(Node):
    def __init__(self):
        super().__init__('virtual_depth_camera')

        self.bridge = CvBridge()

        # 深度图话题
        self.depth_pub = self.create_publisher(Image, '/camera/depth/image_rect_raw', 10)
        self.depth_info_pub = self.create_publisher(CameraInfo, '/camera/depth/camera_info', 10)

        # 30 FPS
        self.timer = self.create_timer(1.0 / 30.0, self.timer_callback)

        # 构造 CameraInfo（示例参数，和 color 对齐）
        self.depth_info = CameraInfo()
        self.depth_info.width = 640
        self.depth_info.height = 480
        fx = 525.0
        fy = 525.0
        cx = 319.5
        cy = 239.5
        self.depth_info.k = [fx, 0.0, cx,
                             0.0, fy, cy,
                             0.0, 0.0, 1.0]
        self.depth_info.d = [0.0, 0.0, 0.0, 0.0, 0.0]
        self.depth_info.distortion_model = 'plumb_bob'
        self.depth_info.r = [1.0, 0.0, 0.0,
                             0.0, 1.0, 0.0,
                             0.0, 0.0, 1.0]
        self.depth_info.p = [fx, 0.0, cx, 0.0,
                             0.0, fy, cy, 0.0,
                             0.0, 0.0, 1.0, 0.0]

        self.depth_frame_id = 'camera_depth_optical_frame'
        self.get_logger().info('Virtual depth camera node started (Z16, 30 FPS).')

    def timer_callback(self):
        # 1. 生成一张 16-bit 深度图（单位：毫米）
        h, w = 480, 640

        # 基础平面：所有像素 2.0m （2000 mm）
        depth_mm = np.full((h, w), 2000, dtype=np.uint16)

        # 做一点花样：中间区域拉近/拉远，模拟场景
        cx, cy = w // 2, h // 2
        y_grid, x_grid = np.ogrid[:h, :w]
        dist2 = (x_grid - cx) ** 2 + (y_grid - cy) ** 2

        # 圆形区域更近一点（1500 mm）
        mask_near = dist2 < (min(h, w) // 4) ** 2
        depth_mm[mask_near] = 1500

        # 外圈更远一点（2500 mm）
        mask_far = dist2 > (min(h, w) // 3) ** 2
        depth_mm[mask_far] = 2500

        # 2. numpy(16UC1) -> ROS Image (encoding='16UC1')
        depth_msg = self.bridge.cv2_to_imgmsg(depth_mm, encoding='16UC1')

        now = self.get_clock().now().to_msg()
        depth_msg.header.stamp = now
        depth_msg.header.frame_id = self.depth_frame_id

        # 3. CameraInfo 对齐
        self.depth_info.header.stamp = now
        self.depth_info.header.frame_id = self.depth_frame_id

        # 4. 发布
        self.depth_pub.publish(depth_msg)
        self.depth_info_pub.publish(self.depth_info)


def main(args=None):
    rclpy.init(args=args)
    node = VirtualDepthCamera()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
