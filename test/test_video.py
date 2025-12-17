import cv2
import os
import glob

# Check available video devices
def check_video_devices():
    """
    Check and list all available video devices on the system
    """
    print("=== 检查系统视频设备 ===")
    
    # Check /dev/video* devices
    video_devices = glob.glob('/dev/video*')
    if not video_devices:
        print("❌ 未找到任何 /dev/video* 设备")
        print("\n可能的原因：")
        print("1. 摄像头未正确连接到虚拟机")
        print("2. 驱动未加载（运行: sudo modprobe uvcvideo）")
        print("3. VMware 中连接了错误的 USB 设备")
        print("\n请检查 VMware：虚拟机 → 可移动设备 → 选择正确的摄像头")
        return []
    
    print(f"✓ 找到 {len(video_devices)} 个视频设备:")
    for device in sorted(video_devices):
        print(f"  - {device}")
    
    return sorted(video_devices)

# Test each video device
def test_video_capture(device_id):
    """
    Test video capture from a specific device
    """
    print(f"\n=== 测试设备 {device_id} ===")
    
    cap = cv2.VideoCapture(device_id)
 
if not cap.isOpened():
        print(f"❌ 无法打开设备 {device_id}")
        return False
    
    # Get device properties
    width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    fps = cap.get(cv2.CAP_PROP_FPS)
    
    print(f"✓ 设备已打开")
    print(f"  分辨率: {int(width)}x{int(height)}")
    print(f"  帧率: {fps}")
    
    # Try to read a frame
    ret, frame = cap.read()
    if ret:
        print(f"✓ 成功读取帧，尺寸: {frame.shape}")
        cap.release()
        return True
    else:
        print(f"❌ 无法读取帧")
        cap.release()
        return False

# Main diagnostic
def main():
    print("OpenCV 摄像头诊断工具\n")
    
    # Check for video devices
    devices = check_video_devices()
    
    if not devices:
        print("\n请先解决设备检测问题后再运行此脚本")
        return
    
    # Test each device
    working_devices = []
    for i in range(len(devices)):
        if test_video_capture(i):
            working_devices.append(i)
    
    # Summary
    print("\n=== 总结 ===")
    if working_devices:
        print(f"✓ 找到 {len(working_devices)} 个可用的摄像头:")
        for device_id in working_devices:
            print(f"  - 设备 {device_id} (/dev/video{device_id})")
        
        # Start live preview for first working device
        device_id = working_devices[0]
        print(f"\n开始显示设备 {device_id} 的实时画面 (按 'q' 退出)...")
        
        cap = cv2.VideoCapture(device_id)
        while cap.isOpened():
            ret, frame = cap.read()
            if ret:
                cv2.imshow(f"Camera {device_id} (Press 'q' to quit)", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
 
cap.release()
cv2.destroyAllWindows()
    else:
        print("❌ 没有找到可用的摄像头设备")

if __name__ == "__main__":
    main()

