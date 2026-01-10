#!/usr/bin/env python3
"""
LangGraph Agent - 使用 Deepseek 和天气查询工具的智能对话代理
"""

import os
import operator
from typing import Annotated, TypedDict, Sequence
from dotenv import load_dotenv

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage, SystemMessage
import logging
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_core.tools import tool

from weather_tool import query_weather as weather_query_func

load_dotenv()


# 定义Agent状态
class AgentState(TypedDict):
    """Agent的状态定义"""
    messages: Annotated[Sequence[BaseMessage], operator.add]


# 定义工具
@tool
def query_weather(city: str) -> str:
    """
    查询指定城市的天气信息
    
    Args:
        city: 城市名称，如：北京、上海、深圳等
        
    Returns:
        天气信息的文字描述
    """
    return weather_query_func(city)


@tool
def remember_face(person_name: str) -> str:
    """
    记住用户的脸部特征，用于人脸识别
    
    当用户想让系统记住他们的身份时使用此工具。
    用户可能会说：
    - "记住我的脸，我是XXX"
    - "帮我记住我，我叫XXX"  
    - "你能记住我吗？我的名字是XXX"
    - "把我的脸存下来，我叫XXX"
    - "请记一下我，我是XXX"
    等各种表达方式。
    
    Args:
        person_name: 用户的名字，例如：张三、李四、王骏达
        
    Returns:
        操作结果消息。如果成功，返回"好的，我已经记住{person_name}的脸了！"
        如果失败，返回相应的错误提示。
        
    Note:
        这个工具会返回一个特殊标记，实际的人脸捕获操作
        会在chat_node中处理（调用face detection服务），然后
        将实际结果替换工具返回值，让Agent生成最终回复。
    """
    # 返回特殊标记，chat_node会检测并处理，然后替换为实际结果
    return f"__REMEMBER_FACE_REQUEST__|{person_name}"


