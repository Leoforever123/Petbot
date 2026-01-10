#!/bin/bash
# Petbot 快速环境激活脚本
# 使用方法: source activate.sh

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# 激活虚拟环境
if [ -d ".venv" ]; then
    source .venv/bin/activate
    echo "✅ Python 虚拟环境已激活"
else
    echo "⚠️  虚拟环境未找到，请先运行 ./setup.sh"
fi

# 加载 ROS2
if [ -f "/opt/ros/jazzy/setup.bash" ]; then
    source /opt/ros/jazzy/setup.bash
    echo "✅ ROS2 环境已加载"
fi

# 加载服务定义
if [ -f "install/setup.bash" ]; then
    source install/setup.bash
    echo "✅ ROS2 服务定义已加载"
fi

# 加载环境变量
if [ -f ".env" ]; then
    set -a
    source .env
    set +a
    echo "✅ 环境变量已加载"
fi

echo ""
echo "🚀 Petbot 环境已就绪！"
echo ""
echo "快速启动命令："
echo "  ./start_all.sh              # 启动所有组件"
echo "  ./start_all.sh --no-head    # 不启动头部控制"
echo "  python3 test/test_agent_interactive.py  # 测试 Agent"
echo ""
