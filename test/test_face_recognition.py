"""
Face Recognition Test Program
人脸识别测试程序

功能：
1. 从视频流或摄像头中检测人脸并用方框标出
2. 识别已知人物并显示其姓名

使用方法：
1. 将已知人物的照片放在 images/known_faces/ 文件夹中
2. 照片命名格式：person_name.jpg (如: zhang_san.jpg, li_si.png)
3. 运行本程序
"""

import face_recognition
import cv2
import numpy as np
import os
from pathlib import Path


class FaceRecognitionSystem:
    """
    Face Recognition System for detecting and recognizing faces
    人脸识别系统类
    """
    
    def __init__(self, known_faces_dir):
        """
        Initialize the face recognition system
        初始化人脸识别系统
        
        Args:
            known_faces_dir (str): Directory containing known faces images
                                   包含已知人脸图片的文件夹路径
        """
        self.known_faces_dir = known_faces_dir
        self.known_face_encodings = []  # 存储已知人脸的编码
        self.known_face_names = []      # 存储已知人脸对应的姓名
        
        # Load known faces
        # 加载已知人脸数据
        self.load_known_faces()
    
    def load_known_faces(self):
        """
        Load all known faces from the specified directory
        从指定文件夹加载所有已知人脸
        
        face_recognition.load_image_file(): 加载图片文件
        face_recognition.face_encodings(): 获取图片中人脸的128维特征编码
        """
        print("=" * 60)
        print("正在加载已知人脸数据...")
        print(f"目录: {self.known_faces_dir}")
        
        # Check if directory exists
        # 检查目录是否存在
        if not os.path.exists(self.known_faces_dir):
            print(f"⚠️  目录不存在，创建目录: {self.known_faces_dir}")
            os.makedirs(self.known_faces_dir, exist_ok=True)
            print("\n请在该目录中添加已知人物的照片！")
            print("照片命名格式: person_name.jpg (如: zhang_san.jpg)")
            return
        
        # Supported image formats
        # 支持的图片格式
        image_extensions = ['.jpg', '.jpeg', '.png', '.bmp']
        
        # Load each image file
        # 加载每个图片文件
        image_files = []
        for ext in image_extensions:
            image_files.extend(Path(self.known_faces_dir).glob(f'*{ext}'))
            image_files.extend(Path(self.known_faces_dir).glob(f'*{ext.upper()}'))
        
        if not image_files:
            print(f"⚠️  目录中没有找到图片文件")
            print(f"支持的格式: {', '.join(image_extensions)}")
            print("\n请在该目录中添加已知人物的照片！")
            return
        
        # Process each image
        # 处理每张图片
        for image_path in image_files:
            try:
                # Get person name from filename (without extension)
                # 从文件名获取人物姓名（去掉扩展名）
                person_name = image_path.stem
                
                print(f"\n处理图片: {image_path.name}")
                
                # Load image file
                # face_recognition.load_image_file() 返回 numpy array (RGB格式)
                image = face_recognition.load_image_file(str(image_path))
                
                # Get face encodings from the image
                # face_recognition.face_encodings() 返回图片中所有人脸的编码列表
                # 每个编码是一个128维的numpy数组，代表人脸特征
                face_encodings = face_recognition.face_encodings(image)
                
                if len(face_encodings) == 0:
                    print(f"  ❌ 未检测到人脸")
                    continue
                
                if len(face_encodings) > 1:
                    print(f"  ⚠️  检测到 {len(face_encodings)} 张人脸，使用第一张")
                
                # Use the first face encoding
                # 使用第一个人脸编码
                face_encoding = face_encodings[0]
                
                # Store the encoding and name
                # 存储编码和姓名
                self.known_face_encodings.append(face_encoding)
                self.known_face_names.append(person_name)
                
                print(f"  ✓ 成功加载: {person_name}")
                
            except Exception as e:
                print(f"  ❌ 加载失败: {e}")
        
        print("\n" + "=" * 60)
        print(f"✓ 已加载 {len(self.known_face_names)} 个已知人脸:")
        for name in self.known_face_names:
            print(f"  - {name}")
        print("=" * 60 + "\n")
    
    def recognize_faces_in_frame(self, frame):
        """
        Recognize faces in a video frame
        识别视频帧中的人脸
        
        Args:
            frame: Video frame (BGR format from OpenCV)
                   视频帧（OpenCV的BGR格式）
        
        Returns:
            frame: Frame with face boxes and names drawn
                   绘制了人脸框和姓名的帧
            face_locations: List of face locations
                           人脸位置列表
            face_names: List of recognized names
                       识别出的姓名列表
        """
        # Resize frame for faster processing (optional)
        # 缩小帧尺寸以加快处理速度（可选）
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        
        # Convert BGR (OpenCV) to RGB (face_recognition)
        # 将BGR格式（OpenCV）转换为RGB格式（face_recognition）
        rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
        
        # Find all face locations in the frame
        # face_recognition.face_locations() 返回人脸位置列表
        # 每个位置是一个元组: (top, right, bottom, left)
        # model参数: "hog" 较快但不太准确, "cnn" 更准确但需要GPU
        face_locations = face_recognition.face_locations(rgb_small_frame, model="hog")
        
        # Get face encodings for all detected faces
        # face_recognition.face_encodings() 获取所有检测到人脸的编码
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)
        
        face_names = []
        
        # Compare each detected face with known faces
        # 将每个检测到的人脸与已知人脸进行比对
        for face_encoding in face_encodings:
            name = "Unknown"  # 默认为未知
            
            if len(self.known_face_encodings) > 0:
                # Compare face with all known faces
                # face_recognition.compare_faces() 比较人脸
                # 返回布尔值列表，表示是否匹配
                # tolerance参数: 越小越严格，默认0.6
                matches = face_recognition.compare_faces(
                    self.known_face_encodings, 
                    face_encoding,
                    tolerance=0.6
                )
                
                # Calculate face distances
                # face_recognition.face_distance() 计算人脸距离
                # 距离越小表示越相似
                face_distances = face_recognition.face_distance(
                    self.known_face_encodings, 
                    face_encoding
                )
                
                # Find the best match
                # 找到最佳匹配
                if len(face_distances) > 0:
                    best_match_index = np.argmin(face_distances)
                    if matches[best_match_index]:
                        name = self.known_face_names[best_match_index]
            
            face_names.append(name)
        
        # Scale back up face locations (we resized to 1/4)
        # 将人脸位置放大回原始尺寸（因为我们缩小到了1/4）
        face_locations = [(top * 4, right * 4, bottom * 4, left * 4) 
                         for (top, right, bottom, left) in face_locations]
        
        # Draw boxes and names on the frame
        # 在帧上绘制方框和姓名
        for (top, right, bottom, left), name in zip(face_locations, face_names):
            # Draw box around face
            # 在人脸周围绘制方框
            color = (0, 255, 0) if name != "Unknown" else (0, 0, 255)
            cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
            
            # Draw label background
            # 绘制标签背景
            cv2.rectangle(frame, (left, bottom - 35), (right, bottom), color, cv2.FILLED)
            
            # Draw name
            # 绘制姓名
            font = cv2.FONT_HERSHEY_DUPLEX
            cv2.putText(frame, name, (left + 6, bottom - 6), font, 0.8, (255, 255, 255), 1)
        
        return frame, face_locations, face_names
    
    def process_video_stream(self, video_source=0):
        """
        Process video stream and recognize faces in real-time
        处理视频流并实时识别人脸
        
        Args:
            video_source: Video source (0 for default camera, or video file path)
                         视频源（0表示默认摄像头，或视频文件路径）
        """
        print(f"正在打开视频源: {video_source}")
        
        # Open video capture
        # 打开视频捕获
        video_capture = cv2.VideoCapture(video_source)
        
        if not video_capture.isOpened():
            print(f"❌ 无法打开视频源: {video_source}")
            print("\n如果没有摄像头，可以使用测试视频文件：")
            print("  video_capture = cv2.VideoCapture('path/to/video.mp4')")
            return
        
        print("✓ 视频源已打开")
        print("\n控制说明:")
        print("  - 按 'q' 退出")
        print("  - 按 's' 截图保存当前帧")
        print("\n开始识别...\n")
        
        frame_count = 0
        
        try:
            while True:
                # Read frame from video
                # 从视频读取一帧
                ret, frame = video_capture.read()
                
                if not ret:
                    print("视频流结束")
                    break
                
                frame_count += 1
                
                # Process every other frame to improve performance
                # 每隔一帧处理一次以提高性能
                if frame_count % 2 == 0:
                    frame, face_locations, face_names = self.recognize_faces_in_frame(frame)
                
                # Display info on frame
                # 在帧上显示信息
                info_text = f"Faces: {len(face_locations)} | Frame: {frame_count}"
                cv2.putText(frame, info_text, (10, 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
                # Show frame
                # 显示帧
                cv2.imshow('Face Recognition (Press "q" to quit, "s" to save)', frame)
                
                # Handle keyboard input
                # 处理键盘输入
                key = cv2.waitKey(1) & 0xFF
                
                if key == ord('q'):
                    print("\n用户退出")
                    break
                elif key == ord('s'):
                    # Save screenshot
                    # 保存截图
                    screenshot_path = f"screenshot_{frame_count}.jpg"
                    cv2.imwrite(screenshot_path, frame)
                    print(f"截图已保存: {screenshot_path}")
        
        except KeyboardInterrupt:
            print("\n\n程序被中断")
        
        finally:
            # Clean up
            # 清理资源
            video_capture.release()
            cv2.destroyAllWindows()
            print("\n资源已释放，程序结束")
    
    def recognize_image(self, image_path):
        """
        Recognize faces in a single image
        识别单张图片中的人脸
        
        Args:
            image_path (str): Path to the image file
                             图片文件路径
        """
        print(f"\n处理图片: {image_path}")
        
        # Load image
        # 加载图片
        image = face_recognition.load_image_file(image_path)
        
        # Convert to BGR for OpenCV display
        # 转换为BGR格式以便OpenCV显示
        image_bgr = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        
        # Recognize faces
        # 识别人脸
        result_image, face_locations, face_names = self.recognize_faces_in_frame(image_bgr)
        
        print(f"检测到 {len(face_locations)} 张人脸:")
        for name in face_names:
            print(f"  - {name}")
        
        # Display result
        # 显示结果
        cv2.imshow('Face Recognition Result (Press any key to close)', result_image)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
        
        # Save result
        # 保存结果
        output_path = image_path.replace('.', '_result.')
        cv2.imwrite(output_path, result_image)
        print(f"结果已保存: {output_path}")


def main():
    """
    Main function to run the face recognition system
    主函数
    """
    print("\n" + "=" * 60)
    print("人脸识别测试程序")
    print("Face Recognition Test Program")
    print("=" * 60 + "\n")
    
    # Set up paths
    # 设置路径
    project_root = Path(__file__).parent.parent
    known_faces_dir = project_root / "images" / "known_faces"
    
    # Initialize face recognition system
    # 初始化人脸识别系统
    fr_system = FaceRecognitionSystem(str(known_faces_dir))
    
    # Check if any known faces were loaded
    # 检查是否加载了已知人脸
    if len(fr_system.known_face_names) == 0:
        print("\n⚠️  未加载任何已知人脸!")
        print(f"\n请在以下目录中添加已知人物的照片:")
        print(f"  {known_faces_dir}")
        print("\n照片命名示例:")
        print("  - 张三.jpg")
        print("  - zhang_san.png")
        print("  - John_Doe.jpeg")
        print("\n添加照片后重新运行程序。")
        print("\n现在将以 '未知' 模式运行，仅检测人脸...")
        input("\n按回车键继续...")
    
    # Menu
    # 菜单
    while True:
        print("\n" + "=" * 60)
        print("请选择功能:")
        print("  1. 从摄像头识别人脸 (实时)")
        print("  2. 从视频文件识别人脸")
        print("  3. 从图片文件识别人脸")
        print("  4. 重新加载已知人脸数据")
        print("  0. 退出")
        print("=" * 60)
        
        choice = input("\n请输入选项 (0-4): ").strip()
        
        if choice == '1':
            # Real-time camera
            # 实时摄像头
            fr_system.process_video_stream(0)
        
        elif choice == '2':
            # Video file
            # 视频文件
            video_path = input("请输入视频文件路径: ").strip()
            if os.path.exists(video_path):
                fr_system.process_video_stream(video_path)
            else:
                print(f"❌ 文件不存在: {video_path}")
        
        elif choice == '3':
            # Image file
            # 图片文件
            image_path = input("请输入图片文件路径: ").strip()
            if os.path.exists(image_path):
                fr_system.recognize_image(image_path)
            else:
                print(f"❌ 文件不存在: {image_path}")
        
        elif choice == '4':
            # Reload known faces
            # 重新加载已知人脸
            fr_system.load_known_faces()
        
        elif choice == '0':
            print("\n再见！")
            break
        
        else:
            print("\n❌ 无效选项，请重新输入")


if __name__ == "__main__":
    main()

