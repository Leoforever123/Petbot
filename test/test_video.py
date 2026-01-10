#!/usr/bin/env python3
"""
摄像头诊断工具 - 用于排查虚拟机中USB摄像头连接问题
"""

import cv2
import os
import sys
import glob
import subprocess

def check_system_info():
    """检查系统基本信息"""
    print("=" * 60)
    print("系统信息")
    print("=" * 60)
    
    # 检查是否在虚拟机中
    try:
        with open('/proc/cpuinfo', 'r') as f:
            cpuinfo = f.read()
            if 'hypervisor' in cpuinfo.lower() or 'vmware' in cpuinfo.lower() or 'virtualbox' in cpuinfo.lower():
                print("✓ 检测到虚拟机环境")
            else:
                print("ℹ️  可能运行在物理机上")
    except:
        pass
    
    # 检查OpenCV版本
    print(f"OpenCV 版本: {cv2.__version__}")
    
    # 检查是否有GUI支持
    try:
        # 测试能否显示窗口
        test_img = cv2.imread('/dev/null')  # 只是测试，不会真的打开
        print(f"✓ OpenCV 编译支持: {cv2.getBuildInformation().split('\\n')[0]}")
    except:
        pass
    
    print()

def check_usb_devices():
    """检查USB设备连接情况"""
    print("=" * 60)
    print("USB设备检查")
    print("=" * 60)
    
    try:
        # 使用lsusb列出所有USB设备
        result = subprocess.run(['lsusb'], capture_output=True, text=True)
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            print(f"找到 {len(lines)} 个USB设备:\n")
            
            camera_found = False
            for line in lines:
                # 常见摄像头关键词
                keywords = ['camera', 'webcam', 'video', 'imaging', 'logitech', 'microsoft']
                line_lower = line.lower()
                
                if any(keyword in line_lower for keyword in keywords):
                    print(f"📹 {line}")
                    camera_found = True
                else:
                    print(f"   {line}")
            
            if camera_found:
                print("\n✓ 发现可能的摄像头USB设备")
            else:
                print("\n⚠️  未发现明显的摄像头USB设备")
                print("   请确认虚拟机已连接USB摄像头")
        else:
            print("⚠️  无法运行 lsusb 命令")
    except FileNotFoundError:
        print("⚠️  lsusb 未安装，运行: sudo apt-get install usbutils")
    except Exception as e:
        print(f"❌ 检查USB设备时出错: {e}")
    
    print()

def check_video_devices():
    """
    Check and list all available video devices on the system
    """
    print("=" * 60)
    print("视频设备节点检查")
    print("=" * 60)
    
    # Check /dev/video* devices
    video_devices = glob.glob('/dev/video*')
    if not video_devices:
        print("❌ 未找到任何 /dev/video* 设备\n")
        print("可能的原因和解决方法：")
        print()
        print("1️⃣  摄像头未连接到虚拟机")
        print("   解决: VMware → 虚拟机菜单 → 可移动设备 → 选择摄像头 → 连接")
        print()
        print("2️⃣  USB驱动未加载")
        print("   解决: sudo modprobe uvcvideo")
        print("   验证: lsmod | grep uvcvideo")
        print()
        print("3️⃣  虚拟机USB控制器未启用")
        print("   解决: 虚拟机设置 → USB控制器 → 启用USB 2.0/3.0")
        print()
        print("4️⃣  权限问题")
        print("   解决: sudo chmod 666 /dev/video*")
        print()
        return []
    
    print(f"✓ 找到 {len(video_devices)} 个视频设备节点:\n")
    for device in sorted(video_devices):
        # 获取设备权限和所有者
        try:
            stat_info = os.stat(device)
            permissions = oct(stat_info.st_mode)[-3:]
            
            # 检查当前用户是否有读权限
            readable = os.access(device, os.R_OK)
            writable = os.access(device, os.W_OK)
            
            status = "✓" if (readable and writable) else "⚠️"
            perm_str = f"权限:{permissions} {'(可读写)' if (readable and writable) else '(权限不足!)'}"
            
            print(f"  {status} {device} - {perm_str}")
            
            if not (readable and writable):
                print(f"     💡 修复权限: sudo chmod 666 {device}")
        except Exception as e:
            print(f"  ⚠️  {device} - 无法检查权限: {e}")
    
    print()
    return sorted(video_devices)

