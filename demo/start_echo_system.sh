#!/bin/bash

# Echo System Startup Script
# This script starts the ASR, TTS, and Echo nodes in separate terminals

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Source ROS 2 environment
source ../install/setup.bash

echo "================================================"
echo "Starting Voice Echo System"
echo "================================================"
echo ""
echo "This will start 3 nodes:"
echo "  1. ASR Node - Listens and recognizes speech"
echo "  2. TTS Node - Text-to-speech output"
echo "  3. Echo Node - Bridges ASR and TTS"
echo ""
echo "Press Ctrl+C to stop all nodes"
echo "================================================"
echo ""

# Activate virtual environment if exists
if [ -d "../.venv" ]; then
    source ../.venv/bin/activate
fi

# Start all nodes in the background with output
echo "Starting ASR Node..."
python3 ../examples/asr_node.py &
ASR_PID=$!

sleep 2

echo "Starting TTS Node..."
python3 ../examples/tts_node.py &
TTS_PID=$!

sleep 2

echo "Starting Echo Node..."
python3 echo_node.py &
ECHO_PID=$!

echo ""
echo "================================================"
echo "All nodes started!"
echo "ASR PID: $ASR_PID"
echo "TTS PID: $TTS_PID"
echo "Echo PID: $ECHO_PID"
echo ""
echo "Now speak something and it will be echoed back!"
echo "Press Ctrl+C to stop all nodes"
echo "================================================"

# Wait for Ctrl+C
trap "echo ''; echo 'Stopping all nodes...'; kill $ASR_PID $TTS_PID $ECHO_PID 2>/dev/null; exit" SIGINT SIGTERM

# Wait for all background processes
wait

