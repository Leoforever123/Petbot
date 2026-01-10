#!/usr/bin/env python3
"""
面部识别节点
使用face_recognition库检测人脸并识别已知人物，在屏幕上显示方框和名字
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from service_define.srv import SetString
import cv2
import face_recognition
import json
import numpy as np
from typing import List, Dict, Tuple
import os
import pickle
import time
import threading
import requests
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont

load_dotenv()


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
        self.declare_parameter('known_faces_dir', 'images/known_faces')  # 已知人脸照片目录
        self.declare_parameter('enable_expression', True)  # 是否启用表情控制
        self.declare_parameter('expression_server_url', 'http://localhost:8001')  # 表情服务器URL
        
        # 加载中文字体 (用于显示中文名字)
        self.chinese_font = None
        try:
            # 尝试加载常见的中文字体
            font_paths = [
                '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc',  # Ubuntu 文泉驿正黑
                '/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf',  # Droid字体
                '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',  # Noto Sans CJK
                '/System/Library/Fonts/PingFang.ttc',  # macOS
                'C:\\Windows\\Fonts\\simhei.ttf',  # Windows 黑体
            ]
            for font_path in font_paths:
                if os.path.exists(font_path):
                    self.chinese_font = ImageFont.truetype(font_path, 24)
                    self.get_logger().info(f'✅ 成功加载中文字体: {font_path}')
                    break
            
            if self.chinese_font is None:
                self.get_logger().warn('⚠️  未找到中文字体，使用默认字体')
                self.chinese_font = ImageFont.load_default()
        except Exception as e:
            self.get_logger().warn(f'⚠️  加载中文字体失败: {e}，使用默认字体')
            self.chinese_font = ImageFont.load_default()
        
        # 获取参数
        camera_index = self.get_parameter('camera_index').value
        self.frame_width = self.get_parameter('frame_width').value
        self.frame_height = self.get_parameter('frame_height').value
        self.publish_rate = self.get_parameter('publish_rate').value
        self.display_window = self.get_parameter('display_window').value
        self.detection_scale = self.get_parameter('detection_scale').value
        self.known_faces_dir = self.get_parameter('known_faces_dir').value
        self.enable_expression = self.get_parameter('enable_expression').value
        self.expression_server_url = self.get_parameter('expression_server_url').value
        
        self.get_logger().info('=' * 60)
        self.get_logger().info('🎥 Face Detection Node 初始化中...')
        self.get_logger().info('=' * 60)
        
        # 加载已知人脸
        self.known_face_encodings = []
        self.known_face_names = []
        # 添加锁保护共享数据（避免线程安全问题）
        self.faces_lock = threading.Lock()
        self._load_known_faces()
        
        # 初始化摄像头
        self.get_logger().info(f'正在打开USB摄像头 {camera_index}...')
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
        
        # 创建截图服务（用于"记住我的脸"功能）
        self.capture_service = self.create_service(
            SetString,
            'capture_face',
            self.capture_face_callback
        )
        self.get_logger().info('✅ 已创建服务: /capture_face')
        
        # 创建重新加载人脸服务（用于动态刷新）
        self.reload_faces_service = self.create_service(
            SetString,
            'reload_faces',
            self.reload_faces_callback
        )
        self.get_logger().info('✅ 已创建服务: /reload_faces')
        
        # 存储当前帧（用于截图）
        self.current_frame = None
        
        # 创建定时器
        timer_period = 1.0 / self.publish_rate
        self.timer = self.create_timer(timer_period, self.timer_callback)
        
        # 用于跳帧处理（每N帧处理一次以提高性能）
        self.frame_count = 0
        self.process_every_n_frames = 2
        self.last_face_locations = []
        self.last_face_names = []
        
        # 窗口初始化标志
        self.window_initialized = False
        
        # 统计信息
        self.total_frames = 0
        self.faces_detected_frames = 0
        self.publish_count = 0
        
        # 文件变化检测（用于自动刷新）
        self.last_file_check_time = time.time()
        self.file_check_interval = 5.0  # 每5秒检查一次
        self.known_files_hash = self._get_files_hash()  # 记录当前文件列表的哈希
        
        # 表情控制相关
        self.current_expression = None  # 当前表情状态
        self.last_expression_change_time = 0  # 上次切换表情的时间
        self.expression_debounce_time = 2.0  # 防抖时间（秒），避免频繁切换
        self.last_face_state = None  # 上次的人脸状态（all_known/has_unknown/no_face）
        
        # 表情映射配置
        self.expression_map = {
            'all_known': os.getenv('EXPRESSION_ALL_KNOWN', 'happy'),  # 全是认识的人
            'has_unknown': os.getenv('EXPRESSION_HAS_UNKNOWN', 'surprised'),  # 有陌生人
            'no_face': os.getenv('EXPRESSION_NO_FACE', 'neutral'),  # 没有人脸
        }
        
        # 检查表情服务器连接
        if self.enable_expression:
            self._check_expression_server()
        else:
            self.get_logger().info('⚠️  表情控制已禁用')
        
        self.get_logger().info('=' * 60)
        self.get_logger().info('✅ Face Detection Node 启动成功！')
        self.get_logger().info(f'   - 摄像头索引: {camera_index}')
        self.get_logger().info(f'   - 分辨率: {self.frame_width}x{self.frame_height}')
        self.get_logger().info(f'   - 发布频率: {self.publish_rate}Hz')
        self.get_logger().info(f'   - 检测缩放: {self.detection_scale}')
        self.get_logger().info(f'   - 显示窗口: {self.display_window}')
        self.get_logger().info(f'   - 已知人脸数: {len(self.known_face_names)}')
        self.get_logger().info(f'   - 表情控制: {"启用" if self.enable_expression else "禁用"}')
        if self.enable_expression:
            self.get_logger().info(f'   - 表情服务器: {self.expression_server_url}')
            self.get_logger().info(f'   - 全认识: {self.expression_map["all_known"]}')
            self.get_logger().info(f'   - 有陌生人: {self.expression_map["has_unknown"]}')
            self.get_logger().info(f'   - 无人脸: {self.expression_map["no_face"]}')
        self.get_logger().info('=' * 60)
        # 输出就绪标志 - 用于启动脚本检测
        print("PETBOT_FACE_READY", flush=True)
    
    def _check_expression_server(self):
        """检查表情服务器是否可用"""
        try:
            response = requests.get(
                f"{self.expression_server_url}/expressions",
                timeout=2.0
            )
            if response.status_code == 200:
                self.get_logger().info(f'✅ 表情服务器连接成功: {self.expression_server_url}')
                return True
            else:
                self.get_logger().warn(f'⚠️  表情服务器响应异常: {response.status_code}')
                return False
        except Exception as e:
            self.get_logger().warn(f'⚠️  无法连接到表情服务器: {e}')
            self.get_logger().warn('   表情控制功能将不可用')
            self.enable_expression = False
            return False
    
    def _change_expression(self, expression: str):
        """
        改变机器人表情
        
        Args:
            expression: 表情名称
        """
        if not self.enable_expression:
            return
        
        # 防抖：如果距离上次切换时间太短，不切换
        current_time = time.time()
        if current_time - self.last_expression_change_time < self.expression_debounce_time:
            return
        
        # 如果表情相同，不切换
        if expression == self.current_expression:
            return
        
        try:
            response = requests.post(
                f"{self.expression_server_url}/expression/{expression}",
                timeout=1.0
            )
            if response.status_code == 200:
                self.get_logger().info(f'😊 切换表情: {self.current_expression} → {expression}')
                self.current_expression = expression
                self.last_expression_change_time = current_time
            else:
                self.get_logger().warn(f'⚠️  切换表情失败: {response.status_code}')
        except Exception as e:
            self.get_logger().warn(f'⚠️  调用表情服务失败: {e}')
    
    def _update_expression_by_faces(self, face_names: List[str]):
        """
        根据识别到的人脸更新表情
        
        Args:
            face_names: 识别到的人名列表
        """
        if not self.enable_expression:
            return
        
        # 判断当前状态
        if not face_names:
            # 没有人脸
            new_state = 'no_face'
        else:
            # 有人脸，检查是否有陌生人
            unknown_count = sum(1 for name in face_names if name == "Unknown")
            if unknown_count > 0:
                # 有陌生人
                new_state = 'has_unknown'
            else:
                # 全是认识的人
                new_state = 'all_known'
        
        # 状态改变时切换表情
        if new_state != self.last_face_state:
            self.get_logger().info(f'🔄 人脸状态变化: {self.last_face_state} → {new_state}')
            target_expression = self.expression_map[new_state]
            self._change_expression(target_expression)
            self.last_face_state = new_state
    
    def _get_files_hash(self) -> str:
        """
        获取已知人脸目录中所有文件的哈希值（用于检测变化）
        
        Returns:
            文件列表的哈希字符串
        """
        import hashlib
        
        if not os.path.exists(self.known_faces_dir):
            return ""
        
        # 获取所有图片文件的修改时间
        files_info = []
        image_extensions = ['.jpg', '.jpeg', '.png', '.bmp']
        
        for filename in os.listdir(self.known_faces_dir):
            name, ext = os.path.splitext(filename)
            if ext.lower() in image_extensions:
                filepath = os.path.join(self.known_faces_dir, filename)
                try:
                    # 使用文件名和修改时间作为哈希依据
                    mtime = os.path.getmtime(filepath)
                    files_info.append(f"{filename}:{mtime}")
                except:
                    pass
        
        # 排序后生成哈希
        files_info.sort()
        hash_str = hashlib.md5("|".join(files_info).encode()).hexdigest()
        return hash_str
    
    def _check_and_reload_if_changed(self):
        """
        检查文件是否有变化，如果有则自动重新加载
        """
        current_time = time.time()
        
        # 检查是否到了检查时间
        if current_time - self.last_file_check_time < self.file_check_interval:
            return
        
        self.last_file_check_time = current_time
        
        # 获取当前文件哈希
        current_hash = self._get_files_hash()
        
        # 如果哈希不同，说明文件有变化
        if current_hash != self.known_files_hash:
            self.get_logger().info('🔍 检测到 known_faces 目录文件变化，自动重新加载...')
            # 使用锁保护共享数据
            with self.faces_lock:
                old_count = len(self.known_face_names)
                # 清空并重新加载
                self.known_face_encodings = []
                self.known_face_names = []
                self._load_known_faces()
                new_count = len(self.known_face_names)
            self.known_files_hash = current_hash  # 更新哈希
            
            self.get_logger().info(f'✅ 自动重新加载完成: {old_count} → {new_count} 个已知人脸')
    
    def _load_known_faces(self):
        """加载已知人脸数据"""
        self.get_logger().info(f'正在加载已知人脸从目录: {self.known_faces_dir}')
        
        # 如果目录不存在，创建它
        if not os.path.exists(self.known_faces_dir):
            os.makedirs(self.known_faces_dir)
            self.get_logger().warn(f'创建了目录: {self.known_faces_dir}')
            self.get_logger().info(f'请将已知人物的照片放入此目录，文件名即为人名')
            self.get_logger().info(f'例如: {self.known_faces_dir}/张三.jpg')
            return
        
        # 支持的图片格式
        image_extensions = ['.jpg', '.jpeg', '.png', '.bmp']
        
        # 遍历目录中的所有图片
        for filename in os.listdir(self.known_faces_dir):
            # 检查文件扩展名
            name, ext = os.path.splitext(filename)
            if ext.lower() not in image_extensions:
                continue
            
            filepath = os.path.join(self.known_faces_dir, filename)
            self.get_logger().info(f'  加载: {filename}')
            
            try:
                # 加载图片
                image = face_recognition.load_image_file(filepath)
                
                # 获取人脸编码
                encodings = face_recognition.face_encodings(image)
                
                if len(encodings) == 0:
                    self.get_logger().warn(f'  ⚠️  {filename} 中未检测到人脸，跳过')
                    continue
                
                if len(encodings) > 1:
                    self.get_logger().warn(f'  ⚠️  {filename} 中检测到多张人脸，使用第一张')
                
                # 使用第一张人脸的编码
                encoding = encodings[0]
                
                # 保存编码和名字
                self.known_face_encodings.append(encoding)
                self.known_face_names.append(name)
                
                self.get_logger().info(f'  ✓ 成功加载: {name}')
                
            except Exception as e:
                self.get_logger().error(f'  ❌ 加载 {filename} 失败: {e}')
        
        if len(self.known_face_names) > 0:
            self.get_logger().info(f'✅ 共加载 {len(self.known_face_names)} 个已知人脸')
        else:
            self.get_logger().warn('⚠️  未加载任何已知人脸，将只进行人脸检测')
    
    def detect_and_recognize_faces(self, frame: np.ndarray) -> Tuple[List[tuple], List[str]]:
        """
        检测并识别图像中的人脸
        
        Args:
            frame: BGR格式的图像帧
            
        Returns:
            (face_locations, face_names) 元组
            - face_locations: 人脸位置列表，每个位置为(top, right, bottom, left)
            - face_names: 对应的人名列表
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
        
        # 如果没有已知人脸，直接返回位置
        face_names = []
        # 使用锁保护共享数据，创建副本以避免长时间持有锁
        with self.faces_lock:
            known_encodings = list(self.known_face_encodings)  # 创建副本
            known_names = list(self.known_face_names)  # 创建副本
        
        if len(known_encodings) == 0:
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
            face_names = ["Unknown"] * len(face_locations)
            return face_locations, face_names
        
        # 获取人脸编码
        face_encodings = face_recognition.face_encodings(small_frame, face_locations)
        
        # 识别每张人脸
        for face_encoding in face_encodings:
            # 与已知人脸比对（使用锁保护的副本）
            matches = face_recognition.compare_faces(
                known_encodings, 
                face_encoding,
                tolerance=0.6  # 容差，越小越严格
            )
            name = "Unknown"
            
            # 如果找到匹配
            if True in matches:
                # 计算面部距离
                face_distances = face_recognition.face_distance(
                    known_encodings, 
                    face_encoding
                )
                best_match_index = np.argmin(face_distances)
                if matches[best_match_index]:
                    name = known_names[best_match_index]
            
            face_names.append(name)
        
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
        
        return face_locations, face_names
    
    def put_chinese_text(self, img: np.ndarray, text: str, position: Tuple[int, int], 
                        font_size: int = 24, color: Tuple[int, int, int] = (255, 255, 255),
                        bg_color: Tuple[int, int, int] = None) -> np.ndarray:
        """
        在OpenCV图像上绘制中文文字（使用PIL）
        
        Args:
            img: OpenCV BGR图像
            text: 要绘制的文字
            position: 文字位置 (x, y)
            font_size: 字体大小
            color: 文字颜色 (B, G, R) for OpenCV
            bg_color: 背景颜色，None表示不绘制背景
            
        Returns:
            绘制后的图像
        """
        # 转换为PIL Image (RGB)
        img_pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(img_pil)
        
        # 创建字体（如果需要调整大小）
        try:
            if font_size != 24:
                font_paths = [
                    '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc',
                    '/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf',
                    '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
                ]
                font = None
                for font_path in font_paths:
                    if os.path.exists(font_path):
                        font = ImageFont.truetype(font_path, font_size)
                        break
                if font is None:
                    font = ImageFont.load_default()
            else:
                font = self.chinese_font
        except:
            font = self.chinese_font
        
        # 获取文字边界框
        bbox = draw.textbbox(position, text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # 绘制背景
        if bg_color is not None:
            # OpenCV BGR to PIL RGB
            bg_color_rgb = (bg_color[2], bg_color[1], bg_color[0])
            bg_rect = [
                position[0] - 5,
                position[1] - 5,
                position[0] + text_width + 5,
                position[1] + text_height + 5
            ]
            draw.rectangle(bg_rect, fill=bg_color_rgb)
        
        # 绘制文字 (OpenCV BGR to PIL RGB)
        color_rgb = (color[2], color[1], color[0])
        draw.text(position, text, font=font, fill=color_rgb)
        
        # 转换回OpenCV BGR
        img_bgr = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)
        return img_bgr
    
    def draw_faces(self, frame: np.ndarray, face_locations: List[tuple], face_names: List[str]) -> np.ndarray:
        """
        在图像上绘制人脸方框、名字和信息
        
        Args:
            frame: 原始图像帧
            face_locations: 人脸位置列表
            face_names: 对应的人名列表
            
        Returns:
            绘制了方框的图像
        """
        annotated_frame = frame.copy()
        
        for i, ((top, right, bottom, left), name) in enumerate(zip(face_locations, face_names)):
            # 根据是否识别出来选择颜色
            if name == "Unknown":
                box_color = (0, 165, 255)  # 橙色 - 未知
                text_color = (0, 165, 255)
            else:
                box_color = (0, 255, 0)  # 绿色 - 已识别
                text_color = (0, 255, 0)
            
            # 绘制矩形框
            cv2.rectangle(
                annotated_frame,
                (left, top),
                (right, bottom),
                box_color,
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
            
            # 在人脸上方显示序号
            label = f'#{i+1}'
            cv2.putText(
                annotated_frame,
                label,
                (left, top - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                text_color,
                2
            )
            
            # 在人脸下方显示名字（重点功能）
            # 使用PIL绘制中文名字，支持中文显示
            name_label = name
            
            # 使用PIL绘制支持中文的名字
            annotated_frame = self.put_chinese_text(
                annotated_frame,
                name_label,
                (left + 5, bottom + 5),
                font_size=28,
                color=(255, 255, 255),  # 白色文字
                bg_color=box_color  # 与边框同色的背景
            )
            
            # 显示坐标信息（可选）
            coord_text = f'({center_x}, {center_y})'
            cv2.putText(
                annotated_frame,
                coord_text,
                (left, bottom + 45),  # 调整位置以适应新的名字显示
                cv2.FONT_HERSHEY_SIMPLEX,
                0.4,
                (255, 255, 255),
                1
            )
        
        # 在左上角显示统计信息
        info_y = 30
        cv2.putText(
            annotated_frame,
            f'Faces: {len(face_locations)}',
            (10, info_y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 255),
            2
        )
        
        # 显示已知人脸数
        info_y += 30
        cv2.putText(
            annotated_frame,
            f'Known: {len(self.known_face_names)}',
            (10, info_y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 0),
            2
        )
        
        # 绘制图像中心十字线（用于对齐参考）
        h, w = frame.shape[:2]
        center_x = w // 2
        center_y = h // 2
        cv2.drawMarker(
            annotated_frame,
            (center_x, center_y),
            (255, 0, 0),  # 蓝色
            cv2.MARKER_CROSS,
            20,
            2
        )
        
        return annotated_frame
    
    def faces_to_json(self, face_locations: List[tuple], face_names: List[str]) -> str:
        """
        将人脸位置和名字转换为JSON格式
        
        Args:
            face_locations: 人脸位置列表
            face_names: 对应的人名列表
            
        Returns:
            JSON字符串，格式与原系统兼容并添加name字段
        """
        faces_data = []
        
        for (top, right, bottom, left), name in zip(face_locations, face_names):
            # 计算中心点
            center_x = (left + right) // 2
            center_y = (top + bottom) // 2
            
            # 构造数据，格式为: [top, left, bottom, right]
            face_dict = {
                'location': [top, left, bottom, right],
                'center': [center_x, center_y],
                'width': right - left,
                'height': bottom - top,
                'name': name  # 新增：识别出的名字
            }
            faces_data.append(face_dict)
        
        return json.dumps(faces_data)
    
    def timer_callback(self):
        """定时器回调函数，读取图像、检测识别人脸、发布数据"""
        # 检查文件变化（自动刷新）
        self._check_and_reload_if_changed()
        
        ret, frame = self.cap.read()
        
        if not ret:
            self.get_logger().warn('⚠️  无法读取摄像头帧')
            return
        
        # 存储当前帧（用于截图功能）
        self.current_frame = frame.copy()
        
        self.total_frames += 1
        
        # 跳帧处理以提高性能
        self.frame_count += 1
        is_detection_frame = (self.frame_count % self.process_every_n_frames == 0)
        
        if is_detection_frame:
            # 执行人脸检测和识别
            face_locations, face_names = self.detect_and_recognize_faces(frame)
            self.last_face_locations = face_locations
            self.last_face_names = face_names
            
            # 根据识别结果更新表情
            self._update_expression_by_faces(face_names)
            
            if face_locations:
                recognized_count = sum(1 for name in face_names if name != "Unknown")
                self.get_logger().info('🔍 [帧 {}] 发现 {} 张人脸，识别出 {} 人'.format(
                    self.total_frames, len(face_locations), recognized_count))
        else:
            # 使用上一次的检测结果
            face_locations = self.last_face_locations
            face_names = self.last_face_names
        
        # 发布人脸数据
        if face_locations:
            self.faces_detected_frames += 1
            json_data = self.faces_to_json(face_locations, face_names)
            msg = String()
            msg.data = json_data
            self.publisher.publish(msg)
            self.publish_count += 1
            
            # 详细输出检测到的人脸信息
            if is_detection_frame:
                self.get_logger().info('📤 发布人脸数据:')
                for i, ((top, right, bottom, left), name) in enumerate(zip(face_locations, face_names)):
                    center_x = (left + right) // 2
                    center_y = (top + bottom) // 2
                    width = right - left
                    height = bottom - top
                    self.get_logger().info('   人脸 {}: {} - 中心=({}, {}), 尺寸={}x{}'.format(
                        i+1, name, center_x, center_y, width, height))
        else:
            # 即使没有检测到人脸也发布空数据
            msg = String()
            msg.data = '[]'
            self.publisher.publish(msg)
            self.publish_count += 1
            
            if is_detection_frame and self.total_frames % 50 == 0:
                self.get_logger().info('📭 [帧 {}] 未检测到人脸'.format(self.total_frames))
        
        # 每100帧输出一次统计
        if self.total_frames % 100 == 0:
            detection_rate = (self.faces_detected_frames / self.total_frames) * 100
            self.get_logger().info('📊 统计 [总帧数: {}]:'.format(self.total_frames))
            self.get_logger().info('   - 检测到人脸的帧: {} ({:.1f}%)'.format(
                self.faces_detected_frames, detection_rate))
            self.get_logger().info('   - 已发布消息: {}'.format(self.publish_count))
        
        # 显示图像（如果启用）
        if self.display_window:
            annotated_frame = self.draw_faces(frame, face_locations, face_names)
            
            # 首次显示时初始化窗口大小
            if not self.window_initialized:
                window_name = 'Face Detection & Recognition'
                cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
                
                # 设置窗口大小（比原始分辨率稍大，但不超过800x600）
                display_width = min(int(self.frame_width * 1.2), 800)
                display_height = min(int(self.frame_height * 1.2), 600)
                cv2.resizeWindow(window_name, display_width, display_height)
                
                # 设置窗口位置（左上角）
                try:
                    import tkinter as tk
                    root = tk.Tk()
                    root.destroy()
                    cv2.moveWindow(window_name, 50, 50)
                except:
                    pass
                
                self.window_initialized = True
                self.get_logger().info(f'📺 人脸识别窗口已创建: {display_width}x{display_height}')
            
            cv2.imshow('Face Detection & Recognition', annotated_frame)
            
            # 按'q'键退出
            if cv2.waitKey(1) & 0xFF == ord('q'):
                self.get_logger().info('👋 用户请求退出')
                rclpy.shutdown()
    
    def capture_face_callback(self, request, response):
        """
        处理截图请求的服务回调
        用于"记住我的脸"功能
        
        Args:
            request: SetString.Request，data字段包含人名
            response: SetString.Response
            
        Returns:
            response: 包含成功状态和消息
        """
        person_name = request.data.strip()
        
        self.get_logger().info('=' * 60)
        self.get_logger().info(f'📸 收到截图请求: 记住 "{person_name}" 的脸')
        
        if not person_name:
            response.success = False
            self.get_logger().error('❌ 人名为空')
            self.get_logger().info('=' * 60)
            return response
        
        if self.current_frame is None:
            response.success = False
            self.get_logger().error('❌ 当前没有摄像头帧')
            self.get_logger().info('=' * 60)
            return response
        
        try:
            # 检测当前帧中的人脸
            face_locations = face_recognition.face_locations(self.current_frame)
            
            if not face_locations:
                response.success = False
                self.get_logger().warn('⚠️  画面中没有检测到人脸')
                self.get_logger().info('=' * 60)
                return response
            
            if len(face_locations) > 1:
                response.success = False
                self.get_logger().warn(f'⚠️  检测到 {len(face_locations)} 张人脸，需要只有1张')
                self.get_logger().info('=' * 60)
                return response
            
            # 只有一张人脸，继续处理
            self.get_logger().info('✅ 检测到1张人脸')
            
            # 确保目录存在
            os.makedirs(self.known_faces_dir, exist_ok=True)
            
            # 生成文件名（支持中文）
            filename = f"{person_name}.jpg"
            filepath = os.path.join(self.known_faces_dir, filename)
            
            # 保存图像
            success = cv2.imwrite(filepath, self.current_frame)
            
            if success:
                self.get_logger().info(f'✅ 照片已保存: {filepath}')
                
                # 先返回成功响应，避免阻塞
                response.success = True
                self.get_logger().info(f'🎉 成功记住 "{person_name}" 的脸！')
                self.get_logger().info(f'   - 文件: {filepath}')
                
                # 异步重新加载已知人脸数据（不阻塞服务响应）
                # 使用线程在后台执行，避免超时
                def reload_faces_async():
                    try:
                        self.get_logger().info('🔄 后台重新加载人脸数据...')
                        # 使用锁保护共享数据
                        with self.faces_lock:
                            self.known_face_encodings = []
                            self.known_face_names = []
                            self._load_known_faces()
                            # 更新文件哈希
                            self.known_files_hash = self._get_files_hash()
                            new_count = len(self.known_face_names)
                        self.get_logger().info(f'✅ 人脸数据重新加载完成，当前已知人脸数: {new_count}')
                    except Exception as e:
                        self.get_logger().error(f'❌ 后台重新加载人脸数据失败: {e}')
                        import traceback
                        self.get_logger().error(traceback.format_exc())
                
                reload_thread = threading.Thread(target=reload_faces_async, daemon=True)
                reload_thread.start()
            else:
                response.success = False
                self.get_logger().error(f'❌ 保存图像失败: {filepath}')
            
        except Exception as e:
            response.success = False
            self.get_logger().error(f'❌ 截图过程出错: {e}')
            import traceback
            self.get_logger().error(traceback.format_exc())
        
        self.get_logger().info('=' * 60)
        return response
    
    def reload_faces_callback(self, request, response):
        """
        重新加载已知人脸数据的服务回调
        用于动态刷新人脸数据库（当文件被添加、删除或修改时）
        
        Args:
            request: SetString.Request（data字段可以包含提示信息，可选）
            response: SetString.Response
            
        Returns:
            response: 包含成功状态和消息
        """
        self.get_logger().info('=' * 60)
        self.get_logger().info('🔄 收到重新加载人脸数据请求')
        
        try:
            # 使用锁保护共享数据
            with self.faces_lock:
                # 清空当前数据
                old_count = len(self.known_face_names)
                self.known_face_encodings = []
                self.known_face_names = []
                
                # 重新加载
                self._load_known_faces()
                
                new_count = len(self.known_face_names)
            
            response.success = True
            
            self.get_logger().info(f'✅ 重新加载完成')
            self.get_logger().info(f'   - 之前: {old_count} 个已知人脸')
            self.get_logger().info(f'   - 现在: {new_count} 个已知人脸')
            
            if new_count != old_count:
                self.get_logger().info(f'   - 变化: {"+" if new_count > old_count else ""}{new_count - old_count} 个')
            
        except Exception as e:
            response.success = False
            self.get_logger().error(f'❌ 重新加载失败: {e}')
            import traceback
            self.get_logger().error(traceback.format_exc())
        
        self.get_logger().info('=' * 60)
        return response
    
    def destroy_node(self):
        """清理资源"""
        self.cap.release()
        if self.display_window:
            cv2.destroyAllWindows()
        super().destroy_node()


def main(args=None):
    import argparse
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Face Detection & Recognition Node')
    parser.add_argument('--camera_index', type=int, default=0, help='Camera device index')
    parser.add_argument('--frame_width', type=int, default=640, help='Frame width')
    parser.add_argument('--frame_height', type=int, default=480, help='Frame height')
    parser.add_argument('--publish_rate', type=float, default=10.0, help='Publish rate (Hz)')
    parser.add_argument('--display_window', type=str, default='true', help='Display window (true/false)')
    parser.add_argument('--detection_scale', type=float, default=0.25, help='Detection scale factor')
    parser.add_argument('--known_faces_dir', type=str, default='images/known_faces', help='Directory with known face images')
    
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
            rclpy.parameter.Parameter('known_faces_dir', rclpy.Parameter.Type.STRING, cmd_args.known_faces_dir),
        ])
        
        # Re-initialize with new parameters
        camera_index = node.get_parameter('camera_index').value
        node.frame_width = node.get_parameter('frame_width').value
        node.frame_height = node.get_parameter('frame_height').value
        node.publish_rate = node.get_parameter('publish_rate').value
        node.display_window = node.get_parameter('display_window').value
        node.detection_scale = node.get_parameter('detection_scale').value
        node.known_faces_dir = node.get_parameter('known_faces_dir').value
        
        # Reload known faces if directory changed
        node.known_face_encodings = []
        node.known_face_names = []
        node._load_known_faces()
        
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
