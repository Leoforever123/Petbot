#!/usr/bin/env python3
"""
Chat Agent 测试脚本
测试 LangGraph Agent 和天气查询功能（无需ROS2）
"""

import os
import sys

# 添加父目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'nodes', 'chat'))

from agent import ChatAgent
from weather_tool import WeatherTool


def print_separator(title="", char="=", width=60):
    """打印分隔线"""
    if title:
        padding = (width - len(title) - 2) // 2
        print(f"{char * padding} {title} {char * padding}")
    else:
        print(char * width)


def test_weather_tool():
    """测试天气查询工具"""
    print_separator("测试天气查询工具")
    print()
    
    tool = WeatherTool()
    
    # 测试城市列表
    cities = ["北京", "上海", "深圳", "广州"]
    
    for city in cities:
        print(f"🌤️  查询 {city} 天气...")
        result = tool.get_weather(city)
        
        if result['success']:
            print(f"   ✅ {result['message']}")
        else:
            print(f"   ❌ {result['message']}")
        print()
    
    print_separator()
    print()


def test_agent_basic():
    """测试基础对话"""
    print_separator("测试基础对话")
    print()
    
    agent = ChatAgent()
    
    # 测试对话列表
    conversations = [
        "你好",
        "介绍一下 Python",
        "它有什么特点",
    ]
    
    for user_msg in conversations:
        print(f"👤 用户: {user_msg}")
        response = agent.chat(user_msg)
        print(f"🤖 AI: {response}")
        print()
    
    print_separator()
    print()


def test_agent_weather():
    """测试天气查询对话"""
    print_separator("测试天气查询对话")
    print()
    
    agent = ChatAgent()
    
    # 测试天气相关对话
    weather_questions = [
        "北京天气怎么样",
        "上海的天气呢",
        "深圳今天热吗",
    ]
    
    for user_msg in weather_questions:
        print(f"👤 用户: {user_msg}")
        response = agent.chat(user_msg)
        print(f"🤖 AI: {response}")
        print()
    
    print_separator()
    print()


def test_agent_context():
    """测试上下文记忆"""
    print_separator("测试上下文记忆")
    print()
    
    agent = ChatAgent()
    history = []
    
    # 测试上下文对话
    conversations = [
        ("什么是机器学习", None),
        ("它有哪些应用", "history"),  # 应该基于上一个问题回答
        ("能举个例子吗", "history"),   # 应该基于前面的对话
    ]
    
    for user_msg, use_history in conversations:
        print(f"👤 用户: {user_msg}")
        
        if use_history == "history":
            response = agent.chat(user_msg, history)
        else:
            response = agent.chat(user_msg)
        
        print(f"🤖 AI: {response}")
        print()
        
        # 更新历史
        from langchain_core.messages import HumanMessage, AIMessage
        history.append(HumanMessage(content=user_msg))
        history.append(AIMessage(content=response))
    
    print_separator()
    print()


def interactive_test():
    """交互式测试"""
    print_separator("交互式测试模式")
    print()
    print("现在可以与 Agent 自由对话了！")
    print("输入 'quit' 或 'exit' 退出")
    print("输入 'clear' 清除对话历史")
    print()
    print_separator()
    print()
    
    agent = ChatAgent()
    history = []
    
    while True:
        try:
            user_input = input("👤 你: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("\n👋 再见！")
                break
            
            if user_input.lower() == 'clear':
                history = []
                print("🔄 对话历史已清除\n")
                continue
            
            # 获取回复
            response = agent.chat(user_input, history)
            print(f"🤖 AI: {response}\n")
            
            # 更新历史
            from langchain_core.messages import HumanMessage, AIMessage
            history.append(HumanMessage(content=user_input))
            history.append(AIMessage(content=response))
            
        except KeyboardInterrupt:
            print("\n\n👋 再见！")
            break
        except Exception as e:
            print(f"\n❌ 错误: {e}\n")


def main():
    """主函数"""
    print()
    print("╔════════════════════════════════════════════════════════╗")
    print("║         Chat Agent 测试工具                            ║")
    print("╚════════════════════════════════════════════════════════╝")
    print()
    
    # 检查环境变量
    if not os.getenv('DEEPSEEK_API_KEY'):
        print("❌ 错误: 未找到 DEEPSEEK_API_KEY 环境变量")
        print()
        print("请先配置 API 密钥：")
        print("1. 在项目根目录创建 .env 文件")
        print("2. 添加: DEEPSEEK_API_KEY=your-key")
        print()
        print("或者运行: export DEEPSEEK_API_KEY=your-key")
        print()
        return
    
    print("选择测试模式：")
    print()
    print("1. 测试天气查询工具")
    print("2. 测试基础对话")
    print("3. 测试天气查询对话")
    print("4. 测试上下文记忆")
    print("5. 交互式测试（自由对话）")
    print("6. 运行所有测试")
    print("0. 退出")
    print()
    
    try:
        choice = input("请选择 (0-6): ").strip()
        print()
        
        if choice == '1':
            test_weather_tool()
        elif choice == '2':
            test_agent_basic()
        elif choice == '3':
            test_agent_weather()
        elif choice == '4':
            test_agent_context()
        elif choice == '5':
            interactive_test()
        elif choice == '6':
            test_weather_tool()
            test_agent_basic()
            test_agent_weather()
            test_agent_context()
        elif choice == '0':
            print("👋 再见！")
        else:
            print("❌ 无效的选择")
            
    except KeyboardInterrupt:
        print("\n\n👋 测试中断")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()


