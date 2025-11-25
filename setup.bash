#!/bin/bash
# Petbot AI Chat System - Environment Setup Script
# Source this file to set up your environment quickly

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "========================================"
echo "Petbot Environment Setup"
echo "========================================"

# Get project root directory
PETBOT_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
echo "Project root: $PETBOT_ROOT"

# Activate virtual environment
if [ -d "$PETBOT_ROOT/.venv" ]; then
    source "$PETBOT_ROOT/.venv/bin/activate"
    echo -e "${GREEN}✓${NC} Virtual environment activated"
else
    echo -e "${YELLOW}!${NC} Virtual environment not found at $PETBOT_ROOT/.venv"
fi

# Source Service Definition if available
if [ -f "$PETBOT_ROOT/install/setup.bash" ]; then
    source "$PETBOT_ROOT/install/setup.bash"
    echo -e "${GREEN}✓${NC} Service Definition loaded"
else
    echo -e "${YELLOW}!${NC} Service Definition not found (run colcon build first if needed)"
fi

# Source ROS 2 environment
source /opt/ros/jazzy/setup.bash
echo -e "${GREEN}✓${NC} ROS 2 environment loaded"

# Load Deepseek API key from .env if exists and not already set
if [ -z "$DEEPSEEK_API_KEY" ]; then
    if [ -f "$PETBOT_ROOT/.env" ]; then
        export $(cat "$PETBOT_ROOT/.env" | grep -v '^#' | grep 'DEEPSEEK_API_KEY' | xargs)
        if [ -n "$DEEPSEEK_API_KEY" ]; then
            echo -e "${GREEN}✓${NC} Deepseek API key loaded from .env"
            echo "   Key: ${DEEPSEEK_API_KEY:0:8}...${DEEPSEEK_API_KEY: -4}"
        fi
    else
        echo -e "${YELLOW}!${NC} DEEPSEEK_API_KEY not set"
        echo ""
        echo "To set your API key:"
        echo "  export DEEPSEEK_API_KEY='sk-your-key-here'"
        echo ""
        echo "Or create a .env file:"
        echo "  echo 'DEEPSEEK_API_KEY=sk-your-key-here' > $PETBOT_ROOT/.env"
        echo "  source $PETBOT_ROOT/setup.bash"
    fi
else
    echo -e "${GREEN}✓${NC} Deepseek API key already set"
    echo "   Key: ${DEEPSEEK_API_KEY:0:8}...${DEEPSEEK_API_KEY: -4}"
fi

# Set HF_ENDPOINT
export HF_ENDPOINT="https://hf-mirror.com"
echo -e "${GREEN}✓${NC} HF_ENDPOINT set to $HF_ENDPOINT"

echo ""
echo "========================================"
echo "Environment ready!"
echo "========================================"
echo ""
echo "Quick commands:"
echo "  cd demo && ./start_echo_system.sh   # Start echo system"
echo "  cd demo && ./start_chat_system.sh   # Start AI chat"
echo "  cd demo && python3 test_deepseek.py # Test API"
echo ""
