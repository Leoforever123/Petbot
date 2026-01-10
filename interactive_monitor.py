#!/usr/bin/env python3
"""
Interactive Monitor - 交互式监控脚本
提供简洁的用户交互界面，隐藏复杂的日志信息
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import sys
import time
from datetime import datetime


class InteractiveMonitor(Node):
    """交互式监控节点 - 提供用户友好的命令行界面"""
    
    def __init__(self):
        super().__init__('interactive_monitor')
        
        # 状态标志
        self.system_ready = False
        self.is_listening = True
        self.ai_is_thinking = False
        self.tts_is_playing = False
        
        # 订阅 ASR 结果
        self.asr_subscription = self.create_subscription(
            String,
            '/asr_result',
            self.asr_callback,
            10
        )
        
        # 订阅 AI 思考状态
        self.ai_thinking_subscription = self.create_subscription(
            String,
            '/ai_thinking',
            self.ai_thinking_callback,
            10
        )
        
        # 订阅 TTS 生命周期
        self.tts_life_subscription = self.create_subscription(
            String,
            '/tts_life',
            self.tts_life_callback,
            10
        )
        
        # 创建一个发布者用于接收 Chat 节点的回复（如果需要）
        # 这里我们通过修改 chat_node 来发布简洁的回复信息
        self.chat_response_subscription = self.create_subscription(
            String,
            '/chat_response',
            self.chat_response_callback,
            10
        )
        
        # 等待一小段时间让所有节点启动
        self.create_timer(3.0, self.check_system_ready)
        
    def check_system_ready(self):
        """检查系统是否就绪"""
        if not self.system_ready:
            self.system_ready = True
            self.print_separator()
            print("🎤 系统已就绪，请开始说话...")
            self.print_separator()
            print()
    
    def print_separator(self):
        """打印分隔线"""
        print("=" * 60)
    
    def get_timestamp(self):
        """获取时间戳"""
        return datetime.now().strftime("%H:%M:%S")
    
    def asr_callback(self, msg):
        """ASR 结果回调 - 显示用户说的话"""
        user_text = msg.data
        timestamp = self.get_timestamp()
        print(f"\n[{timestamp}] 👤 收到语音: {user_text}")
    
    def ai_thinking_callback(self, msg):
        """AI 思考状态回调"""
        timestamp = self.get_timestamp()
        if msg.data == 'start':
            self.ai_is_thinking = True
            print(f"[{timestamp}] 🤔 AI正在思考中...")
        elif msg.data == 'end':
            self.ai_is_thinking = False
    
    def chat_response_callback(self, msg):
        """Chat 响应回调 - 显示 AI 的回复"""
        ai_response = msg.data
        timestamp = self.get_timestamp()
        print(f"[{timestamp}] 🤖 AI回复: {ai_response}")
    
    def tts_life_callback(self, msg):
        """TTS 生命周期回调"""
        timestamp = self.get_timestamp()
        if msg.data == 'start':
            self.tts_is_playing = True
            print(f"[{timestamp}] 🔊 正在播放语音...")
        elif msg.data == 'end':
            self.tts_is_playing = False
            print(f"[{timestamp}] ✅ 语音播放完成")
            print()
            print("💬 继续说话或按 Ctrl+C 退出")
            self.print_separator()
            print()


def main(args=None):
    """主函数"""
    rclpy.init(args=args)
    
    print("\n")
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 15 + "🤖 PetBot 交互式界面" + " " * 18 + "║")
    print("╚" + "═" * 58 + "╝")
    print()
    print("⏳ 正在等待所有节点启动...")
    
    try:
        monitor = InteractiveMonitor()
        rclpy.spin(monitor)
    except KeyboardInterrupt:
        print("\n")
        print("=" * 60)
        print("👋 再见！PetBot 交互界面已关闭")
        print("=" * 60)
    finally:
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()

