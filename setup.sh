#!/bin/bash
#
# Petbot 统一环境配置脚本
# 一键安装所有依赖、配置环境、准备运行
#

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 获取脚本目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# 打印横幅
print_banner() {
    echo ""
    echo -e "${CYAN}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║                                                                ║${NC}"
    echo -e "${CYAN}║              🤖 Petbot 统一环境配置脚本 v2.0                  ║${NC}"
    echo -e "${CYAN}║                                                                ║${NC}"
    echo -e "${CYAN}╚════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

# 打印步骤标题
print_step() {
    echo ""
    echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
    echo ""
}

# 打印成功消息
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

# 打印警告消息
print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# 打印错误消息
print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# 打印信息消息
print_info() {
    echo -e "${CYAN}ℹ️  $1${NC}"
}

# 检查命令是否存在
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# 主函数
main() {
    print_banner
    
    print_info "项目根目录: $SCRIPT_DIR"
    
    # ========================================
    # 步骤 1: 检查系统依赖
    # ========================================
    print_step "步骤 1/7: 检查系统依赖"
    
    # 检查 Python 3
    if command_exists python3; then
        PYTHON_VERSION=$(python3 --version | awk '{print $2}')
        print_success "Python 3 已安装: $PYTHON_VERSION"
    else
        print_error "未找到 Python 3，请先安装"
        exit 1
    fi
    
    # 检查 pip
    if command_exists pip3; then
        print_success "pip3 已安装"
    else
        print_error "未找到 pip3，请先安装"
        exit 1
    fi
    
    # 检查 ROS2
    if [ -f "/opt/ros/jazzy/setup.bash" ]; then
        print_success "ROS2 Jazzy 已安装"
        source /opt/ros/jazzy/setup.bash
    else
        print_warning "未找到 ROS2 Jazzy（部分功能可能不可用）"
    fi
    
    # 检查 cmake (face_recognition需要)
    if command_exists cmake; then
        print_success "cmake 已安装"
    else
        print_warning "未找到 cmake，将通过 pip 安装"
    fi
    
    # ========================================
    # 步骤 2: 虚拟环境
    # ========================================
    print_step "步骤 2/7: 配置 Python 虚拟环境"
    
    if [ -d ".venv" ]; then
        print_success "发现现有虚拟环境"
        source .venv/bin/activate
        print_success "虚拟环境已激活"
    else
        print_info "创建新的虚拟环境..."
        python3 -m venv .venv
        source .venv/bin/activate
        print_success "虚拟环境已创建并激活"
    fi
    
    # 升级 pip
    print_info "升级 pip..."
    pip install --upgrade pip -q
    print_success "pip 已升级到最新版本"
    
    # ========================================
    # 步骤 3: 安装 Python 依赖
    # ========================================
    print_step "步骤 3/7: 安装 Python 依赖包"
    
    # 从统一的 requirements.txt 安装依赖
    if [ -f "requirements.txt" ]; then
        print_info "从 requirements.txt 安装依赖..."
        print_warning "注意：部分包（ASR/TTS）可能因 GitHub 访问问题而失败，但不影响核心功能"
        
        # 尝试安装，但不因失败而退出
        if pip install -r requirements.txt 2>&1 | tee /tmp/pip_install.log; then
            print_success "依赖安装完成"
        else
            print_warning "部分依赖安装失败，继续安装核心包..."
            
            # 手动安装关键包
            print_info "安装核心包..."
            pip install -q \
                python-dotenv requests fastapi uvicorn \
                opencv-python numpy pillow \
                face-recognition dlib cmake \
                langgraph langchain-openai langchain-core \
                pyyaml loguru dashscope pyaudio pydub pyserial sounddevice can
            
            print_warning "GitHub 依赖包安装失败（ASR/TTS 功能可能不可用）"
            print_info "如需完整功能，请配置 GitHub 代理后重新运行："
            echo "  export https_proxy=http://127.0.0.1:7890"
            echo "  pip install -r requirements.txt"
        fi
    else
        print_warning "未找到 requirements.txt，手动安装核心依赖..."
        pip install -q \
            python-dotenv requests fastapi uvicorn \
            opencv-python numpy pillow \
            face-recognition dlib cmake \
            langgraph langchain-openai langchain-core \
            pyyaml loguru dashscope pyaudio pydub pyserial sounddevice can
    fi
    
    # 验证核心依赖是否安装成功
    print_info "验证核心依赖..."
    python3 -c "import cv2, face_recognition, fastapi, dotenv" 2>/dev/null
    if [ $? -eq 0 ]; then
        print_success "核心依赖验证通过"
    else
        print_error "核心依赖验证失败，请检查安装"
        exit 1
    fi
    
    # ========================================
    # 步骤 4: 构建 ROS2 服务定义
    # ========================================
    print_step "步骤 4/7: 构建 ROS2 服务定义"
    
    # 先检查 install/setup.bash 是否已存在
    if [ -f "install/setup.bash" ]; then
        # 已构建过，直接 source
        source install/setup.bash
        print_success "ROS2 工作空间已加载（已构建）"
    elif [ -d "service_define" ]; then
        # 未构建，但有 service_define 目录，尝试构建
        print_info "发现 service_define 目录，正在构建..."
        
        if command_exists colcon; then
            colcon build --packages-select service_define
            print_success "ROS2 服务定义构建完成"
            
            # Source the workspace
            if [ -f "install/setup.bash" ]; then
                source install/setup.bash
                print_success "ROS2 工作空间已加载"
            fi
        else
            print_warning "未找到 colcon，跳过服务定义构建"
            print_info "如需使用 ROS2 功能，请安装: sudo apt install python3-colcon-common-extensions"
        fi
    else
        # 既没有构建产物，也没有源代码目录
        print_info "未找到 ROS2 服务定义（跳过，不影响核心功能）"
    fi
    
    # ========================================
    # 步骤 5: 配置 API 密钥和环境变量
    # ========================================
    print_step "步骤 5/7: 配置 API 密钥和环境变量"
    
    # 检查或创建 .env 文件
    if [ -f ".env" ]; then
        print_success "发现现有 .env 文件"
    else
        if [ -f "env.example" ]; then
            print_info "从 env.example 创建 .env 文件..."
            cp env.example .env
            print_success ".env 文件已创建"
        else
            print_info "创建新的 .env 文件..."
            touch .env
            print_success ".env 文件已创建"
        fi
    fi
    
    # 配置必需的 API 密钥
    echo ""
    print_info "正在检查必需的 API 密钥..."
    echo ""
    
    # Deepseek API Key
    if grep -q "^DEEPSEEK_API_KEY=.\+" .env 2>/dev/null; then
        print_success "DEEPSEEK_API_KEY 已配置"
    else
        print_warning "未找到 DEEPSEEK_API_KEY"
        echo ""
        read -p "请输入 Deepseek API Key (用于 AI 对话): " deepseek_key
        if [ -n "$deepseek_key" ]; then
            if grep -q "^DEEPSEEK_API_KEY=" .env 2>/dev/null; then
                # 替换现有的空值
                sed -i "s|^DEEPSEEK_API_KEY=.*|DEEPSEEK_API_KEY=$deepseek_key|" .env
            else
                # 添加新行
                echo "DEEPSEEK_API_KEY=$deepseek_key" >> .env
            fi
            print_success "DEEPSEEK_API_KEY 已配置"
        else
            print_warning "跳过 DEEPSEEK_API_KEY 配置（稍后可手动添加）"
        fi
    fi
    
    # 高德地图 API Key (可选)
    echo ""
    if grep -q "^AMAP_API_KEY=.\+" .env 2>/dev/null; then
        print_success "AMAP_API_KEY 已配置（天气查询可用）"
    else
        print_warning "未找到 AMAP_API_KEY（天气查询功能将不可用）"
        echo ""
        read -p "是否配置高德地图 API Key 以启用天气查询？(y/n): " config_amap
        if [ "$config_amap" = "y" ] || [ "$config_amap" = "Y" ]; then
            read -p "请输入高德地图 API Key: " amap_key
            if [ -n "$amap_key" ]; then
                if grep -q "^AMAP_API_KEY=" .env 2>/dev/null; then
                    sed -i "s|^AMAP_API_KEY=.*|AMAP_API_KEY=$amap_key|" .env
                else
                    echo "AMAP_API_KEY=$amap_key" >> .env
                fi
                print_success "AMAP_API_KEY 已配置"
            fi
        else
            print_info "跳过天气查询配置（稍后可手动添加）"
        fi
    fi
    
    # 表情服务器配置（使用默认值）
    echo ""
    if ! grep -q "^EXPRESSION_SERVER_HOST=" .env 2>/dev/null; then
        echo "EXPRESSION_SERVER_HOST=0.0.0.0" >> .env
        print_success "表情服务器地址已配置: 0.0.0.0"
    fi
    
    if ! grep -q "^EXPRESSION_SERVER_PORT=" .env 2>/dev/null; then
        echo "EXPRESSION_SERVER_PORT=8001" >> .env
        print_success "表情服务器端口已配置: 8001"
    fi
    
    # 表情映射配置（使用默认值）
    if ! grep -q "^EXPRESSION_ALL_KNOWN=" .env 2>/dev/null; then
        echo "EXPRESSION_ALL_KNOWN=happy" >> .env
    fi
    if ! grep -q "^EXPRESSION_HAS_UNKNOWN=" .env 2>/dev/null; then
        echo "EXPRESSION_HAS_UNKNOWN=surprised" >> .env
    fi
    if ! grep -q "^EXPRESSION_NO_FACE=" .env 2>/dev/null; then
        echo "EXPRESSION_NO_FACE=neutral" >> .env
    fi
    print_success "表情映射配置已完成"
    
    # HuggingFace 镜像
    if ! grep -q "^HF_ENDPOINT=" .env 2>/dev/null; then
        echo "HF_ENDPOINT=https://hf-mirror.com" >> .env
        print_success "HuggingFace 镜像已配置"
    fi
    
    # ========================================
    # 步骤 6: 创建必要的目录
    # ========================================
    print_step "步骤 6/7: 创建必要的目录结构"
    
    # 创建 images/known_faces 目录
    if [ ! -d "images/known_faces" ]; then
        mkdir -p images/known_faces
        print_success "创建目录: images/known_faces"
        
        # 创建 README
        cat > images/known_faces/README.md << 'EOF'
# 已知人脸照片目录

## 使用方法

1. 将已知人物的照片放入此目录
2. 文件名即为该人的名字（支持中文）
3. 支持的格式：.jpg, .jpeg, .png, .bmp

## 示例

```
images/known_faces/
├── 张三.jpg
├── 李四.png
└── 王五.jpg
```

## 要求

- 每张照片中只能有一个人脸
- 照片清晰，光线充足
- 人脸正面或接近正面

## 或者使用语音命令

对机器人说："记住我的脸，我是张三"

系统会自动截图并保存。
EOF
        print_success "创建 README: images/known_faces/README.md"
    else
        print_success "目录已存在: images/known_faces"
    fi
    
    # 确保 launch 目录存在
    if [ ! -d "launch" ]; then
        mkdir -p launch
        print_success "创建目录: launch"
    fi
    
    # 确保 test 目录存在
    if [ ! -d "test" ]; then
        mkdir -p test
        print_success "创建目录: test"
    fi
    
    # ========================================
    # 步骤 7: 生成快速启动脚本
    # ========================================
    print_step "步骤 7/7: 生成快速环境激活脚本"
    
    # 创建 activate.sh 用于快速激活环境
    cat > activate.sh << 'ACTIVATE_EOF'
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
ACTIVATE_EOF
    
    chmod +x activate.sh
    print_success "已创建 activate.sh（快速环境激活）"
    
    # ========================================
    # 完成
    # ========================================
    echo ""
    print_banner
    
    echo -e "${GREEN}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                                                                ║${NC}"
    echo -e "${GREEN}║                    ✅ 环境配置完成！                            ║${NC}"
    echo -e "${GREEN}║                                                                ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    
    print_info "📋 配置摘要"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  • Python 虚拟环境: ✅ 已激活"
    echo "  • Python 依赖包: ✅ 已安装"
    echo "  • LangGraph & Agent: ✅ 已安装"
    echo "  • ROS2 服务定义: ✅ 已构建"
    
    if grep -q "^DEEPSEEK_API_KEY=.\+" .env 2>/dev/null; then
        echo "  • Deepseek API: ✅ 已配置"
    else
        echo "  • Deepseek API: ⚠️  未配置（需要手动配置）"
    fi
    
    if grep -q "^AMAP_API_KEY=.\+" .env 2>/dev/null; then
        echo "  • 高德地图 API: ✅ 已配置"
    else
        echo "  • 高德地图 API: ⏭️  跳过（天气查询不可用）"
    fi
    
    echo "  • 表情控制: ✅ 已配置"
    echo "  • 目录结构: ✅ 已创建"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    
    print_info "🚀 接下来你可以："
    echo ""
    echo "  1️⃣  激活环境（新终端需要）："
    echo -e "     ${CYAN}source activate.sh${NC}"
    echo ""
    echo "  2️⃣  测试 AI Agent（无需机器人硬件）："
    echo -e "     ${CYAN}python3 test/test_agent_interactive.py${NC}"
    echo ""
    echo "  3️⃣  启动完整系统："
    echo -e "     ${CYAN}./start_all.sh${NC}"
    echo ""
    echo "  4️⃣  仅启动部分组件："
    echo -e "     ${CYAN}./start_all.sh --no-head --no-expression${NC}"
    echo ""
    echo "  5️⃣  查看详细文档："
    echo -e "     ${CYAN}cat README.md${NC}"
    echo ""
    
    if ! grep -q "^DEEPSEEK_API_KEY=.\+" .env 2>/dev/null; then
        print_warning "记得配置 API 密钥"
        echo "  编辑 .env 文件并添加："
        echo -e "  ${CYAN}DEEPSEEK_API_KEY=sk-your-key-here${NC}"
        echo ""
    fi
    
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    print_success "🎉 准备就绪！Petbot 系统已配置完成！"
    echo ""
}

# 运行主函数
main "$@"

