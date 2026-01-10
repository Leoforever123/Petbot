#!/usr/bin/env python3
"""
UDP视频流接收测试脚本
用于测试从主机通过ffmpeg转发的摄像头流
"""

import cv2
import sys
import time
import socket

def check_port_open(port=5555):
    """检查UDP端口是否可用"""
    print("=" * 60)
    print(f"检查UDP端口 {port}")
    print("=" * 60)
    
    try:
        # 创建UDP socket
        sock = socket.socket(socket.SOCK_DGRAM)
        sock.bind(('0.0.0.0', port))
        sock.close()
        print(f"✓ 端口 {port} 可用")
        return True
    except OSError as e:
        print(f"❌ 端口 {port} 不可用: {e}")
        print(f"\n可能被其他程序占用，运行以下命令检查:")
        print(f"  sudo netstat -tulpn | grep {port}")
        print(f"  或: sudo lsof -i :{port}")
        return False
    
    print()

def test_udp_stream(port=5555, timeout=10):
    """测试UDP视频流接收"""
    print("=" * 60)
    print(f"测试UDP视频流接收 (端口 {port})")
    print("=" * 60)
    
    # 构建UDP流URL
    stream_url = f"udp://0.0.0.0:{port}"
    print(f"\nUDP流地址: {stream_url}")
    print(f"超时设置: {timeout}秒")
    print()
    
    print("正在尝试打开UDP流...")
    print("(如果卡住，请确保主机端ffmpeg正在发送流)")
    print()
    
    # 创建VideoCapture对象
    cap = cv2.VideoCapture(stream_url, cv2.CAP_FFMPEG)
    
    # 设置超时
    cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, timeout * 1000)
    cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, 5000)  # 5秒读取超时
    
    if not cap.isOpened():
        print("❌ 无法打开UDP流")
        print("\n可能的问题:")
        print("  1. 主机端ffmpeg未启动或已停止")
        print("  2. IP地址或端口不正确")
        print("  3. 防火墙阻止了UDP流量")
        print("  4. 网络连接问题")
        print()
        print("调试步骤:")
        print(f"  1. 在虚拟机中运行: nc -ul {port}  (监听UDP端口)")
        print("  2. 在主机端运行ffmpeg命令")
        print("  3. 检查nc是否收到数据")
        print()
        print("  4. 检查防火墙:")
        print(f"     sudo ufw allow {port}/udp")
        print(f"     或: sudo iptables -A INPUT -p udp --dport {port} -j ACCEPT")
        return False
    
    print("✓ UDP流已打开")
    
    # 获取流属性
    width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    fps = cap.get(cv2.CAP_PROP_FPS)
    
    print(f"  分辨率: {int(width)}x{int(height)}")
    print(f"  帧率: {fps if fps > 0 else '未知'}")
    print()
    
    # 尝试读取帧
    print("正在读取第一帧...")
    ret, frame = cap.read()
    
    if not ret or frame is None:
        print("❌ 无法读取帧")
        print("\n可能的问题:")
        print("  • UDP流已连接但没有数据传输")
        print("  • ffmpeg编码格式不兼容")
        print("  • 网络丢包严重")
        print()
        print("建议:")
        print("  • 确认主机端ffmpeg正在运行")
        print("  • 检查ffmpeg输出是否有错误")
        print("  • 尝试使用tcpdump监听: sudo tcpdump -i any -n port {port}")
        cap.release()
        return False
    
    print("✓ 成功读取第一帧")
    print(f"  帧尺寸: {frame.shape}")
    print(f"  数据类型: {frame.dtype}")
    
    mean_brightness = frame.mean()
    print(f"  平均亮度: {mean_brightness:.2f}")
    
    if mean_brightness < 1:
        print("  ⚠️  图像可能全黑，请检查摄像头")
    
    cap.release()
    return True

