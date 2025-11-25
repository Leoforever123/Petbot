#!/usr/bin/env python3
"""
Quick test script to verify ROS 2 topic connection between ASR and Echo nodes
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import time


class TopicTester(Node):
    """
    Simple test node to verify topic connections
    """
    
    def __init__(self):
        super().__init__('topic_tester')
        
        # Subscribe to ASR results
        self.asr_subscription = self.create_subscription(
            String,
            '/asr_result',
            self.asr_callback,
            10
        )
        
        # Publisher to simulate ASR
        self.test_publisher = self.create_publisher(String, '/asr_result', 10)
        
        self.get_logger().info("Topic Tester initialized")
        self.get_logger().info("Subscribed to /asr_result")
        self.get_logger().info("Publishing test messages...")
        
        # Publish some test messages
        self.timer = self.create_timer(2.0, self.publish_test_message)
        self.counter = 0
    
    def asr_callback(self, msg):
        """Callback when receiving ASR messages"""
        self.get_logger().info(f"✅ RECEIVED MESSAGE: '{msg.data}'")
    
    def publish_test_message(self):
        """Publish test message"""
        self.counter += 1
        msg = String()
        msg.data = f"测试消息 {self.counter}"
        self.test_publisher.publish(msg)
        self.get_logger().info(f"📤 PUBLISHED: '{msg.data}'")
        
        if self.counter >= 5:
            self.get_logger().info("Test complete. Press Ctrl+C to exit.")
            self.timer.cancel()


def main(args=None):
    rclpy.init(args=args)
    
    tester = TopicTester()
    
    try:
        rclpy.spin(tester)
    except KeyboardInterrupt:
        tester.get_logger().info("Shutting down...")
    finally:
        tester.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()

