#!/usr/bin/env python3
import cv2
from flask import Flask, Response

app = Flask(__name__)

def gen_frames():
    # 打开设备 0（FaceTime 高清相机）
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise RuntimeError("Cannot open camera 0")

    # 设置分辨率和帧率（30帧）
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 30)

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        # 此时 frame 就是 OpenCV 标准格式：
        #   - numpy.ndarray
        #   - dtype = uint8
        #   - shape = (H, W, 3)
        #   - 通道顺序 = BGR  （也就是 BGR8）

        # 只在传输时压成 JPEG，客户端解码后仍然是 BGR
        ret, buffer = cv2.imencode('.jpg', frame)
        if not ret:
            continue
        jpg_bytes = buffer.tobytes()
        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n" + jpg_bytes + b"\r\n"
        )

@app.route('/video')
def video():
    return Response(
        gen_frames(),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )

if __name__ == '__main__':
    # 对容器暴露：0.0.0.0:5000
    app.run(host='0.0.0.0', port=5012, debug=False, threaded=True)
