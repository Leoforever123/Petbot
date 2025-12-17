#!/bin/bash
# Face Recognition Test Program Launcher
# 人脸识别测试程序启动脚本

echo "=================================="
echo "人脸识别测试程序启动器"
echo "=================================="
echo ""

# Get project root directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Check if virtual environment exists
if [ ! -d "$PROJECT_ROOT/.venv" ]; then
    echo "❌ 错误: 虚拟环境不存在"
    echo "请先创建虚拟环境: python3 -m venv .venv"
    exit 1
fi

# Activate virtual environment
echo "正在激活虚拟环境..."
source "$PROJECT_ROOT/.venv/bin/activate"

# Check if face_recognition is installed
if ! python3 -c "import face_recognition" 2>/dev/null; then
    echo ""
    echo "⚠️  face_recognition 库未安装"
    echo ""
    echo "需要先安装依赖，这可能需要 5-10 分钟时间。"
    read -p "是否现在安装? (y/n): " install_choice
    
    if [ "$install_choice" = "y" ] || [ "$install_choice" = "Y" ]; then
        echo ""
        echo "安装系统依赖..."
        sudo apt update
        sudo apt install -y build-essential cmake pkg-config
        sudo apt install -y libx11-dev libatlas-base-dev
        sudo apt install -y libgtk-3-dev libboost-python-dev
        
        echo ""
        echo "安装 Python 包（这一步可能需要较长时间）..."
        pip install --upgrade pip
        pip install face-recognition dlib cmake
        
        echo ""
        echo "✓ 安装完成！"
    else
        echo "已取消。请手动安装依赖后再运行。"
        exit 1
    fi
fi

# Check known faces directory
KNOWN_FACES_DIR="$PROJECT_ROOT/images/known_faces"
if [ ! -d "$KNOWN_FACES_DIR" ]; then
    echo "创建 known_faces 目录..."
    mkdir -p "$KNOWN_FACES_DIR"
fi

# Count known faces
FACE_COUNT=$(find "$KNOWN_FACES_DIR" -type f \( -iname "*.jpg" -o -iname "*.jpeg" -o -iname "*.png" \) 2>/dev/null | wc -l)
echo ""
echo "已知人脸数量: $FACE_COUNT"
if [ "$FACE_COUNT" -eq 0 ]; then
    echo ""
    echo "⚠️  提示: 尚未添加任何已知人脸照片"
    echo "照片目录: $KNOWN_FACES_DIR"
    echo ""
fi

# Run the program
echo ""
echo "启动程序..."
echo ""
cd "$SCRIPT_DIR"
python3 test_face_recognition.py

echo ""
echo "程序已退出"

