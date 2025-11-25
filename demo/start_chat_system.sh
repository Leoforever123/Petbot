#!/bin/bash

# AI Chat System Startup Script
# Starts ASR, TTS, and AI Chat nodes for intelligent conversations

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Source ROS 2 environment and service definitions
# Check if install directory exists in examples or project root
if [ -f "../examples/install/setup.bash" ]; then
    source ../examples/install/setup.bash
elif [ -f "../install/setup.bash" ]; then
    source ../install/setup.bash
else
    echo "⚠️  Warning: ROS 2 service definitions not found"
    echo "   Make sure you have run 'colcon build' if needed"
fi

echo "================================================"
echo "Starting AI Chat System with Deepseek"
echo "================================================"
echo ""
echo "This will start 3 nodes:"
echo "  1. ASR Node - Listens and recognizes speech"
echo "  2. TTS Node - Text-to-speech output"
echo "  3. Chat Node - AI conversation with Deepseek"
echo ""
echo "Press Ctrl+C to stop all nodes"
echo "================================================"
echo ""

# Activate virtual environment if exists
if [ -d "../.venv" ]; then
    source ../.venv/bin/activate
fi

# Check for API key
if [ -z "$DEEPSEEK_API_KEY" ]; then
    # Try loading from .env file if it exists
    if [ -f "../.env" ]; then
        echo "Loading API key from .env file..."
        export $(cat ../.env | grep -v '^#' | grep 'DEEPSEEK_API_KEY' | xargs)
    fi
    
    # Check again after loading .env
    if [ -z "$DEEPSEEK_API_KEY" ]; then
        echo "❌ ERROR: DEEPSEEK_API_KEY not found!"
        echo ""
        echo "Please set your Deepseek API key using one of these methods:"
        echo ""
        echo "📝 Method 1: Export environment variable (recommended)"
        echo "   export DEEPSEEK_API_KEY='sk-your-key-here'"
        echo "   ./start_chat_system.sh"
        echo ""
        echo "📝 Method 2: Create .env file"
        echo "   echo 'DEEPSEEK_API_KEY=sk-your-key-here' > ../.env"
        echo "   ./start_chat_system.sh"
        echo ""
        echo "📝 Method 3: Add to ~/.bashrc (persistent)"
        echo "   echo 'export DEEPSEEK_API_KEY=sk-your-key-here' >> ~/.bashrc"
        echo "   source ~/.bashrc"
        echo ""
        exit 1
    fi
    echo "✅ API key loaded from .env file"
else
    echo "✅ API key found in environment"
fi

# Show partial key for verification
echo "   Key: ${DEEPSEEK_API_KEY:0:8}...${DEEPSEEK_API_KEY: -4}"
echo ""

# Start all nodes in the background with output
echo "Starting ASR Node..."
python3 ../examples/asr_node.py &
ASR_PID=$!

sleep 2

echo "Starting TTS Node..."
python3 ../examples/tts_node.py &
TTS_PID=$!

sleep 2

echo "Starting Chat Node..."
python3 chat_node.py &
CHAT_PID=$!

echo ""
echo "================================================"
echo "All nodes started!"
echo "ASR PID: $ASR_PID"
echo "TTS PID: $TTS_PID"
echo "Chat PID: $CHAT_PID"
echo ""
echo "🤖 Now speak to have an AI conversation!"
echo "   The AI will respond to your questions"
echo ""
echo "Press Ctrl+C to stop all nodes"
echo "================================================"

# Wait for Ctrl+C
trap "echo ''; echo 'Stopping all nodes...'; kill $ASR_PID $TTS_PID $CHAT_PID 2>/dev/null; exit" SIGINT SIGTERM

# Wait for all background processes
wait

