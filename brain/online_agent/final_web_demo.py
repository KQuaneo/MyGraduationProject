import cv2
import time
import threading
import base64
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn
from picamera2 import Picamera2
from ultralytics import YOLO

# ================= ☁️ 云端配置 =================
import dashscope
from http import HTTPStatus

# ⚠️⚠️⚠️ 请在这里填入你的阿里云 API Key ⚠️⚠️⚠️
dashscope.api_key = "sk-c77cfbdc9a5643d8b3d7ac8c6cfd1572"

# 使用通义千问视觉模型 (效果好且快)
CLOUD_MODEL = "qwen-vl-plus" 
# 本地 YOLO 依然保留
YOLO_MODEL = "yolov8n.pt" 
HOST_PORT = 8000
# ===============================================

# 全局变量
latest_frame = None     
output_frame = None     
frame_lock = threading.Lock()
analyzing = False
analysis_result = "Ready. Click 'Analyze' to start."

class VideoStreamHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global analyzing
        
        if self.path == '/stream.mjpg':
            self.send_response(200)
            self.send_header('Content-type', 'multipart/x-mixed-replace; boundary=FRAME')
            self.end_headers()
            try:
                while True:
                    with frame_lock:
                        if output_frame is None:
                            time.sleep(0.01)
                            continue
                        ret, jpeg = cv2.imencode('.jpg', output_frame)
                        frame_data = jpeg.tobytes()
                    
                    self.wfile.write(b'--FRAME\r\n')
                    self.send_header('Content-Type', 'image/jpeg')
                    self.send_header('Content-Length', len(frame_data))
                    self.end_headers()
                    self.wfile.write(frame_data)
                    self.wfile.write(b'\r\n')
                    time.sleep(0.04) 
            except Exception:
                pass

        elif self.path == '/analyze':
            if not analyzing:
                threading.Thread(target=run_cloud_analysis).start()
                self.send_response(200)
                self.wfile.write(b"Analysis Started")
            else:
                self.send_response(429) 
                self.wfile.write(b"Busy")

        else:
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            html_content = """
                <html>
                <head>
                    <title>Pi 5 Cloud AI Vision</title>
                    <meta charset="UTF-8">
                    <style>
                        body { background: #1a1a1a; color: white; font-family: sans-serif; text-align: center; margin: 0; padding: 20px; }
                        h1 { margin-bottom: 10px; color: #00e5ff; } /* 换个云端的蓝色 */
                        .container { display: flex; flex-direction: column; align-items: center; }
                        img { border: 2px solid #444; border-radius: 8px; max-width: 100%; height: auto; box-shadow: 0 0 20px rgba(0,0,0,0.5); }
                        .controls { margin-top: 20px; }
                        button { 
                            padding: 15px 30px; font-size: 20px; background: #007bff; color: white; 
                            border: none; border-radius: 5px; cursor: pointer; transition: 0.3s;
                        }
                        button:hover { background: #0056b3; }
                        button:disabled { background: #555; cursor: not-allowed; }
                        #status { margin-top: 20px; font-size: 18px; color: #ffcc00; min-height: 30px;}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <h1>☁️ Pi 5 Cloud AI (Qwen-VL)</h1>
                        <img src="/stream.mjpg" />
                        
                        <div class="controls">
                            <button id="btn" onclick="triggerAnalysis()">🚀 Ask Cloud AI</button>
                        </div>
                        <div id="status">System Ready.</div>
                    </div>

                    <script>
                        function triggerAnalysis() {
                            const btn = document.getElementById('btn');
                            const status = document.getElementById('status');
                            
                            btn.disabled = true;
                            btn.innerText = "Uploading & Analyzing...";
                            status.innerText = "Sending to Alibaba Cloud...";

                            fetch('/analyze').then(() => {
                                setTimeout(() => {
                                    btn.disabled = false;
                                    btn.innerText = "🚀 Ask Cloud AI";
                                    status.innerText = "Check video feed for results.";
                                }, 3000); // 云端很快，3秒冷却够了
                            });
                        }
                    </script>
                </body>
                </html>
            """
            self.wfile.write(html_content.encode('utf-8'))

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle requests in a separate thread."""

def run_cloud_analysis():
    global analyzing, analysis_result, latest_frame
    
    with frame_lock:
        if latest_frame is None: return
        img_for_ai = latest_frame.copy()
    
    analyzing = True
    analysis_result = "Uploading to Cloud..." 
    print("\n☁️ [Cloud] 正在上传图片到云端...")

    try:
        start_time = time.time()
        
        # 1. 保存临时图片 (云端模型能力强，不需要压到 96x96，给个 640x480 都没问题)
        # 这里用 640x480 保证识别精度
        cv2.imwrite("temp_cloud.jpg", img_for_ai)
        
        # 2. 调用阿里云 SDK
        # 注意：DashScope 需要本地文件路径格式为 file://...
        img_path = "file://./temp_cloud.jpg"
        
        response = dashscope.MultiModalConversation.call(
            model=CLOUD_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"image": img_path},
                        {"text": "Describe this image in one short sentence."} # 你可以问得更复杂了！
                    ]
                }
            ]
        )

        duration = time.time() - start_time
        
        if response.status_code == HTTPStatus.OK:
            text = response.output.choices[0].message.content[0]['text']
            print(f"✅ [Cloud] 完成! ({duration:.1f}s): {text}")
            analysis_result = f"☁️: {text} ({duration:.1f}s)"
            
            # 语音播报 (可选)
            # import os
            # os.system(f"espeak -v en-us+f3 '{text}' &")
        else:
            print(f"❌ Cloud Error: {response.code} - {response.message}")
            analysis_result = f"Error: {response.message}"

    except Exception as e:
        print(f"❌ Local Error: {e}")
        analysis_result = "Network Error"
    finally:
        analyzing = False

def ai_loop():
    global output_frame, analysis_result, latest_frame
    
    print("🚀 Loading YOLO...")
    yolo = YOLO(YOLO_MODEL)
    print("✅ YOLO Ready!")

    while True:
        if latest_frame is None:
            time.sleep(0.1)
            continue

        current_frame = latest_frame.copy()
        
        # 即使云端在跑，YOLO 也可以继续跑！因为云端不占 CPU！
        # 我们可以实现真正的"双线程"操作
        results = yolo(current_frame, stream=True, verbose=False, imgsz=320)
        for r in results:
            current_frame = r.plot()
        
        if not analyzing:
            status_text = "Real-time Detection + Cloud Ready"
            color = (0, 255, 0)
        else:
            status_text = "Wait for Cloud Response..."
            color = (255, 165, 0) # 橙色
            cv2.putText(current_frame, "CLOUD ANALYZING...", (200, 240), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 165, 0), 3)

        cv2.rectangle(current_frame, (0, 0), (640, 40), (0,0,0), -1)
        cv2.putText(current_frame, status_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        
        cv2.rectangle(current_frame, (0, 440), (640, 480), (0,0,0), -1)
        # 支持中文显示比较麻烦，我们还是用英文
        cv2.putText(current_frame, analysis_result, (10, 470), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

        with frame_lock:
            output_frame = current_frame

        time.sleep(0.01)

def camera_thread_func():
    global latest_frame
    picam2 = Picamera2()
    config = picam2.create_preview_configuration(
        main={"size": (640, 480), "format": "RGB888"},
        controls={"AfMode": 2}
    )
    picam2.configure(config)
    picam2.start()
    while True:
        img_rgb = picam2.capture_array()
        latest_frame = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)
        time.sleep(0.02)

def main():
    threading.Thread(target=camera_thread_func, daemon=True).start()
    threading.Thread(target=ai_loop, daemon=True).start()

    print(f"\n==========================================")
    print(f"☁️ 云端版服务启动！访问: http://<树莓派IP>:8000")
    print(f"🔑 请确保 API Key 已填入代码")
    print(f"==========================================\n")
    
    server = ThreadedHTTPServer(('0.0.0.0', HOST_PORT), VideoStreamHandler)
    server.serve_forever()

if __name__ == "__main__":
    main()