def show_live_stream(port=5555):
    """显示实时UDP流"""
    print("=" * 60)
    print("显示实时UDP流")
    print("=" * 60)
    
    stream_url = f"udp://0.0.0.0:{port}"
    
    print(f"\n正在打开: {stream_url}")
    print("按 'q' 键退出\n")
    
    cap = cv2.VideoCapture(stream_url, cv2.CAP_FFMPEG)
    
    if not cap.isOpened():
        print("❌ 无法打开UDP流")
        return False
    
    frame_count = 0
    start_time = time.time()
    last_fps_time = start_time
    fps_counter = 0
    current_fps = 0.0
    
    try:
        while True:
            ret, frame = cap.read()
            
            if not ret or frame is None:
                print("⚠️  读取帧失败，可能流中断了")
                break
            
            frame_count += 1
            fps_counter += 1
            
            # 计算实际FPS
            current_time = time.time()
            if current_time - last_fps_time >= 1.0:
                current_fps = fps_counter / (current_time - last_fps_time)
                fps_counter = 0
                last_fps_time = current_time
            
            # 在图像上添加信息
            info_y = 30
            cv2.putText(frame, f"UDP Stream: port {port}", (10, info_y),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            info_y += 30
            cv2.putText(frame, f"Frame: {frame_count}", (10, info_y),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            info_y += 30
            cv2.putText(frame, f"FPS: {current_fps:.1f}", (10, info_y),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            elapsed = time.time() - start_time
            info_y += 30
            cv2.putText(frame, f"Time: {elapsed:.1f}s", (10, info_y),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            # 底部提示
            cv2.putText(frame, "Press 'q' to quit", (10, frame.shape[0] - 20),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            
            cv2.imshow("UDP Stream Viewer", frame)
            
            # 按 'q' 退出
            if cv2.waitKey(1) & 0xFF == ord('q'):
                print("\n用户退出")
                break
                
    except KeyboardInterrupt:
        print("\n\n用户中断")
    finally:
        cap.release()
        cv2.destroyAllWindows()
        
        # 统计信息
        total_time = time.time() - start_time
        avg_fps = frame_count / total_time if total_time > 0 else 0
        
        print()
        print("=" * 60)
        print("流统计")
        print("=" * 60)
        print(f"总帧数: {frame_count}")
        print(f"总时长: {total_time:.2f}秒")
        print(f"平均FPS: {avg_fps:.2f}")
        print()
    
    return True

def check_network():
    """检查网络配置"""
    print("=" * 60)
    print("网络配置检查")
    print("=" * 60)
    
    try:
        import subprocess
        
        # 获取IP地址
        result = subprocess.run(['hostname', '-I'], capture_output=True, text=True)
        if result.returncode == 0:
            ips = result.stdout.strip().split()
            print(f"\n虚拟机IP地址: {', '.join(ips)}")
            print("\n确认主机端ffmpeg使用的IP地址是否正确")
        
        # 检查是否可以ping通主机
        print("\n检查网络连接...")
        # 这里可以添加ping测试，但需要主机IP
        
    except Exception as e:
        print(f"⚠️  无法检查网络: {e}")
    
    print()

def main():
    print()
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 18 + "UDP视频流测试工具" + " " * 18 + "║")
    print("║" + " " * 12 + "用于测试ffmpeg UDP流转发" + " " * 13 + "║")
    print("╚" + "═" * 58 + "╝")
    print()
    
    # 默认端口
    PORT = 5555
    
    # 可以从命令行参数获取端口
    if len(sys.argv) > 1:
        try:
            PORT = int(sys.argv[1])
            print(f"使用命令行指定的端口: {PORT}\n")
        except ValueError:
            print(f"⚠️  无效的端口号: {sys.argv[1]}，使用默认端口 {PORT}\n")
    
    print("主机端应该运行的命令:")
    print("-" * 60)
    print(f'ffmpeg -f dshow -i video="Camera Sensor Front" \\')
    print(f'       -preset ultrafast -tune zerolatency \\')
    print(f'       -vcodec libx264 -f mpegts \\')
    print(f'       udp://192.169.74.128:{PORT}')
    print("-" * 60)
    print()
    print("⚠️  注意: 请确保IP地址是虚拟机的实际IP地址")
    print()
    
    # Step 1: 检查网络
    check_network()
    
    # Step 2: 检查端口
    if not check_port_open(PORT):
        print("\n端口检查失败，但仍可以继续测试...")
        print()
    
    # Step 3: 测试UDP流
    if test_udp_stream(PORT):
        print()
        print("=" * 60)
        print("基本测试通过！")
        print("=" * 60)
        print()
        
        # Step 4: 询问是否显示实时流
        try:
            response = input("是否显示实时视频流? (y/n): ").strip().lower()
            if response == 'y' or response == 'yes':
                print()
                show_live_stream(PORT)
        except KeyboardInterrupt:
            print("\n\n用户中断")
        
        print()
        print("=" * 60)
        print("配置建议")
        print("=" * 60)
        print()
        print("在人脸识别节点中使用UDP流:")
        print()
        print("方法1: 修改face_detection_node_universal.py")
        print(f'  stream_url = "udp://0.0.0.0:{PORT}"')
        print('  cap = cv2.VideoCapture(stream_url, cv2.CAP_FFMPEG)')
        print()
        print("方法2: 创建专门的UDP流桥接节点")
        print("  (建议，更灵活)")
        print()
        
        return 0
    else:
        print()
        print("=" * 60)
        print("测试失败")
        print("=" * 60)
        print()
        print("常见问题排查:")
        print()
        print("1️⃣  确认主机端ffmpeg正在运行")
        print("   • 检查命令窗口是否有错误")
        print("   • 确认没有弹出摄像头权限对话框")
        print()
        print("2️⃣  确认IP地址正确")
        print("   • 在虚拟机中运行: hostname -I")
        print("   • 确保ffmpeg使用的IP匹配")
        print()
        print("3️⃣  检查防火墙")
        print(f"   • sudo ufw status")
        print(f"   • sudo ufw allow {PORT}/udp")
        print()
        print("4️⃣  测试网络连接")
        print(f"   • 在虚拟机运行: nc -ul {PORT}")
        print("   • 启动ffmpeg")
        print("   • 看nc是否收到数据")
        print()
        print("5️⃣  使用tcpdump监听")
        print(f"   • sudo tcpdump -i any -n port {PORT}")
        print("   • 查看是否有UDP包到达")
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

