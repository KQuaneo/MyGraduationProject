import time
import io
import cv2
import numpy as np
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from picamera2 import Picamera2
from deepface import DeepFace

# ================= 配置区域 =================
HOST_NAME = '0.0.0.0'
PORT_NUMBER = 8000
# 检测频率：每隔多少帧检测一次表情 (Pi5 上建议 15-30)
DETECT_INTERVAL = 20 
# ===========================================

# 全局变量，用于在不同线程间共享最新的表情结果
current_emotion = "Analyzing..."
current_score = 0.0
face_box = None

print("正在初始化摄像头...")
picam2 = Picamera2()
# 配置为 640x480 分辨率，格式 RGB888
config = picam2.create_preview_configuration(main={"size": (640, 480), "format": "RGB888"})
picam2.configure(config)
picam2.start()
print("摄像头已启动！")

# --- 表情识别线程函数 ---
# 我们在主循环里做简单的跳帧处理，复杂的识别逻辑由 DeepFace 内部处理
# 为了不阻塞视频流，我们在每一帧只做绘制，识别只在特定帧触发

class StreamingHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global current_emotion, current_score, face_box
        
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"""
                <html>
                <head><title>Pi 5 Emotion AI</title></head>
                <body style="background: #111; color: #eee; text-align: center;">
                    <h1>Facial Emotion Recognition</h1>
                    <img src="/stream.mjpg" style="border: 4px solid #00ff00;" />
                </body>
                </html>
            """)
        elif self.path == '/stream.mjpg':
            self.send_response(200)
            self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=FRAME')
            self.end_headers()
            
            frame_count = 0
            
            try:
                while True:
                    # 1. 获取图像矩阵 (RGB)
                    image = picam2.capture_array()
                    
                    # 2. 转为 OpenCV 格式 (BGR)
                    image_bgr = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
                    
                    # 3. --- 核心识别逻辑 (跳帧处理) ---
                    if frame_count % DETECT_INTERVAL == 0:
                        try:
                            # actions=['emotion'] 只识别表情
                            # detector_backend='opencv' 使用最快的 opencv 人脸检测器 (也可以换 'ssd' 或 'mediapipe')
                            # enforce_detection=False 允许未检测到人脸时不报错
                            results = DeepFace.analyze(
                                img_path = image_bgr, 
                                actions = ['emotion'], 
                                detector_backend = 'opencv', 
                                enforce_detection = False,
                                silent = True
                            )
                            
                            if results and len(results) > 0:
                                # 取第一张人脸的结果
                                res = results[0]
                                dominant_emotion = res['dominant_emotion'] # 例如 "happy"
                                emotion_score = res['emotion'][dominant_emotion] # 例如 95.2
                                
                                # 更新全局变量
                                current_emotion = dominant_emotion
                                current_score = emotion_score
                                
                                # 更新人脸框位置
                                region = res['region']
                                face_box = (region['x'], region['y'], region['w'], region['h'])
                            else:
                                face_box = None
                                current_emotion = "No Face"
                                
                        except Exception as e:
                            print(f"识别出错: {e}")

                    # 4. --- 绘制结果 (每一帧都画) ---
                    # 画框
                    if face_box:
                        x, y, w, h = face_box
                        cv2.rectangle(image_bgr, (x, y), (x+w, y+h), (0, 255, 0), 2)
                    
                    # 画文字 (背景黑条 + 文字)
                    info_text = f"{current_emotion}: {current_score:.1f}%"
                    cv2.rectangle(image_bgr, (10, 10), (300, 50), (0,0,0), -1) # 文字背景
                    
                    # 根据表情改变文字颜色
                    text_color = (0, 255, 255) # 默认黄
                    if current_emotion == 'happy': text_color = (0, 255, 0) # 开心绿
                    elif current_emotion == 'angry': text_color = (0, 0, 255) # 生气红
                    
                    cv2.putText(image_bgr, info_text, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, text_color, 2)

                    # 5. 编码为 JPEG 并发送
                    ret, jpeg = cv2.imencode('.jpg', image_bgr)
                    frame_data = jpeg.tobytes()
                    
                    self.wfile.write(b'--FRAME\r\n')
                    self.send_header('Content-Type', 'image/jpeg')
                    self.send_header('Content-Length', len(frame_data))
                    self.end_headers()
                    self.wfile.write(frame_data)
                    self.wfile.write(b'\r\n')
                    
                    frame_count += 1
                    
            except Exception as e:
                print(f"Stream closed: {e}")

if __name__ == '__main__':
    print(f"AI 服务运行中: http://{HOST_NAME}:{PORT_NUMBER}")
    print("首次运行 DeepFace 会下载模型 (约几百MB)，请保持网络通畅！")
    server = HTTPServer((HOST_NAME, PORT_NUMBER), StreamingHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        picam2.stop()
        server.server_close()