# Test each video device
def test_video_capture(device_id):
    """
    Test video capture from a specific device
    """
    print("=" * 60)
    print(f"测试设备 {device_id} (/dev/video{device_id})")
    print("=" * 60)
    
    try:
        cap = cv2.VideoCapture(device_id)
        
        if not cap.isOpened():
            print(f"❌ 无法打开设备 {device_id}")
            print("\n可能的问题:")
            print("  - 设备正在被其他程序使用")
            print("  - 权限不足")
            print("  - 设备不是真实的摄像头（可能是元数据设备）")
            print(f"\n尝试: sudo fuser /dev/video{device_id}  # 查看哪个进程在使用")
            return False
        
        # Get device properties
        width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        fps = cap.get(cv2.CAP_PROP_FPS)
        backend = cap.getBackendName()
        
        print(f"✓ 设备已打开")
        print(f"  后端: {backend}")
        print(f"  分辨率: {int(width)}x{int(height)}")
        print(f"  帧率: {fps if fps > 0 else '未知'}")
        
        # Try to read a frame
        print("\n尝试读取帧...")
        ret, frame = cap.read()
        
        if ret and frame is not None:
            print(f"✓ 成功读取帧")
            print(f"  帧尺寸: {frame.shape}")
            print(f"  数据类型: {frame.dtype}")
            
            # 检查是否为有效图像（非全黑）
            mean_brightness = frame.mean()
            print(f"  平均亮度: {mean_brightness:.2f}")
            
            if mean_brightness < 1:
                print("  ⚠️  图像可能全黑，请检查摄像头镜头盖或光线")
            
            cap.release()
            return True
        else:
            print(f"❌ 无法读取帧")
            print("  设备可能不是真实的视频捕获设备")
            cap.release()
            return False
            
    except Exception as e:
        print(f"❌ 测试设备 {device_id} 时出错: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print()

def test_face_recognition():
    """测试face_recognition库"""
    print("=" * 60)
    print("Face Recognition 库测试")
    print("=" * 60)
    
    try:
        import face_recognition
        print(f"✓ face_recognition 已安装 (版本: {face_recognition.__version__ if hasattr(face_recognition, '__version__') else '未知'})")
        
        # 创建一个测试图像
        import numpy as np
        test_img = np.zeros((480, 640, 3), dtype=np.uint8)
        test_img_rgb = cv2.cvtColor(test_img, cv2.COLOR_BGR2RGB)
        
        # 测试检测功能
        print("测试人脸检测功能...")
        face_locations = face_recognition.face_locations(test_img_rgb)
        print(f"✓ face_recognition.face_locations() 可以正常调用")
        print(f"  (测试空白图像，检测到 {len(face_locations)} 张人脸，符合预期)")
        
        return True
        
    except ImportError:
        print("❌ face_recognition 未安装")
        print("\n安装方法:")
        print("  pip install face_recognition")
        print("  或: pip install face_recognition opencv-python")
        return False
    except Exception as e:
        print(f"❌ 测试 face_recognition 时出错: {e}")
        return False
    
    print()

# Main diagnostic
def main():
    print()
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 15 + "摄像头诊断工具" + " " * 15 + "║")
    print("║" + " " * 10 + "用于排查虚拟机USB摄像头问题" + " " * 10 + "║")
    print("╚" + "═" * 58 + "╝")
    print()
    
    # Step 1: 检查系统信息
    check_system_info()
    
    # Step 2: 检查USB设备
    check_usb_devices()
    
    # Step 3: 检查视频设备节点
    devices = check_video_devices()
    
    if not devices:
        print("=" * 60)
        print("诊断结果：未找到视频设备")
        print("=" * 60)
        print("\n请按照上述提示解决设备检测问题，然后重新运行此脚本")
        print("\n快速检查步骤:")
        print("  1. 检查虚拟机是否连接了USB摄像头")
        print("  2. 运行: ls -l /dev/video*")
        print("  3. 运行: lsusb")
        print("  4. 运行: sudo modprobe uvcvideo")
        print()
        return 1
    
    # Step 4: 测试每个设备
    working_devices = []
    print("=" * 60)
    print("开始测试各个设备...")
    print("=" * 60)
    print()
    
    for i in range(len(devices)):
        if test_video_capture(i):
            working_devices.append(i)
    
    # Step 5: 测试face_recognition库
    face_rec_ok = test_face_recognition()
    
    # Summary
    print()
    print("=" * 60)
    print("诊断总结")
    print("=" * 60)
    
    if working_devices:
        print(f"\n✅ 找到 {len(working_devices)} 个可用的摄像头:")
        for device_id in working_devices:
            print(f"   • 设备 {device_id} (/dev/video{device_id})")
        
        if face_rec_ok:
            print("\n✅ face_recognition 库正常")
        else:
            print("\n⚠️  face_recognition 库有问题，请先安装")
        
        print("\n" + "=" * 60)
        print("推荐配置")
        print("=" * 60)
        device_id = working_devices[0]
        print(f"\n在人脸识别节点中使用:")
        print(f"  CAMERA_INDEX={device_id} ./launch/start_face_tracking.sh")
        print(f"\n或者:")
        print(f"  python3 nodes/vision/face_detection_node.py --camera_index {device_id}")
        
        # 询问是否显示实时画面
        print("\n" + "=" * 60)
        try:
            response = input("是否显示实时画面测试? (y/n): ").strip().lower()
            if response == 'y' or response == 'yes':
                device_id = working_devices[0]
                print(f"\n开始显示设备 {device_id} 的实时画面 (按 'q' 退出)...\n")
                
                cap = cv2.VideoCapture(device_id)
                frame_count = 0
                
                while cap.isOpened():
                    ret, frame = cap.read()
                    if ret:
                        frame_count += 1
                        # 在图像上添加信息
                        cv2.putText(frame, f"Device: /dev/video{device_id}", (10, 30),
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                        cv2.putText(frame, f"Frame: {frame_count}", (10, 60),
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                        cv2.putText(frame, "Press 'q' to quit", (10, frame.shape[0] - 20),
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                        
                        cv2.imshow(f"Camera Test - /dev/video{device_id}", frame)
                        
                        if cv2.waitKey(1) & 0xFF == ord('q'):
                            break
                    else:
                        print("⚠️  读取帧失败")
                        break
                
                cap.release()
                cv2.destroyAllWindows()
                print("\n✓ 实时画面测试完成")
        except KeyboardInterrupt:
            print("\n\n用户中断")
        
        return 0
    else:
        print("\n❌ 没有找到可用的摄像头设备\n")
        print("所有设备测试都失败了。可能的原因:")
        print("  • 设备节点存在但不是真实的摄像头")
        print("  • 设备正在被其他程序使用")
        print("  • 虚拟机USB直通配置有问题")
        print()
        print("建议:")
        print("  1. 重启虚拟机")
        print("  2. 确保摄像头未被主机使用")
        print("  3. 检查虚拟机USB设置（USB 2.0/3.0控制器）")
        print()
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code if exit_code is not None else 0)
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断程序")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ 程序出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

