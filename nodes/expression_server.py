import cv2
import time
import threading
import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import JSONResponse
import uvicorn
from dotenv import load_dotenv
import requests

# 加载环境变量
load_dotenv()

# 获取表情视频基础路径（相对于脚本所在目录）
SCRIPT_DIR = Path(__file__).parent
VIDEO_BASE_PATH = str(SCRIPT_DIR / "expression") + os.sep

gaze_mode = False

#显示视线的思路，接收一个post请求，如果注视状态发生变化则改变neutral表情的映射，那这样current_video就也需要改成表情

# 表情对应的视频文件路径配置
expressions = {
    "happy": f"{VIDEO_BASE_PATH}happy.mp4",
    "angry": f"{VIDEO_BASE_PATH}angry.mp4",
    "sad": f"{VIDEO_BASE_PATH}sad.mp4",
    "hatred": f"{VIDEO_BASE_PATH}hatred.mp4",
    "scared": f"{VIDEO_BASE_PATH}scared.mp4",
    "surprised": f"{VIDEO_BASE_PATH}surprised.mp4",
    "more-happy": f"{VIDEO_BASE_PATH}surprised.mp4",
    "neutral": f"{VIDEO_BASE_PATH}neutral_notlisten.mp4",
    "dizzy": f"{VIDEO_BASE_PATH}dizzy.mp4",
    "evil_smile": f"{VIDEO_BASE_PATH}evil_smile.mp4",
    "nauty_smile": f"{VIDEO_BASE_PATH}evil_smile.mp4",
    "pitying": f"{VIDEO_BASE_PATH}sympathy.mp4",
    "sleep": f"{VIDEO_BASE_PATH}sleep1.mp4",
    "say_hallo": f"{VIDEO_BASE_PATH}say_hallo.mp4",
    "function_display": f"{VIDEO_BASE_PATH}function_express.mp4",
    "camera_error": f"{VIDEO_BASE_PATH}camera_error.mp4",
}

# 默认表情
DEFAULT_EXPRESSION = os.getenv("EXPRESSION_DEFAULT", "neutral")
current_expression = DEFAULT_EXPRESSION

# 线程同步，通知播放线程切换视频
stop_event = threading.Event()
switch_event = threading.Event()  # 用于通知切换视频

# 全局变量：窗口是否已初始化
window_initialized = False

# 实例化 FastAPI 应用
app = FastAPI(title="Expression Player API", description="API 助力 OpenCV 播放表情视频")


@app.get("/expressions")
async def get_available_expressions():
    """
    返回所有可用的表情列表
    """
    return {"expressions": list(expressions.keys())}

@app.post("/if_gaze/{if_gaze}")
async def change_gazemode(if_gaze:str):
    global stop_event,gaze_mode,expressions,VIDEO_BASE_PATH
    if if_gaze == "true":
        if_gaze = True
    else:
        if_gaze = False
    if if_gaze!=gaze_mode:
        gaze_mode = if_gaze
        if gaze_mode:
            expressions['neutral'] = f"{VIDEO_BASE_PATH}neutral.mp4"
        else:
            expressions['neutral'] = f"{VIDEO_BASE_PATH}neutral_notlisten.mp4"
        switch_event.set()  # 通知切换视频


@app.post("/expression/{expression}")
async def change_expression(expression: str):
    """
    设置指定表情
    """
    global current_expression, switch_event

    if expression not in expressions:
        return JSONResponse(
            status_code=404, content={"message": f"Expression '{expression}' not found"}
        )

    if current_expression != expression:
        current_expression = expression
        switch_event.set()  # 通知播放线程立即切换
        return {"message": f"Switching to '{expression}' expression"}
    else:
        return {"message": f"Expression '{expression}' is already playing"}


@app.post("/reset")
async def reset_expression():
    """
    重置为默认表情
    """
    global current_expression, switch_event
    current_expression = DEFAULT_EXPRESSION
    switch_event.set()  # 通知播放线程切换到默认视频
    return {"message": f"Reset to default expression '{DEFAULT_EXPRESSION}'"}


def run_api_server():
    """
    运行 FastAPI 服务器，使用 uvicorn 启动
    """
    host = os.getenv("EXPRESSION_SERVER_HOST", "0.0.0.0")
    port = int(os.getenv("EXPRESSION_SERVER_PORT", "8001"))
    uvicorn.run(app, host=host, port=port)


# 全局窗口名称
EXPRESSION_WINDOW_NAME = "PetBot 表情显示"

