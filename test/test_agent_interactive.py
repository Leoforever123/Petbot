#!/usr/bin/env python3
"""
Agent 交互测试脚本
简单的命令行界面测试 LangGraph Agent 功能

使用方法：
    python3 test/test_agent_interactive.py
"""

import os
import sys
from pathlib import Path

# 添加父目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "nodes" / "chat"))

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, AIMessage

# 加载环境变量
load_dotenv()

# 导入 Agent
try:
    from agent import ChatAgent
    from weather_tool import WeatherTool
except ImportError as e:
    print(f"❌ 导入失败: {e}")
    print("请确保已安装所有依赖: pip install langgraph langchain-openai langchain-core requests python-dotenv")
    sys.exit(1)


def print_banner():
    """打印欢迎横幅"""
    print("\n" + "="*60)
    print("         🤖 LangGraph Agent 交互测试")
    print("="*60)
    print()
    print("功能：")
    print("  • 智能对话（Deepseek LLM）")
    print("  • 天气查询（高德地图API）")
    print("  • 上下文记忆")
    print()
    print("命令：")
    print("  - 输入消息开始对话")
    print("  - 'quit' 或 'exit' - 退出程序")
    print("  - 'clear' - 清除对话历史")
    print("  - 'history' - 查看对话历史")
    print("  - 'weather' - 测试天气查询")
    print("  - 'help' - 显示帮助")
    print()
    print("="*60)
    print()


def print_help():
    """打印帮助信息"""
    print("\n📖 帮助信息")
    print("-" * 60)
    print("示例对话：")
    print("  你: 你好")
    print("  AI: 你好！有什么可以帮你的吗？")
    print()
    print("  你: 北京天气怎么样")
    print("  AI: 北京当前天气晴，气温25度，南风3级")
    print()
    print("  你: 上海呢")
    print("  AI: （基于上下文回答上海天气）")
    print("-" * 60)
    print()


def test_weather_tool():
    """测试天气查询工具"""
    print("\n🌤️  测试天气查询工具")
    print("-" * 60)
    
    tool = WeatherTool()
    
    test_cities = ["北京", "上海", "深圳"]
    
    for city in test_cities:
        print(f"查询 {city} 天气...")
        result = tool.get_weather(city)
        
        if result['success']:
            print(f"  ✅ {result['message']}")
        else:
            print(f"  ❌ {result['message']}")
    
    print("-" * 60)
    print()


def show_history(history):
    """显示对话历史"""
    if not history:
        print("\n📭 对话历史为空")
        return
    
    print("\n📜 对话历史")
    print("-" * 60)
    for i, msg in enumerate(history, 1):
        if isinstance(msg, HumanMessage):
            print(f"[{i}] 👤 你: {msg.content}")
        elif isinstance(msg, AIMessage):
            print(f"[{i}] 🤖 AI: {msg.content}")
    print("-" * 60)
    print()


def main():
    """主函数"""
    # 检查环境变量
    if not os.getenv('DEEPSEEK_API_KEY'):
        print("❌ 错误: 未找到 DEEPSEEK_API_KEY 环境变量")
        print()
        print("请设置 API 密钥：")
        print("1. 在项目根目录创建 .env 文件")
        print("2. 添加: DEEPSEEK_API_KEY=your-key")
        print()
        print("或者运行: export DEEPSEEK_API_KEY=your-key")
        return
    
    # 打印欢迎信息
    print_banner()
    
    # 初始化 Agent
    try:
        print("🔄 正在初始化 Agent...")
        agent = ChatAgent()
        print("✅ Agent 初始化成功！")
        print()
    except Exception as e:
        print(f"❌ Agent 初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 对话历史
    history = []
    
    # 主循环
    print("💬 开始对话（输入 'help' 查看帮助）")
    print()
    
    while True:
        try:
            # 获取用户输入
            user_input = input("👤 你: ").strip()
            
            if not user_input:
                continue
            
            # 处理命令
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("\n👋 再见！")
                break
            
            elif user_input.lower() == 'help':
                print_help()
                continue
            
            elif user_input.lower() == 'clear':
                history = []
                print("\n🔄 对话历史已清除")
                print()
                continue
            
            elif user_input.lower() == 'history':
                show_history(history)
                continue
            
            elif user_input.lower() == 'weather':
                test_weather_tool()
                continue
            
            # 正常对话
            print("🤖 AI: ", end="", flush=True)
            
            try:
                # 调用 Agent
                response = agent.chat(user_input, history)
                print(response)
                print()
                
                # 更新历史
                history.append(HumanMessage(content=user_input))
                history.append(AIMessage(content=response))
                
                # 限制历史长度（保留最近10轮）
                if len(history) > 20:
                    history = history[-20:]
                
            except Exception as e:
                print(f"\n❌ 对话出错: {e}")
                print()
                import traceback
                traceback.print_exc()
        
        except KeyboardInterrupt:
            print("\n\n👋 检测到中断信号，正在退出...")
            break
        
        except Exception as e:
            print(f"\n❌ 发生错误: {e}")
            import traceback
            traceback.print_exc()


if __name__ == '__main__':
    main()

