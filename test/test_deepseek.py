#!/usr/bin/env python3
"""
Test script to verify Deepseek API configuration
"""

import os
from openai import OpenAI
from dotenv import load_dotenv

print("=" * 60)
print("Deepseek API 测试")
print("=" * 60)

# Load environment variables
load_dotenv()

# Check for API key
api_key = os.getenv('DEEPSEEK_API_KEY')

if not api_key:
    print("\n❌ 错误: 未找到 DEEPSEEK_API_KEY")
    print("\n请在项目根目录创建 .env 文件并添加：")
    print("DEEPSEEK_API_KEY=your_api_key_here")
    print("\n或者运行：")
    print("export DEEPSEEK_API_KEY=your_api_key_here")
    exit(1)

print(f"\n✅ API Key 找到: {api_key[:8]}...{api_key[-4:]}")

# Initialize client
try:
    client = OpenAI(
        api_key=api_key,
        base_url="https://api.deepseek.com"
    )
    print("✅ Deepseek 客户端初始化成功")
except Exception as e:
    print(f"❌ 客户端初始化失败: {e}")
    exit(1)

# Test API call
print("\n发送测试消息到 Deepseek...")
print("问题: '你好，请用一句话介绍你自己'")

try:
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": "你是一个简洁的助手，每次回答不超过30字"},
            {"role": "user", "content": "你好，请用一句话介绍你自己"}
        ],
        max_tokens=150,
        temperature=0.7
    )
    
    answer = response.choices[0].message.content
    print(f"\n✅ API 调用成功！")
    print(f"回复: {answer}")
    
    # Show usage
    usage = response.usage
    print(f"\nToken 使用情况:")
    print(f"  输入: {usage.prompt_tokens} tokens")
    print(f"  输出: {usage.completion_tokens} tokens")
    print(f"  总计: {usage.total_tokens} tokens")
    
    # Estimate cost (approximate)
    cost = (usage.prompt_tokens * 0.001 + usage.completion_tokens * 0.002) / 1000
    print(f"  预估费用: ¥{cost:.6f}")
    
    print("\n" + "=" * 60)
    print("🎉 所有测试通过！您可以开始使用 AI 对话系统了")
    print("=" * 60)
    print("\n运行以下命令启动：")
    print("./start_chat_system.sh")
    
except Exception as e:
    print(f"\n❌ API 调用失败: {e}")
    print("\n可能的原因：")
    print("1. API Key 不正确")
    print("2. 网络连接问题")
    print("3. 账户余额不足")
    print("4. API 访问受限")
    print("\n请检查 Deepseek 控制台: https://platform.deepseek.com/")
    exit(1)