def init_window():
    """
    初始化窗口（只调用一次）
    """
    global window_initialized
    
    if window_initialized:
        return
    
    # 创建窗口（可调整大小）
    cv2.namedWindow(EXPRESSION_WINDOW_NAME, cv2.WINDOW_NORMAL)
    
    # 设置窗口大小
    default_width = int(os.getenv("EXPRESSION_VIDEO_WIDTH", "640"))
    default_height = int(os.getenv("EXPRESSION_VIDEO_HEIGHT", "480"))
    cv2.resizeWindow(EXPRESSION_WINDOW_NAME, default_width, default_height)
    
    # 设置窗口位置（右上角）
    try:
        import tkinter as tk
        root = tk.Tk()
        screen_width = root.winfo_screenwidth()
        root.destroy()
        cv2.moveWindow(EXPRESSION_WINDOW_NAME, screen_width - default_width - 50, 50)
    except:
        pass
    
    window_initialized = True
    print(f"✅ 表情窗口已创建: {EXPRESSION_WINDOW_NAME} ({default_width}x{default_height})")


def play_video_continuously():
    """
    主循环：在同一个窗口中持续播放视频，根据current_expression切换不同的视频
    """
    global current_expression, switch_event, expressions, window_initialized
    
    # 初始化窗口（只一次）
    init_window()
    
    current_video_path = None
    cap = None
    
    default_width = int(os.getenv("EXPRESSION_VIDEO_WIDTH", "640"))
    default_height = int(os.getenv("EXPRESSION_VIDEO_HEIGHT", "480"))
    frame_delay = float(os.getenv("EXPRESSION_FRAME_DELAY", "0.04"))
    
    while True:
        # 检查是否需要切换视频
        if switch_event.is_set():
            switch_event.clear()
            
            new_video_path = expressions[current_expression]
            
            # 如果视频路径改变了，需要切换
            if new_video_path != current_video_path:
                # 关闭旧的视频
                if cap is not None:
                    cap.release()
                    cap = None
                
                # 打开新视频
                current_video_path = new_video_path
                print(f"🎬 切换到表情视频: {os.path.basename(current_video_path)}")
                
                cap = cv2.VideoCapture(current_video_path)
                if not cap.isOpened():
                    print(f"❌ 无法打开视频: {current_video_path}")
                    cap = None
                    current_video_path = None
                    continue
        
        # 如果还没有打开视频，打开默认视频
        if cap is None:
            current_video_path = expressions[current_expression]
            print(f"🎬 播放表情视频: {os.path.basename(current_video_path)}")
            cap = cv2.VideoCapture(current_video_path)
            if not cap.isOpened():
                print(f"❌ 无法打开视频: {current_video_path}")
                time.sleep(1)  # 等待一下再重试
                continue
        
        # 读取并显示帧
        ret, frame = cap.read()
        
        if not ret:
            # 视频播放完毕，重新开始
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            continue
        
        # 调整帧大小
        frame = cv2.resize(frame, (default_width, default_height))
        
        # 在视频上叠加当前表情名称
        expression_text = os.path.basename(current_video_path).replace('.mp4', '')
        text_size = cv2.getTextSize(f"表情: {expression_text}", cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2)[0]
        cv2.rectangle(frame, (5, 5), (text_size[0] + 15, text_size[1] + 20), (0, 0, 0), -1)
        cv2.putText(frame, f"表情: {expression_text}", 
                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        
        # 显示帧
        cv2.imshow(EXPRESSION_WINDOW_NAME, frame)
        
        # 检查按键（'q'退出）
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
        
        # 控制播放速度
        time.sleep(frame_delay)
    
    # 清理
    if cap is not None:
        cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    print("=" * 60)
    print("🎭 PetBot 表情显示系统启动中...")
    print("=" * 60)
    print(f"📁 表情视频目录: {VIDEO_BASE_PATH}")
    print(f"🎬 默认表情: {DEFAULT_EXPRESSION}")
    print(f"🌐 API服务器: http://localhost:8001")
    print("=" * 60)
    print()
    
    # 开启 FastAPI 服务线程（守护线程）
    api_thread = threading.Thread(target=run_api_server, daemon=True)
    api_thread.start()
    
    # 等待服务器启动
    time.sleep(1)
    
    # 输出就绪标志 - 用于启动脚本检测
    print("PETBOT_EXPRESSION_READY", flush=True)
    print()
    print("✅ 表情系统已就绪！")
    print("📺 表情窗口将自动打开...")
    print("💡 提示: 按 'q' 键可以关闭表情窗口")
    print()
    
    # 主线程运行 OpenCV 视频播放（默认及切换表情）
    try:
        play_video_continuously()
    except KeyboardInterrupt:
        print("\n正在关闭表情窗口...")
        cv2.destroyAllWindows()
        print("✅ 表情系统已关闭")
