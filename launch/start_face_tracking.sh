#!/bin/bash

# Face Tracking System Startup Script
# Starts face detection and head tracking nodes for robot face following

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Source ROS 2 environment and service definitions
# Check if install directory exists in examples or project root
if [ -f "../nodes/install/setup.bash" ]; then
    source ../nodes/install/setup.bash
elif [ -f "../install/setup.bash" ]; then
    source ../install/setup.bash
else
    echo "⚠️  Warning: ROS 2 service definitions not found"
    echo "   Make sure you have run 'colcon build' if needed"
fi

echo "================================================"
echo "Starting Face Tracking System"
echo "================================================"
echo ""
echo "This will start 2 nodes:"
echo "  1. Face Detection Node - Detects faces with camera"
echo "  2. Turn Head Node - Controls robot to follow faces"
echo ""
echo "Press Ctrl+C to stop all nodes"
echo "================================================"
echo ""

# Activate virtual environment if exists
if [ -d "../.venv" ]; then
    source ../.venv/bin/activate
    echo "✅ Virtual environment activated"
fi

# Configuration parameters (can be customized)
CAMERA_INDEX=${CAMERA_INDEX:-0}
FRAME_WIDTH=${FRAME_WIDTH:-640}
FRAME_HEIGHT=${FRAME_HEIGHT:-480}
PUBLISH_RATE=${PUBLISH_RATE:-10}
DISPLAY_WINDOW=${DISPLAY_WINDOW:-true}
DETECTION_SCALE=${DETECTION_SCALE:-0.25}

echo "Camera Configuration:"
echo "  - Camera Index: $CAMERA_INDEX"
echo "  - Resolution: ${FRAME_WIDTH}x${FRAME_HEIGHT}"
echo "  - Publish Rate: ${PUBLISH_RATE}Hz"
echo "  - Display Window: $DISPLAY_WINDOW"
echo "  - Detection Scale: $DETECTION_SCALE"
echo ""

# Check if face_recognition is installed
if ! python3 -c "import face_recognition" 2>/dev/null; then
    echo "❌ ERROR: face_recognition library not found!"
    echo ""
    echo "Please install it using:"
    echo "  pip install face_recognition opencv-python"
    echo ""
    echo "Or install system dependencies first:"
    echo "  sudo apt-get install build-essential cmake libopenblas-dev liblapack-dev"
    echo "  pip install face_recognition opencv-python"
    echo ""
    exit 1
fi

echo "✅ face_recognition library is installed"
echo ""

# Start face detection node
echo "Starting Face Detection Node..."
python3 ../nodes/vision/face_detection_node.py \
    --camera_index $CAMERA_INDEX \
    --frame_width $FRAME_WIDTH \
    --frame_height $FRAME_HEIGHT \
    --publish_rate $PUBLISH_RATE \
    --display_window $DISPLAY_WINDOW \
    --detection_scale $DETECTION_SCALE &
FACE_DETECTION_PID=$!

sleep 2

# Start turn head node (using the simpler copy version that works)
echo "Starting Turn Head Node..."
python3 "../nodes/body_control/turn_head copy.py" &
TURN_HEAD_PID=$!

echo ""
echo "================================================"
echo "All nodes started!"
echo "Face Detection PID: $FACE_DETECTION_PID"
echo "Turn Head PID: $TURN_HEAD_PID"
echo ""
echo "🤖 The robot will now track faces in view!"
echo "   A window will show the camera feed with detected faces."
echo "   Press 'q' in the window or Ctrl+C here to stop."
echo ""
echo "Press Ctrl+C to stop all nodes"
echo "================================================"

# Wait for Ctrl+C
trap "echo ''; echo 'Stopping all nodes...'; kill $FACE_DETECTION_PID $TURN_HEAD_PID 2>/dev/null; exit" SIGINT SIGTERM

# Wait for all background processes
wait

