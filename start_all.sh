#!/bin/bash

#####################################################################
#                    Petbot 一键启动脚本                             #
#                                                                   #
# 功能：启动所有系统组件                                             #
#   1. 表情服务器 (Expression Server)                               #
#   2. 人脸识别节点 (Face Detection Node with Expression Control)   #
#   3. ASR 语音识别节点 (ASR Node)                                   #
#   4. TTS 语音合成节点 (TTS Node)                                   #
#   5. Chat 对话节点 (Enhanced Chat Node with LangGraph)            #
#   6. 头部跟踪节点 (Turn Head Node) [可选]                         #
#                                                                   #
# 使用方法：./start_all.sh [选项]                                   #
#   选项：                                                          #
#     --no-head    : 不启动头部跟踪                                 #
#     --no-tts     : 不启动TTS（测试模式）                          #
#     --no-asr     : 不启动ASR（测试模式）                          #
#     --no-expression : 不启动表情服务器                            #
#####################################################################

# 设置颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 脚本目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# 解析命令行参数
START_HEAD=true
START_TTS=true
START_ASR=true
START_EXPRESSION=true

for arg in "$@"; do
    case $arg in
        --no-head)
            START_HEAD=false
            shift
            ;;
        --no-tts)
            START_TTS=false
            shift
            ;;
        --no-asr)
            START_ASR=false
            shift
            ;;
        --no-expression)
            START_EXPRESSION=false
            shift
            ;;
        *)
            ;;
    esac
done

# 打印标题
echo -e "${BLUE}"
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                    Petbot 一键启动脚本                          ║"
echo "║                                                                ║"
echo "║             智能桌面机器人 - 完整系统启动                       ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo ""

# 检查虚拟环境
if [ -d ".venv" ]; then
    echo -e "${GREEN}✓${NC} 发现虚拟环境，正在激活..."
    source .venv/bin/activate
else
    echo -e "${YELLOW}⚠${NC}  未发现虚拟环境，使用系统 Python"
fi

# 检查环境变量
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  步骤 1/7: 检查配置"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ -f ".env" ]; then
    echo -e "${GREEN}✓${NC} 发现 .env 配置文件"
    source .env
else
    echo -e "${YELLOW}⚠${NC}  未发现 .env 文件"
    if [ -f "env.example" ]; then
        echo -e "${BLUE}ℹ${NC}  可以复制 env.example 为 .env 并配置"
        echo "   cp env.example .env"
    fi
fi

# 检查 API Key
if [ -z "$DEEPSEEK_API_KEY" ]; then
    echo -e "${RED}✗${NC} 错误: DEEPSEEK_API_KEY 未配置"
    echo ""
    echo "请配置 API 密钥："
    echo "  1. 编辑 .env 文件"
    echo "  2. 添加: DEEPSEEK_API_KEY=sk-your-key"
    echo ""
    echo "或者临时设置："
    echo "  export DEEPSEEK_API_KEY=sk-your-key"
    echo "  ./start_all.sh"
    exit 1
else
    echo -e "${GREEN}✓${NC} Deepseek API Key: ${DEEPSEEK_API_KEY:0:8}...${DEEPSEEK_API_KEY: -4}"
fi

if [ -n "$AMAP_API_KEY" ]; then
    echo -e "${GREEN}✓${NC} 高德地图 API Key: ${AMAP_API_KEY:0:8}...${AMAP_API_KEY: -4}"
    echo -e "   ${GREEN}天气查询功能已启用${NC}"
else
    echo -e "${YELLOW}⚠${NC}  高德地图 API Key 未配置（天气查询不可用）"
fi

# 数组存储进程PID
declare -a PIDS=()
declare -a NAMES=()

# 清理函数
cleanup() {
    echo ""
    echo -e "${YELLOW}正在关闭所有节点...${NC}"
    for i in "${!PIDS[@]}"; do
        pid=${PIDS[$i]}
        name=${NAMES[$i]}
        if kill -0 $pid 2>/dev/null; then
            echo -e "  ${YELLOW}→${NC} 关闭 $name (PID: $pid)"
            kill $pid 2>/dev/null
        fi
    done
    echo -e "${GREEN}✓${NC} 所有节点已关闭"
    exit 0
}

# 捕获中断信号
trap cleanup SIGINT SIGTERM

# 启动表情服务器
if [ "$START_EXPRESSION" = true ]; then
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  步骤 2/7: 启动表情服务器"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    if pgrep -f "expression_server.py" > /dev/null; then
        echo -e "${YELLOW}⚠${NC}  表情服务器已在运行"
    else
        echo -e "${BLUE}→${NC} 启动表情服务器..."
        python3 nodes/expression_server.py > /tmp/petbot_expression.log 2>&1 &
        EXPR_PID=$!
        PIDS+=($EXPR_PID)
        NAMES+=("Expression Server")
        sleep 3
        
        if kill -0 $EXPR_PID 2>/dev/null; then
            echo -e "${GREEN}✓${NC} 表情服务器已启动 (PID: $EXPR_PID)"
            echo -e "   日志: /tmp/petbot_expression.log"
        else
            echo -e "${RED}✗${NC} 表情服务器启动失败"
            echo "   查看日志: cat /tmp/petbot_expression.log"
        fi
    fi
else
    echo -e "${YELLOW}⊘${NC}  跳过表情服务器"
fi

# 启动人脸识别节点
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  步骤 3/7: 启动人脸识别节点"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo -e "${BLUE}→${NC} 启动人脸识别节点..."
python3 nodes/vision/face_detection_node.py > /tmp/petbot_face.log 2>&1 &
FACE_PID=$!
PIDS+=($FACE_PID)
NAMES+=("Face Detection Node")
sleep 2

