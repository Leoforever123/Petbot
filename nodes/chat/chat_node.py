#!/usr/bin/env python3
"""
Chat Node: AI-powered conversation system using LangGraph + Deepseek
带天气查询功能的智能对话节点

功能：
- 集成 LangGraph Agent
- 支持天气查询（高德地图API）
- Deepseek LLM 对话
- 与 ASR/TTS 集成
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from service_define.srv import SetString
import time
import os
import sys
import re
from dotenv import load_dotenv

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(__file__))

from agent import ChatAgent


class ChatNode(Node):
    """
    AI chat node with LangGraph agent
    集成了工具调用能力的智能对话节点
    """
    
    def __init__(self):
        super().__init__('chat_node')
        self.get_logger().info("=" * 60)
        self.get_logger().info("🤖 Initializing Enhanced Chat Node with LangGraph")
        self.get_logger().info("=" * 60)
        
        # Load environment variables
        load_dotenv()
        
        # 检查必要的API密钥
        self._check_api_keys()
        
        # Initialize LangGraph Agent
        try:
            self.get_logger().info("正在初始化 LangGraph Agent...")
            self.agent = ChatAgent()
            self.get_logger().info("✅ LangGraph Agent 初始化成功")
        except Exception as e:
            self.get_logger().error(f"❌ Agent 初始化失败: {e}")
            raise
        
        # Conversation history (保持消息对象以支持工具调用)
        self.conversation_messages = []
        self.max_history = 10  # 保持最近10轮对话
        
        # State management
        self.is_processing = False
        self.last_text = ""
        self.last_time = time.time()
        self.tts_service_ready = False
        
        # Subscribe to ASR results
        self.asr_subscription = self.create_subscription(
            String,
            '/asr_result',
            self.asr_callback,
            10
        )
        self.get_logger().info("✅ 已订阅话题: /asr_result")
        
        # Create TTS service client
        self.tts_client = self.create_client(SetString, 'tts_service_wait')
        
        # Create face capture service client (for "remember my face" feature)
        self.face_capture_client = self.create_client(SetString, 'capture_face')
        self.face_capture_service_ready = False
        
        # Check face capture service
        if self.face_capture_client.service_is_ready():
            self.face_capture_service_ready = True
            self.get_logger().info("✅ 人脸截图服务已就绪")
        else:
            self.get_logger().warn("⚠️  人脸截图服务暂未就绪（可选功能）")
        
        # Publisher to signal when thinking (to pause ASR)
        self.thinking_publisher = self.create_publisher(String, '/ai_thinking', 10)
        
        # Publisher for user-friendly chat responses (for interactive monitor)
        self.chat_response_publisher = self.create_publisher(String, '/chat_response', 10)
        
        # Check TTS service availability
        self.get_logger().info("正在检查 TTS 服务...")
        if self.tts_client.service_is_ready():
            self.tts_service_ready = True
            self.get_logger().info("✅ TTS 服务已就绪")
        else:
            self.get_logger().warn("⚠️  TTS 服务暂未就绪（将在首次使用时等待）")
        
        self.get_logger().info("=" * 60)
        self.get_logger().info("✅ Enhanced Chat Node 启动成功！")
        self.get_logger().info("   - LangGraph Agent: ✓")
        self.get_logger().info("   - 天气查询工具: ✓")
        self.get_logger().info("   - Deepseek LLM: ✓")
        self.get_logger().info("   - 人脸记忆功能: ✓" if self.face_capture_service_ready else "   - 人脸记忆功能: ⚠️  (未启动face节点)")
        self.get_logger().info("=" * 60)
        self.get_logger().info("🎤 现在可以开始对话了！")
        self.get_logger().info("   💡 试试问：'北京天气怎么样'")
        self.get_logger().info("   📸 试试说：'记住我的脸，我是张三'")
        self.get_logger().info("=" * 60)
        # 输出就绪标志 - 用于启动脚本检测
        print("PETBOT_CHAT_READY", flush=True)
    
    def _check_api_keys(self):
        """检查必要的API密钥"""
        # 检查 Deepseek API Key
        deepseek_key = os.getenv('DEEPSEEK_API_KEY')
        if not deepseek_key:
            self.get_logger().error("❌ 未找到 DEEPSEEK_API_KEY!")
            self.get_logger().error("")
            self.get_logger().error("请使用以下方法之一设置：")
            self.get_logger().error("1. export DEEPSEEK_API_KEY=your_key")
            self.get_logger().error("2. 在 .env 文件中添加: DEEPSEEK_API_KEY=your_key")
            raise ValueError("Missing DEEPSEEK_API_KEY")
        
        self.get_logger().info(f"✅ Deepseek API Key: {deepseek_key[:8]}...{deepseek_key[-4:]}")
        
        # 检查高德地图 API Key（可选，用于天气查询）
        amap_key = os.getenv('AMAP_API_KEY')
        if amap_key:
            self.get_logger().info(f"✅ 高德地图 API Key: {amap_key[:8]}...{amap_key[-4:]}")
            self.get_logger().info("   天气查询功能已启用")
        else:
            self.get_logger().warn("⚠️  未配置 AMAP_API_KEY")
            self.get_logger().warn("   天气查询功能将不可用")
            self.get_logger().warn("   若需使用，请在 .env 中添加: AMAP_API_KEY=your_key")
    
    def asr_callback(self, msg):
        """
        ASR结果回调函数
        使用 LangGraph Agent 处理用户输入
        
        Args:
            msg (String): ASR识别的文本
        """
        recognized_text = msg.data.strip()
        
        if not recognized_text:
            return
        
        # Prevent duplicate processing
        current_time = time.time()
        if recognized_text == self.last_text and (current_time - self.last_time) < 3.0:
            self.get_logger().info(f"⏭️  重复输入，跳过: '{recognized_text}'")
            return
        
        # Prevent concurrent processing
        if self.is_processing:
            self.get_logger().warn(f"⏳ 正在处理上一个请求，跳过")
            return
        
        self.last_text = recognized_text
        self.last_time = current_time
        self.is_processing = True
        
        self.get_logger().info("")
        self.get_logger().info("─" * 60)
        self.get_logger().info(f"👤 用户: {recognized_text}")
        
        # Signal that we're thinking (to pause ASR if needed)
        self.thinking_publisher.publish(String(data='start'))
        
        # 传给 Agent 处理（包括记住人脸的请求）
        try:
            response_text = self.query_agent(recognized_text)
            
            # 检查是否是 remember_face 工具的返回（特殊标记）
            if response_text.startswith("__REMEMBER_FACE_REQUEST__|"):
                # 提取人名
                person_name = response_text.split("|")[1]
                self.get_logger().info("=" * 60)
                self.get_logger().info(f"🔧 检测到工具调用: remember_face")
                self.get_logger().info(f"📸 提取到人名: '{person_name}'")
                self.get_logger().info("=" * 60)
                
                # 调用实际的人脸捕获服务
                try:
                    capture_result = self.handle_remember_face(person_name)
                    
                    # 将服务执行结果作为Agent的最终回复
                    # 这样Agent可以基于这个结果生成自然语言回复
                    final_response = self.query_agent_with_context(
                        user_message=recognized_text,
                        tool_result=capture_result
                    )
                    
                    self.get_logger().info(f"🤖 AI: {final_response}")
                    self.get_logger().info("─" * 60)
                    self.get_logger().info("")
                    
                    # Publish response to interactive monitor
                    self.chat_response_publisher.publish(String(data=final_response))
                    
                    # Speak the response
                    self.speak_response(final_response)
                    
                except Exception as e:
                    self.get_logger().error(f"❌ 处理记忆人脸出错: {e}")
                    import traceback
                    self.get_logger().error(traceback.format_exc())
                    error_msg = "抱歉，记忆人脸功能出现了问题。"
                    self.chat_response_publisher.publish(String(data=error_msg))
                    self.speak_response(error_msg)
            else:
                # 正常的 Agent 回复
                self.get_logger().info(f"🤖 AI: {response_text}")
                self.get_logger().info("─" * 60)
                self.get_logger().info("")
                
                # Publish response to interactive monitor
                self.chat_response_publisher.publish(String(data=response_text))
                
                # Speak the response
                self.speak_response(response_text)
            
        except Exception as e:
            self.get_logger().error(f"❌ 对话过程出错: {e}")
            import traceback
            self.get_logger().error(traceback.format_exc())
            # Speak an error message
            self.speak_response("抱歉，我遇到了一些问题。")
        finally:
            self.thinking_publisher.publish(String(data='end'))
            self.is_processing = False
    
    def check_remember_face_command(self, text: str) -> str:
        """
        检查是否是"记住我的脸"命令，并提取人名
        
        支持的格式：
        - 记住我的脸，我是XXX
        - 记住我的脸我是XXX
        - 记住我我是XXX
        - 记住我叫XXX
        
        Args:
            text: 用户输入的文本
            
        Returns:
            人名（如果匹配），否则返回None
        """
        text = text.strip()
        
        # 定义多种匹配模式
        patterns = [
            r'记住我的脸[，,、 ]*我是(.+)',
            r'记住我的脸[，,、 ]*我叫(.+)',
            r'记住我[，,、 ]*我是(.+)',
            r'记住我[，,、 ]*我叫(.+)',
            r'记住我的脸(.+)',  # 最宽松的匹配
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                person_name = match.group(1).strip()
                # 清理可能的标点符号
                person_name = re.sub(r'[，,。.！!？?]', '', person_name).strip()
                if person_name:
                    return person_name
        
        return None
    
    def handle_remember_face(self, person_name: str) -> str:
        """
        处理"记住我的脸"命令，调用face capture服务
        
        Args:
            person_name: 要记住的人名
            
        Returns:
            给用户的响应消息
        """
        self.get_logger().info("=" * 60)
        self.get_logger().info(f"🔧 开始处理人脸记忆请求")
        self.get_logger().info(f"   人名: {person_name}")
        
        # 检查服务是否可用
        if not self.face_capture_service_ready:
            self.get_logger().warn("⏳ 人脸截图服务未就绪，尝试等待...")
            for i in range(5):
                if self.face_capture_client.wait_for_service(timeout_sec=1.0):
                    self.face_capture_service_ready = True
                    self.get_logger().info("✅ 人脸截图服务已连接")
                    break
            
            if not self.face_capture_service_ready:
                self.get_logger().error("❌ 人脸截图服务不可用")
                self.get_logger().info("=" * 60)
                return "抱歉，人脸识别节点没有启动，无法记住你的脸。"
        
        # 调用截图服务
        request = SetString.Request()
        request.data = person_name
        
        self.get_logger().info(f"🔄 正在调用 ROS2 服务: /capture_face")
        self.get_logger().info(f"   请求参数: person_name = '{person_name}'")
        
        try:
            # 同步调用服务
            future = self.face_capture_client.call_async(request)
            
            # 等待结果（最多20秒，给人脸检测、保存和重新加载足够时间）
            rclpy.spin_until_future_complete(self, future, timeout_sec=20.0)
            
            if future.done():
                response = future.result()
                self.get_logger().info(f"📥 收到服务响应:")
                self.get_logger().info(f"   success: {response.success}")
                
                if response.success:
                    self.get_logger().info(f"✅ 人脸保存成功！")
                    self.get_logger().info("=" * 60)
                    return f"好的，我已经记住 {person_name} 的脸了！"
                else:
                    # 从日志中判断错误类型（因为response没有message字段）
                    # 查看最近的face节点日志来判断错误类型
                    self.get_logger().error(f"❌ 人脸保存失败")
                    self.get_logger().info("=" * 60)
                    # 返回通用错误消息，具体错误已在face节点日志中记录
                    return "抱歉，记忆失败。请确保只有你一个人面对摄像头，并且光线充足。"
            else:
                self.get_logger().error("❌ 服务调用超时（20秒内未响应）")
                self.get_logger().info("=" * 60)
                # 即使超时，也可能已经保存成功了，检查一下文件是否存在
                import os
                from pathlib import Path
                known_faces_dir = Path(__file__).parent.parent.parent / "images" / "known_faces"
                expected_file = known_faces_dir / f"{person_name}.jpg"
                if expected_file.exists():
                    self.get_logger().warn(f"⚠️  虽然服务超时，但检测到文件已存在: {expected_file}")
                    return f"好的，我已经记住 {person_name} 的脸了！虽然响应有点慢，但已经保存成功了。"
                return "抱歉，人脸识别响应超时了，请再试一次。"
                
        except Exception as e:
            self.get_logger().error(f"❌ 调用人脸截图服务失败: {e}")
            self.get_logger().info("=" * 60)
            import traceback
            self.get_logger().error(traceback.format_exc())
            return "抱歉，记忆人脸时出现了问题。"
    
    def query_agent(self, user_message: str) -> str:
        """
        使用 LangGraph Agent 查询响应
        
        Args:
            user_message (str): 用户输入
            
        Returns:
            str: Agent的回复
        """
        self.get_logger().info("🔄 调用 LangGraph Agent...")
        
        try:
            # 使用 Agent 处理消息
            response = self.agent.chat(
                user_message, 
                history=self.conversation_messages
            )
            
            # 更新对话历史
            from langchain_core.messages import HumanMessage, AIMessage
            self.conversation_messages.append(HumanMessage(content=user_message))
            self.conversation_messages.append(AIMessage(content=response))
            
            # 限制历史长度
            if len(self.conversation_messages) > self.max_history * 2:
                self.conversation_messages = self.conversation_messages[-self.max_history * 2:]
            
            return response
            
        except Exception as e:
            self.get_logger().error(f"❌ Agent 查询失败: {e}")
            raise
    
    def query_agent_with_context(self, user_message: str, tool_result: str) -> str:
        """
        使用 LangGraph Agent 查询响应，并提供工具执行结果作为上下文
        
        用于工具调用后，让Agent基于工具结果生成自然语言回复
        
        Args:
            user_message (str): 用户输入
            tool_result (str): 工具执行的结果（用于remember_face工具）
            
        Returns:
            str: Agent的回复
        """
        self.get_logger().info("🔄 调用 LangGraph Agent（带工具结果上下文）...")
        
        try:
            # 构建包含工具结果的上下文消息
            # 告诉Agent工具已经执行完成，结果是什么
            context_message = f"用户说：{user_message}\n\n工具执行结果：{tool_result}\n\n请基于工具执行结果，用自然、友好的语言回复用户。"
            
            # 使用 Agent 处理消息
            response = self.agent.chat(
                context_message, 
                history=self.conversation_messages
            )
            
            # 更新对话历史（使用原始用户消息，而不是上下文消息）
            from langchain_core.messages import HumanMessage, AIMessage
            self.conversation_messages.append(HumanMessage(content=user_message))
            self.conversation_messages.append(AIMessage(content=response))
            
            # 限制历史长度
            if len(self.conversation_messages) > self.max_history * 2:
                self.conversation_messages = self.conversation_messages[-self.max_history * 2:]
            
            return response
            
        except Exception as e:
            self.get_logger().error(f"❌ Agent 查询失败: {e}")
            # 如果Agent处理失败，直接返回工具结果
            return tool_result
    
    def speak_response(self, text: str):
        """
        通过TTS服务播放回复
        
        Args:
            text (str): 要播放的文本
        """
        # Wait for TTS service if not ready
        if not self.tts_service_ready:
            self.get_logger().info("⏳ 等待 TTS 服务...")
            for i in range(10):
                if self.tts_client.wait_for_service(timeout_sec=1.0):
                    self.tts_service_ready = True
                    break
            
            if not self.tts_service_ready:
                self.get_logger().error("❌ TTS 服务不可用")
                return
        
        # Call TTS service
        request = SetString.Request()
        request.data = text
        
        try:
            future = self.tts_client.call_async(request)
            future.add_done_callback(self.tts_callback)
        except Exception as e:
            self.get_logger().error(f"❌ TTS 服务调用失败: {e}")
    
    def tts_callback(self, future):
        """TTS服务响应回调"""
        try:
            response = future.result()
            if response.success:
                self.get_logger().info("🔊 TTS 播放完成")
            else:
                self.get_logger().warn("⚠️  TTS 播放失败")
        except Exception as e:
            self.get_logger().error(f"❌ TTS 回调错误: {e}")


def main(args=None):
    """主函数"""
    # Load environment variables
    load_dotenv()
    
    rclpy.init(args=args)
    
    try:
        chat_node = ChatNode()
        rclpy.spin(chat_node)
    except KeyboardInterrupt:
        print("\n👋 正在关闭 Chat Node...")
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
