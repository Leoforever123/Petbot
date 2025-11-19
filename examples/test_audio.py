#!/usr/bin/env python3
"""
Test audio device availability in WSL2
"""

import pyaudio
import sys

def test_audio_devices():
    """Test PyAudio device availability"""
    try:
        p = pyaudio.PyAudio()
        
        print("\n" + "="*70)
        print("PyAudio 音频设备测试".center(70))
        print("="*70 + "\n")
        
        device_count = p.get_device_count()
        print(f"找到 {device_count} 个音频设备\n")
        
        if device_count == 0:
            print("❌ 没有找到音频设备!")
            print("\n请按照以下步骤配置 WSL2 音频:")
            print("1. 确保 WSL2 已更新: wsl --update (在 Windows PowerShell 中)")
            print("2. 安装音频工具: sudo apt-get install -y pulseaudio alsa-utils")
            print("3. 配置 PulseAudio:")
            print("   mkdir -p ~/.config/pulse")
            print("   echo 'default-server = unix:/mnt/wslg/PulseServer' > ~/.config/pulse/client.conf")
            p.terminate()
            return False
        
        # 列出所有设备
        input_devices = []
        for i in range(device_count):
            try:
                info = p.get_device_info_by_index(i)
                print(f"设备 {i}:")
                print(f"  名称: {info['name']}")
                print(f"  输入通道: {info['maxInputChannels']}")
                print(f"  输出通道: {info['maxOutputChannels']}")
                print(f"  采样率: {int(info['defaultSampleRate'])} Hz")
                print()
                
                if info['maxInputChannels'] > 0:
                    input_devices.append((i, info['name']))
            except Exception as e:
                print(f"  ⚠️ 读取设备 {i} 失败: {e}\n")
        
        # 显示默认设备
        try:
            default_input = p.get_default_input_device_info()
            print(f"✅ 默认输入设备: [{default_input['index']}] {default_input['name']}")
        except Exception as e:
            print(f"❌ 没有默认输入设备: {e}")
        
        try:
            default_output = p.get_default_output_device_info()
            print(f"✅ 默认输出设备: [{default_output['index']}] {default_output['name']}")
        except Exception as e:
            print(f"❌ 没有默认输出设备: {e}")
        
        print("\n" + "="*70)
        
        # 显示可用的输入设备
        if input_devices:
            print(f"\n🎤 可用的输入设备 (共 {len(input_devices)} 个):")
            for idx, name in input_devices:
                print(f"   [{idx}] {name}")
            print(f"\n💡 在 asr_node.py 中使用设备，运行时添加参数:")
            print(f"   python3 asr_node.py")
            print(f"   或使用 ROS2 参数:")
            print(f"   ros2 run <package> asr_node --ros-args -p audio_device_index:={input_devices[0][0]}")
        else:
            print("\n❌ 没有找到输入设备 (麦克风)")
        
        print()
        p.terminate()
        return len(input_devices) > 0
        
    except Exception as e:
        print(f"\n❌ PyAudio 初始化失败: {e}")
        print("\n可能的解决方案:")
        print("1. 确保 portaudio19-dev 已安装: sudo apt-get install portaudio19-dev")
        print("2. 重新安装 PyAudio: pip install --upgrade --force-reinstall pyaudio")
        return False

if __name__ == "__main__":
    success = test_audio_devices()
    sys.exit(0 if success else 1)