if kill -0 $FACE_PID 2>/dev/null; then
    echo -e "${GREEN}✓${NC} 人脸识别节点已启动 (PID: $FACE_PID)"
    echo -e "   日志: /tmp/petbot_face.log"
else
    echo -e "${RED}✗${NC} 人脸识别节点启动失败"
    echo "   查看日志: cat /tmp/petbot_face.log"
fi

# 启动 ASR 节点
if [ "$START_ASR" = true ]; then
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  步骤 4/7: 启动 ASR 语音识别节点"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    echo -e "${BLUE}→${NC} 启动 ASR 节点..."
    python3 nodes/asr_node.py > /tmp/petbot_asr.log 2>&1 &
    ASR_PID=$!
    PIDS+=($ASR_PID)
    NAMES+=("ASR Node")
    sleep 2
    
    if kill -0 $ASR_PID 2>/dev/null; then
        echo -e "${GREEN}✓${NC} ASR 节点已启动 (PID: $ASR_PID)"
        echo -e "   日志: /tmp/petbot_asr.log"
    else
        echo -e "${RED}✗${NC} ASR 节点启动失败"
        echo "   查看日志: cat /tmp/petbot_asr.log"
    fi
else
    echo -e "${YELLOW}⊘${NC}  跳过 ASR 节点"
fi

# 启动 TTS 节点
if [ "$START_TTS" = true ]; then
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  步骤 5/7: 启动 TTS 语音合成节点"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    echo -e "${BLUE}→${NC} 启动 TTS 节点..."
    python3 nodes/tts_node.py > /tmp/petbot_tts.log 2>&1 &
    TTS_PID=$!
    PIDS+=($TTS_PID)
    NAMES+=("TTS Node")
    sleep 2
    
    if kill -0 $TTS_PID 2>/dev/null; then
        echo -e "${GREEN}✓${NC} TTS 节点已启动 (PID: $TTS_PID)"
        echo -e "   日志: /tmp/petbot_tts.log"
    else
        echo -e "${RED}✗${NC} TTS 节点启动失败"
        echo "   查看日志: cat /tmp/petbot_tts.log"
    fi
else
    echo -e "${YELLOW}⊘${NC}  跳过 TTS 节点"
fi

# 启动 Chat 节点
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  步骤 6/7: 启动 Chat 对话节点"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo -e "${BLUE}→${NC} 启动 Chat 节点（LangGraph Agent）..."
python3 nodes/chat/chat_node.py > /tmp/petbot_chat.log 2>&1 &
CHAT_PID=$!
PIDS+=($CHAT_PID)
NAMES+=("Chat Node")
sleep 2

if kill -0 $CHAT_PID 2>/dev/null; then
    echo -e "${GREEN}✓${NC} Chat 节点已启动 (PID: $CHAT_PID)"
    echo -e "   日志: /tmp/petbot_chat.log"
else
    echo -e "${RED}✗${NC} Chat 节点启动失败"
    echo "   查看日志: cat /tmp/petbot_chat.log"
fi

# 启动头部跟踪节点
if [ "$START_HEAD" = true ]; then
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  步骤 7/7: 启动头部跟踪节点"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    if [ -f "nodes/body_control/turn_head copy.py" ]; then
        echo -e "${BLUE}→${NC} 启动头部跟踪节点..."
        python3 "nodes/body_control/turn_head copy.py" > /tmp/petbot_head.log 2>&1 &
        HEAD_PID=$!
        PIDS+=($HEAD_PID)
        NAMES+=("Turn Head Node")
        sleep 2
        
        if kill -0 $HEAD_PID 2>/dev/null; then
            echo -e "${GREEN}✓${NC} 头部跟踪节点已启动 (PID: $HEAD_PID)"
            echo -e "   日志: /tmp/petbot_head.log"
        else
            echo -e "${RED}✗${NC} 头部跟踪节点启动失败"
            echo "   查看日志: cat /tmp/petbot_head.log"
        fi
    else
        echo -e "${YELLOW}⚠${NC}  未找到头部跟踪节点文件"
    fi
else
    echo -e "${YELLOW}⊘${NC}  跳过头部跟踪节点"
fi

# 显示启动总结
echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                      系统启动完成                               ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

echo -e "${GREEN}✓${NC} 所有节点已启动！"
echo ""
echo "运行中的节点："
for i in "${!PIDS[@]}"; do
    pid=${PIDS[$i]}
    name=${NAMES[$i]}
    if kill -0 $pid 2>/dev/null; then
        echo -e "  ${GREEN}●${NC} $name (PID: $pid)"
    else
        echo -e "  ${RED}●${NC} $name (已停止)"
    fi
done

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  查看详细日志"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  tail -f /tmp/petbot_expression.log  # 表情服务器"
echo "  tail -f /tmp/petbot_face.log        # 人脸识别"
echo "  tail -f /tmp/petbot_asr.log         # 语音识别"
echo "  tail -f /tmp/petbot_tts.log         # 语音合成"
echo "  tail -f /tmp/petbot_chat.log        # 对话系统"
echo "  tail -f /tmp/petbot_head.log        # 头部跟踪"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 启动交互式监控界面
echo -e "${BLUE}→${NC} 启动交互式用户界面..."
echo ""
sleep 1

# 启动交互式监控（前台运行，这样用户可以看到交互）
python3 interactive_monitor.py

# 当交互式监控退出时，清理所有节点
echo ""
echo "正在关闭所有节点..."