class ChatAgent:
    """基于LangGraph的对话代理"""
    
    def __init__(self):
        """初始化Agent"""
        # 加载API密钥
        api_key = os.getenv('DEEPSEEK_API_KEY')
        if not api_key:
            raise ValueError("未找到 DEEPSEEK_API_KEY 环境变量")
        
        # 初始化LLM（使用Deepseek）
        self.llm = ChatOpenAI(
            model="deepseek-chat",
            api_key=api_key,
            base_url="https://api.deepseek.com",
            temperature=0.7,
            max_tokens=150
        )
        
        # 定义工具列表
        self.tools = [query_weather, remember_face]
        
        # 绑定工具到LLM
        self.llm_with_tools = self.llm.bind_tools(self.tools)
        
        # 创建工具节点
        self.tool_node = ToolNode(self.tools)
        
        # 构建图
        self.graph = self._build_graph()
        
        # 系统提示词
        self.system_prompt = """你是一个智能语音助手。请遵循以下规则：

1. 回答要简洁，每次回答控制在30字以内
2. 用口语化的方式回答，就像面对面聊天
3. 如果问题复杂，只说最关键的信息
4. 避免使用列表、分点等书面语格式
5. 回答要自然流畅，适合语音播放

工具使用规则：
6. 当用户询问天气时，使用 query_weather 工具查询
7. 当用户想让你记住他们的脸/身份时，使用 remember_face 工具
   - 用户可能说"记住我"、"帮我记住"、"存下我的脸"等
   - 必须从用户的话中提取出他们的名字
   - 如果用户没说名字，询问"请问你叫什么名字？"
8. 工具查询结果直接转述，不要添加额外说明"""
    
    def _build_graph(self) -> StateGraph:
        """构建LangGraph图"""
        # 创建图
        workflow = StateGraph(AgentState)
        
        # 添加节点
        workflow.add_node("agent", self._call_model)
        workflow.add_node("tools", self.tool_node)
        
        # 设置入口
        workflow.set_entry_point("agent")
        
        # 添加条件边：根据agent的输出决定是调用工具还是结束
        workflow.add_conditional_edges(
            "agent",
            self._should_continue,
            {
                "continue": "tools",
                "end": END
            }
        )
        
        # 从工具节点返回agent节点
        workflow.add_edge("tools", "agent")
        
        # 编译图
        return workflow.compile()
    
    def _call_model(self, state: AgentState) -> AgentState:
        """调用LLM"""
        messages = list(state["messages"])
        
        # 确保第一条消息是系统提示
        if not messages or not isinstance(messages[0], SystemMessage):
            messages = [SystemMessage(content=self.system_prompt)] + messages
        
        # 调用LLM
        response = self.llm_with_tools.invoke(messages)
        
        # 使用 operator.add，只返回新消息
        return {"messages": [response]}
    
    def _should_continue(self, state: AgentState) -> str:
        """判断是否需要继续调用工具"""
        messages = state["messages"]
        last_message = messages[-1]
        
        # 如果LLM调用了工具，继续执行
        if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
            return "continue"
        
        # 否则结束
        return "end"
    
    def chat(self, user_message: str, history: list = None) -> str:
        """
        与Agent对话
        
        Args:
            user_message: 用户消息
            history: 对话历史（可选）
            
        Returns:
            Agent的回复
        """
        # 构建消息列表
        messages = []
        
        # 添加历史消息
        if history:
            messages.extend(history)
        
        # 添加当前用户消息
        messages.append(HumanMessage(content=user_message))
        
        # 调用图
        try:
            result = self.graph.invoke({"messages": messages})
            
            # 检查所有消息，查找工具调用结果
            tool_result_found = None
            for i, msg in enumerate(result["messages"]):
                # 检查是否是工具消息（工具执行的结果）
                if isinstance(msg, ToolMessage):
                    tool_result = msg.content
                    print(f"[DEBUG] 找到工具消息 [{i}]: {tool_result}")
                    # 如果是 remember_face 工具的特殊标记，保存它
                    if tool_result.startswith("__REMEMBER_FACE_REQUEST__|"):
                        tool_result_found = tool_result
                        print(f"[DEBUG] ✅ 找到 remember_face 工具结果: {tool_result_found}")
                
                # 检查AI消息中是否有工具调用
                if isinstance(msg, AIMessage) and hasattr(msg, 'tool_calls') and msg.tool_calls:
                    for tool_call in msg.tool_calls:
                        tool_name = tool_call.get('name', '')
                        tool_args = tool_call.get('args', {})
                        print(f"[DEBUG] AI调用了工具: {tool_name}, 参数: {tool_args}")
            
            # 如果找到了工具结果，优先返回工具结果
            if tool_result_found:
                print(f"[DEBUG] 返回工具结果: {tool_result_found}")
                return tool_result_found
            
            # 获取最后的AI消息
            last_message = result["messages"][-1]
            
            if isinstance(last_message, AIMessage):
                content = last_message.content
                print(f"[DEBUG] 返回AI消息内容: {content}")
                # 检查AI回复中是否提到了工具调用（但工具结果被忽略了）
                # 如果AI说"我会记住你的脸"但没有调用工具，说明工具调用可能失败了
                if "记住" in content and "脸" in content and not tool_result_found:
                    print(f"[WARNING] AI说会记住，但没有找到工具调用结果！")
                return content
            else:
                return "抱歉，我遇到了一些问题。"
                
        except Exception as e:
            print(f"Agent执行错误: {e}")
            import traceback
            traceback.print_exc()
            return "抱歉，我遇到了一些问题。"
    
    def get_conversation_history(self, messages: list) -> list:
        """
        从图的输出中提取对话历史
        
        Args:
            messages: 消息列表
            
        Returns:
            简化的对话历史
        """
        history = []
        for msg in messages:
            if isinstance(msg, (HumanMessage, AIMessage)):
                history.append(msg)
        return history[-10:]  # 保持最近10轮对话


# 测试代码
if __name__ == '__main__':
    print("初始化 ChatAgent...")
    agent = ChatAgent()
    
    print("\n" + "="*60)
    print("测试对话")
    print("="*60)
    
    # 测试普通对话
    print("\n用户: 你好")
    response = agent.chat("你好")
    print(f"Agent: {response}")
    
    # 测试天气查询
    print("\n用户: 北京天气怎么样")
    response = agent.chat("北京天气怎么样")
    print(f"Agent: {response}")
    
    # 测试带历史的对话
    print("\n用户: 上海呢")
    history = [
        HumanMessage(content="北京天气怎么样"),
        AIMessage(content=response)
    ]
    response = agent.chat("上海呢", history)
    print(f"Agent: {response}")
    
    print("\n测试完成!")


