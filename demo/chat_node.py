#!/usr/bin/env python3
"""
Chat Node: AI-powered conversation system using Deepseek.
Listens to ASR results, queries Deepseek LLM, and speaks responses via TTS.
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from service_define.srv import SetString
import time
import os
from openai import OpenAI
from dotenv import load_dotenv


class ChatNode(Node):
    """
    AI chat node that integrates ASR, Deepseek LLM, and TTS for natural conversations.
    """
    
    def __init__(self):
        super().__init__('chat_node')
        self.get_logger().info("Initializing Chat Node with Deepseek LLM...")
        
        # Load environment variables (won't override existing env vars)
        load_dotenv()
        
        # Initialize Deepseek client
        api_key = os.getenv('DEEPSEEK_API_KEY')
        if not api_key:
            self.get_logger().error("DEEPSEEK_API_KEY not found in environment variables!")
            self.get_logger().error("")
            self.get_logger().error("Please set it using one of these methods:")
            self.get_logger().error("1. Export in terminal: export DEEPSEEK_API_KEY=your_key")
            self.get_logger().error("2. Add to .env file: DEEPSEEK_API_KEY=your_key")
            self.get_logger().error("3. Add to shell config: ~/.bashrc or ~/.zshrc")
            raise ValueError("Missing DEEPSEEK_API_KEY")
        
        self.get_logger().info(f"Using API key: {api_key[:8]}...{api_key[-4:]}")
        
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com"
        )
        self.get_logger().info("Deepseek client initialized successfully")
        
        # Conversation history (keep last N messages for context)
        self.conversation_history = []
        self.max_history = 10  # Keep last 10 exchanges
        
        # System prompt to control response length and style
        self.system_prompt = (
            "你是一个智能语音助手。请遵循以下规则：\n"
            "1. 回答要简洁，每次回答控制在30字以内\n"
            "2. 用口语化的方式回答，就像面对面聊天\n"
            "3. 如果问题复杂，只说最关键的信息\n"
            "4. 避免使用列表、分点等书面语格式\n"
            "5. 回答要自然流畅，适合语音播放"
        )
        
        # State management
        self.is_processing = False
        self.last_text = ""
        self.last_time = time.time()
        self.tts_service_ready = False
        
        # Subscribe to ASR results
        # Use default QoS (10) to match ASR publisher
        self.asr_subscription = self.create_subscription(
            String,
            '/asr_result',
            self.asr_callback,
            10
        )
        self.get_logger().info("Subscribed to '/asr_result' topic")
        
        # Create TTS service client
        self.tts_client = self.create_client(SetString, 'tts_service_wait')
        
        # Publisher to signal when thinking (to pause ASR)
        self.thinking_publisher = self.create_publisher(String, '/ai_thinking', 10)
        
        # Check TTS service availability
        self.get_logger().info("Waiting for TTS service...")
        if self.tts_client.service_is_ready():
            self.tts_service_ready = True
            self.get_logger().info("TTS service is ready!")
        else:
            self.get_logger().warn("TTS service not available yet")
        
        self.get_logger().info("Chat Node ready! Start speaking to have a conversation.")
    
    def asr_callback(self, msg):
        """
        Callback when ASR result is received.
        Queries Deepseek and speaks the response.
        
        Args:
            msg (String): The recognized text from ASR
        """
        recognized_text = msg.data.strip()
        
        if not recognized_text:
            return
        
        # Prevent duplicate processing
        current_time = time.time()
        if recognized_text == self.last_text and (current_time - self.last_time) < 3.0:
            self.get_logger().info(f"Duplicate detected, skipping: '{recognized_text}'")
            return
        
        # Prevent concurrent processing
        if self.is_processing:
            self.get_logger().warn(f"Still processing previous request, skipping")
            return
        
        self.last_text = recognized_text
        self.last_time = current_time
        self.is_processing = True
        
        self.get_logger().info(f"User said: '{recognized_text}'")
        
        # Signal that we're thinking (to pause ASR if needed)
        self.thinking_publisher.publish(String(data='start'))
        
        # Query Deepseek
        try:
            response_text = self.query_deepseek(recognized_text)
            self.get_logger().info(f"AI response: '{response_text}'")
            
            # Speak the response
            self.speak_response(response_text)
            
        except Exception as e:
            self.get_logger().error(f"Error during conversation: {e}")
            # Speak an error message
            self.speak_response("抱歉，我遇到了一些问题。")
        finally:
            self.thinking_publisher.publish(String(data='end'))
            self.is_processing = False
    
    def query_deepseek(self, user_message: str) -> str:
        """
        Query Deepseek LLM with the user's message.
        
        Args:
            user_message (str): User's input text
            
        Returns:
            str: AI's response
        """
        self.get_logger().info("Querying Deepseek LLM...")
        
        # Add user message to history
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })
        
        # Prepare messages for API call
        messages = [
            {"role": "system", "content": self.system_prompt}
        ] + self.conversation_history[-self.max_history:]  # Keep recent history
        
        try:
            # Call Deepseek API
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=messages,
                max_tokens=150,  # Limit response length
                temperature=0.7,
                stream=False
            )
            
            assistant_message = response.choices[0].message.content.strip()
            
            # Add assistant response to history
            self.conversation_history.append({
                "role": "assistant",
                "content": assistant_message
            })
            
            # Trim history if too long
            if len(self.conversation_history) > self.max_history * 2:
                self.conversation_history = self.conversation_history[-self.max_history * 2:]
            
            return assistant_message
            
        except Exception as e:
            self.get_logger().error(f"Deepseek API error: {e}")
            raise
    
    def speak_response(self, text: str):
        """
        Send text to TTS service for speech output.
        
        Args:
            text (str): Text to be spoken
        """
        # Wait for TTS service if not ready
        if not self.tts_service_ready:
            self.get_logger().info("Waiting for TTS service...")
            for i in range(10):
                if self.tts_client.wait_for_service(timeout_sec=1.0):
                    self.tts_service_ready = True
                    break
            
            if not self.tts_service_ready:
                self.get_logger().error("TTS service unavailable")
                return
        
        # Call TTS service
        request = SetString.Request()
        request.data = text
        
        try:
            future = self.tts_client.call_async(request)
            future.add_done_callback(self.tts_callback)
        except Exception as e:
            self.get_logger().error(f"Failed to call TTS service: {e}")
    
    def tts_callback(self, future):
        """Callback for TTS service response"""
        try:
            response = future.result()
            if response.success:
                self.get_logger().info("TTS completed successfully")
            else:
                self.get_logger().warn("TTS reported failure")
        except Exception as e:
            self.get_logger().error(f"TTS service error: {e}")


def main(args=None):
    # Load environment variables
    load_dotenv()
    
    rclpy.init(args=args)
    
    try:
        chat_node = ChatNode()
        rclpy.spin(chat_node)
    except KeyboardInterrupt:
        print("\nShutting down Chat Node...")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()

