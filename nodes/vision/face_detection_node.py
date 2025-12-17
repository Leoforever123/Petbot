#!/usr/bin/env python3
"""
面部识别节点
使用face_recognition库检测人脸，在屏幕上显示方框，并发布人脸数据供body控制节点订阅
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import cv2
import face_recognition
import json
import numpy as np
from typing import List, Dict


class FaceDetectionNode(Node):
    def __init__(self):
        super().__init__('face_detection_node')
        
        # 声明参数
        self.declare_parameter('camera_index', 0)
        self.declare_parameter('frame_width', 640)
        self.declare_parameter('frame_height', 480)
        self.declare_parameter('publish_rate', 10.0)  # Hz
        self.declare_parameter('display_window', True)
        self.declare_parameter('detection_scale', 0.25)  # 缩放因子，提高检测速度
        
        # 获取参数
        camera_index = self.get_parameter('camera_index').value
        self.frame_width = self.get_parameter('frame_width').value
        self.frame_height = self.get_parameter('frame_height').value
        self.publish_rate = self.get_parameter('publish_rate').value
        self.display_window = self.get_parameter('display_window').value
        self.detection_scale = self.get_parameter('detection_scale').value
        
        self.get_logger().info('=' * 60)
        self.get_logger().info('🎥 Face Detection Node 初始化中...')
        self.get_logger().info('=' * 60)
        
        # 初始化摄像头
        self.get_logger().info(f'正在打开摄像头 {camera_index}...')
        self.cap = cv2.VideoCapture(camera_index)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.frame_width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.frame_height)
        
        if not self.cap.isOpened():
            self.get_logger().error(f'❌ 无法打开摄像头 {camera_index}')
            raise RuntimeError('摄像头初始化失败')
        
        self.get_logger().info(f'✅ 摄像头已打开')
        
        # 创建发布者
        self.publisher = self.create_publisher(
            String,
            'face_recognition_result',
            10
        )
        self.get_logger().info('✅ 已创建发布者: /face_recognition_result')
        
        # 创建定时器
        timer_period = 1.0 / self.publish_rate
        self.timer = self.create_timer(timer_period, self.timer_callback)
        
        # 用于跳帧处理（每N帧处理一次以提高性能）
        self.frame_count = 0
        self.process_every_n_frames = 2
        self.last_face_locations = []
        
        # 统计信息
        self.total_frames = 0
        self.faces_detected_frames = 0
        self.publish_count = 0
        
        self.get_logger().info('=' * 60)
        self.get_logger().info('✅ Face Detection Node 启动成功！')
        self.get_logger().info(f'   - 分辨率: {self.frame_width}x{self.frame_height}')
        self.get_logger().info(f'   - 发布频率: {self.publish_rate}Hz')
        self.get_logger().info(f'   - 检测缩放: {self.detection_scale}')
        self.get_logger().info(f'   - 显示窗口: {self.display_window}')
        self.get_logger().info('=' * 60)
    
    def detect_faces(self, frame: np.ndarray) -> List[tuple]:
        """
        检测图像中的人脸
        
        Args:
            frame: BGR格式的图像帧
            
        Returns:
            人脸位置列表，每个位置为(top, right, bottom, left)
        """
        # 转换为RGB（face_recognition需要RGB格式）
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # 缩小图像以提高检测速度
        if self.detection_scale != 1.0:
            small_frame = cv2.resize(
                rgb_frame, 
                (0, 0), 
                fx=self.detection_scale, 
                fy=self.detection_scale
            )
        else:
            small_frame = rgb_frame
        
        # 检测人脸位置
        face_locations = face_recognition.face_locations(
            small_frame,
            model='hog'  # 可选 'hog' 或 'cnn'，hog更快但精度略低
        )
        
        # 将坐标缩放回原始大小
        if self.detection_scale != 1.0:
            face_locations = [
                (
                    int(top / self.detection_scale),
                    int(right / self.detection_scale),
                    int(bottom / self.detection_scale),
                    int(left / self.detection_scale)
                )
                for (top, right, bottom, left) in face_locations
            ]
        
        return face_locations
    
    def draw_faces(self, frame: np.ndarray, face_locations: List[tuple]) -> np.ndarray:
        """
        在图像上绘制人脸方框和信息
        
        Args:
            frame: 原始图像帧
            face_locations: 人脸位置列表
            
        Returns:
            绘制了方框的图像
        """
        annotated_frame = frame.copy()
        
        for i, (top, right, bottom, left) in enumerate(face_locations):
            # 绘制矩形框
            cv2.rectangle(
                annotated_frame,
                (left, top),
                (right, bottom),
                (0, 255, 0),  # 绿色
                2
            )
            
            # 计算人脸中心点
            center_x = (left + right) // 2
            center_y = (top + bottom) // 2
            
            # 绘制中心点
            cv2.circle(
                annotated_frame,
                (center_x, center_y),
                5,
                (0, 0, 255),  # 红色
                -1
            )
            
            # 添加文字标签
            label = f'Face {i+1}'
            cv2.putText(
                annotated_frame,
                label,
                (left, top - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 0),
                2
            )
            
            # 显示坐标信息
            coord_text = f'({center_x}, {center_y})'
            cv2.putText(
                annotated_frame,
                coord_text,
                (left, bottom + 20),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (255, 255, 255),
                1
            )
        
        # 在左上角显示检测到的人脸数量
        info_text = f'Faces: {len(face_locations)}'
        cv2.putText(
            annotated_frame,
            info_text,
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 255),
            2
        )
        
        # 绘制图像中心十字线（用于对齐参考）
        center_x = self.frame_width // 2
        center_y = self.frame_height // 2
        cv2.drawMarker(
            annotated_frame,
            (center_x, center_y),
            (255, 0, 0),  # 蓝色
            cv2.MARKER_CROSS,
            20,
            2
        )
        
        return annotated_frame
    
    def faces_to_json(self, face_locations: List[tuple]) -> str:
        """
        将人脸位置转换为JSON格式
        
        Args:
            face_locations: 人脸位置列表
            
        Returns:
            JSON字符串，格式与原系统兼容
        """
        faces_data = []
        
        for top, right, bottom, left in face_locations:
            # 计算中心点
            center_x = (left + right) // 2
            center_y = (top + bottom) // 2
            
            # 构造数据，格式为: [top, left, bottom, right]
            # 注意：这里的顺序要与原系统保持一致
            face_dict = {
                'location': [top, left, bottom, right],
                'center': [center_x, center_y],
                'width': right - left,
                'height': bottom - top
            }
            faces_data.append(face_dict)
        
        return json.dumps(faces_data)
    
    def timer_callback(self):
        """定时器回调函数，读取图像、检测人脸、发布数据"""
        ret, frame = self.cap.read()
        
        if not ret:
            self.get_logger().warn('⚠️  无法读取摄像头帧')
            return
        
        self.total_frames += 1
        
        # 跳帧处理以提高性能
        self.frame_count += 1
        is_detection_frame = (self.frame_count % self.process_every_n_frames == 0)
        
        if is_detection_frame:
            # 执行人脸检测
            face_locations = self.detect_faces(frame)
            self.last_face_locations = face_locations
            
            if face_locations:
                self.get_logger().info('🔍 [帧 {}] 正在检测... 发现 {} 张人脸！'.format(
                    self.total_frames, len(face_locations)))
        else:
            # 使用上一次的检测结果
            face_locations = self.last_face_locations
        
        # 发布人脸数据
        if face_locations:
            self.faces_detected_frames += 1
            json_data = self.faces_to_json(face_locations)
            msg = String()
            msg.data = json_data
            self.publisher.publish(msg)
            self.publish_count += 1
            
            # 详细输出检测到的人脸信息
            if is_detection_frame:
                self.get_logger().info('📤 发布人脸数据:')
                for i, (top, right, bottom, left) in enumerate(face_locations):
                    center_x = (left + right) // 2
                    center_y = (top + bottom) // 2
                    width = right - left
                    height = bottom - top
                    self.get_logger().info('   人脸 {}: 中心=({}, {}), 尺寸={}x{}, 位置=[{}, {}, {}, {}]'.format(
                        i+1, center_x, center_y, width, height, top, left, bottom, right))
                self.get_logger().info('   JSON: {}'.format(json_data[:100] + '...' if len(json_data) > 100 else json_data))
                
        else:
            # 即使没有检测到人脸也发布空数据
            msg = String()
            msg.data = '[]'
            self.publisher.publish(msg)
            self.publish_count += 1
            
            if is_detection_frame and self.total_frames % 50 == 0:  # 每50帧提示一次
                self.get_logger().info('📭 [帧 {}] 未检测到人脸，发布空数据'.format(self.total_frames))
        
        # 每100帧输出一次统计
        if self.total_frames % 100 == 0:
            detection_rate = (self.faces_detected_frames / self.total_frames) * 100
            self.get_logger().info('📊 统计 [总帧数: {}]:'.format(self.total_frames))
            self.get_logger().info('   - 检测到人脸的帧: {} ({:.1f}%)'.format(
                self.faces_detected_frames, detection_rate))
            self.get_logger().info('   - 已发布消息: {}'.format(self.publish_count))
        
        # 显示图像（如果启用）
        if self.display_window:
            annotated_frame = self.draw_faces(frame, face_locations)
            cv2.imshow('Face Detection', annotated_frame)
            
            # 按'q'键退出
            if cv2.waitKey(1) & 0xFF == ord('q'):
                self.get_logger().info('👋 用户请求退出')
                rclpy.shutdown()
    
    def destroy_node(self):
        """清理资源"""
        self.cap.release()
        if self.display_window:
            cv2.destroyAllWindows()
        super().destroy_node()


def main(args=None):
    import argparse
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Face Detection Node')
    parser.add_argument('--camera_index', type=int, default=0, help='Camera device index')
    parser.add_argument('--frame_width', type=int, default=640, help='Frame width')
    parser.add_argument('--frame_height', type=int, default=480, help='Frame height')
    parser.add_argument('--publish_rate', type=float, default=10.0, help='Publish rate (Hz)')
    parser.add_argument('--display_window', type=str, default='true', help='Display window (true/false)')
    parser.add_argument('--detection_scale', type=float, default=0.25, help='Detection scale factor')
    
    # Parse known args to allow ROS args to pass through
    cmd_args, ros_args = parser.parse_known_args()
    
    # Initialize ROS with remaining args
    rclpy.init(args=ros_args)
    
    try:
        node = FaceDetectionNode()
        
        # Override parameters from command line if provided
        node.set_parameters([
            rclpy.parameter.Parameter('camera_index', rclpy.Parameter.Type.INTEGER, cmd_args.camera_index),
            rclpy.parameter.Parameter('frame_width', rclpy.Parameter.Type.INTEGER, cmd_args.frame_width),
            rclpy.parameter.Parameter('frame_height', rclpy.Parameter.Type.INTEGER, cmd_args.frame_height),
            rclpy.parameter.Parameter('publish_rate', rclpy.Parameter.Type.DOUBLE, cmd_args.publish_rate),
            rclpy.parameter.Parameter('display_window', rclpy.Parameter.Type.BOOL, 
                                    cmd_args.display_window.lower() in ['true', '1', 'yes']),
            rclpy.parameter.Parameter('detection_scale', rclpy.Parameter.Type.DOUBLE, cmd_args.detection_scale),
        ])
        
        # Re-initialize with new parameters
        camera_index = node.get_parameter('camera_index').value
        node.frame_width = node.get_parameter('frame_width').value
        node.frame_height = node.get_parameter('frame_height').value
        node.publish_rate = node.get_parameter('publish_rate').value
        node.display_window = node.get_parameter('display_window').value
        node.detection_scale = node.get_parameter('detection_scale').value
        
        # Reinitialize camera with new settings
        node.cap.release()
        node.cap = cv2.VideoCapture(camera_index)
        node.cap.set(cv2.CAP_PROP_FRAME_WIDTH, node.frame_width)
        node.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, node.frame_height)
        
        if not node.cap.isOpened():
            node.get_logger().error(f'无法打开摄像头 {camera_index}')
            raise RuntimeError('摄像头初始化失败')
        
        # Update timer
        node.destroy_timer(node.timer)
        timer_period = 1.0 / node.publish_rate
        node.timer = node.create_timer(timer_period, node.timer_callback)
        
        node.get_logger().info(
            f'面部识别节点已启动 - 分辨率: {node.frame_width}x{node.frame_height}, '
            f'发布频率: {node.publish_rate}Hz'
        )
        
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f'错误: {e}')
        import traceback
        traceback.print_exc()
    finally:
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()


