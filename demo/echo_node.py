#!/usr/bin/env python3
"""
Echo Node: Bridges ASR and TTS to create a voice echo system.
Listens to ASR results and speaks them back via TTS.
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from service_define.srv import SetString
import time


class EchoNode(Node):
    """
    Simple echo node that listens to ASR results and speaks them back via TTS.
    """
    
    def __init__(self):
        super().__init__('echo_node')
        self.get_logger().info("Initializing Echo Node...")
        
        # State management
        self.is_processing = False
        self.last_text = ""
        self.last_time = time.time()
        self.tts_service_ready = False
        
        # Subscribe to ASR results with explicit QoS
        from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
        
        qos_profile = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            history=HistoryPolicy.KEEP_LAST,
            depth=10
        )
        
        self.asr_subscription = self.create_subscription(
            String,
            '/asr_result',
            self.asr_callback,
            qos_profile
        )
        self.get_logger().info("Subscribed to '/asr_result' topic with RELIABLE QoS")
        
        # Create TTS service client (use tts_service_wait for sequential processing)
        self.tts_client = self.create_client(SetString, 'tts_service_wait')
        
        # Check TTS service availability (non-blocking)
        self.get_logger().info("Checking TTS service availability...")
        if self.tts_client.service_is_ready():
            self.tts_service_ready = True
            self.get_logger().info("TTS service is ready!")
        else:
            self.get_logger().warn("TTS service not yet available. Will retry when receiving ASR results.")
        
        self.get_logger().info("Echo Node initialization complete! Speak something and I'll echo it back.")
    
    def asr_callback(self, msg):
        """
        Callback function when ASR result is received.
        Sends the recognized text to TTS service.
        
        Args:
            msg (String): The recognized text from ASR
        """
        self.get_logger().info(f"[DEBUG] ASR callback triggered! Received message: '{msg.data}'")
        
        recognized_text = msg.data.strip()
        
        if not recognized_text:
            self.get_logger().warn("Received empty ASR result, skipping...")
            return
        
        # Prevent duplicate processing
        current_time = time.time()
        if recognized_text == self.last_text and (current_time - self.last_time) < 2.0:
            self.get_logger().info(f"Duplicate text detected within 2s, skipping: '{recognized_text}'")
            return
        
        # Prevent concurrent processing
        if self.is_processing:
            self.get_logger().warn(f"Still processing previous request, skipping: '{recognized_text}'")
            return
        
        # Wait for TTS service if not ready yet
        if not self.tts_service_ready:
            self.get_logger().info("Waiting for TTS service to become available...")
            max_wait = 10  # Maximum 10 seconds
            for i in range(max_wait):
                if self.tts_client.wait_for_service(timeout_sec=1.0):
                    self.tts_service_ready = True
                    self.get_logger().info("TTS service is now ready!")
                    break
            
            if not self.tts_service_ready:
                self.get_logger().error("TTS service still not available after waiting. Skipping this request.")
                return
        
        self.last_text = recognized_text
        self.last_time = current_time
        self.is_processing = True
        
        self.get_logger().info(f"ASR recognized: '{recognized_text}'")
        self.get_logger().info(f"Echoing back: '{recognized_text}'")
        
        # Call TTS service to speak the recognized text
        self.call_tts_service(recognized_text)
    
    def call_tts_service(self, text):
        """
        Call the TTS service to speak the given text.
        
        Args:
            text (str): Text to be spoken
        """
        request = SetString.Request()
        request.data = text
        
        # Call service asynchronously
        future = self.tts_client.call_async(request)
        future.add_done_callback(self.tts_response_callback)
    
    def tts_response_callback(self, future):
        """
        Callback for TTS service response.
        
        Args:
            future: The future object containing the service response
        """
        try:
            response = future.result()
            if response.success:
                self.get_logger().info("TTS service call successful")
            else:
                self.get_logger().warn("TTS service call returned failure")
        except Exception as e:
            self.get_logger().error(f"TTS service call failed: {e}")
        finally:
            # Reset processing flag
            self.is_processing = False


def main(args=None):
    rclpy.init(args=args)
    
    echo_node = EchoNode()
    
    try:
        rclpy.spin(echo_node)
    except KeyboardInterrupt:
        echo_node.get_logger().info("Keyboard Interrupt. Shutting down Echo Node...")
    finally:
        echo_node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()

