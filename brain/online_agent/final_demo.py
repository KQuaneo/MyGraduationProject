import cv2
import time
import threading
import ollama
from picamera2 import Picamera2
from ultralytics import YOLO
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn

# ================= 核心配置 =================
OLLAMA_MODEL = "qnguyen3/nanollava"
YOLO_MODEL = "yolov8n.pt" 
HOST_PORT = 8000
# ===========================================

# 全局变量
latest_frame = None     
output_frame = None     
frame_lock = threading.Lock()
analyzing = False
analysis_result = "Ready. Click 'Analyze' to start."

class VideoStreamHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global analyzing
        
        # 1. 视频流路由
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
                        # 编码为 JPEG
                        ret, jpeg = cv2.imencode('.jpg', output_frame)
                        frame_data = jpeg.tobytes()
                    
                    # 发送分块数据
                    self.wfile.write(b'--FRAME\r\n')
                    self.send_header('Content-Type', 'image/jpeg')
                    self.send_header('Content-Length', len(frame_data))
                    self.end_headers()
                    self.wfile.write(frame_data)
                    self.wfile.write(b'\r\n')
                    time.sleep(0.04) 
            except Exception as e:
                pass

        # 2. 触发分析路由 (API)
        elif self.path == '/analyze':
            if not analyzing:
                threading.Thread(target=run_deep_analysis).start()
                self.send_response(200)
                self.wfile.write(b"Analysis Started")
            else:
                self.send_response(429) 
                self.wfile.write(b"Busy")

        # 3. 主页 (HTML Dashboard)
        else:
            self.send_response(200)
            # 关键修改：指明 charset=utf-8
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            
            # 关键修改：去掉 b 前缀，使用 .encode('utf-8')
            html_content = """
                <html>
                <head>
                    <title>Pi 5 AI Dashboard</title>
                    <meta charset="UTF-8">
                    <style>
                        body { background: #1a1a1a; color: white; font-family: sans-serif; text-align: center; margin: 0; padding: 20px; }
                        h1 { margin-bottom: 10px; color: #00ff00; }
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
                        <h1>Raspberry Pi 5 AI Vision</h1>
                        <img src="/stream.mjpg" />
                        
                        <div class="controls">
                            <button id="btn" onclick="triggerAnalysis()">🧠 Deep Analysis (NanoLLaVA)</button>
                        </div>
                        <div id="status">System Ready.</div>
                    </div>

                    <script>
                        function triggerAnalysis() {
                            const btn = document.getElementById('btn');
                            const status = document.getElementById('status');
                            
                            btn.disabled = true;
                            btn.innerText = "Thinking...";
                            status.innerText = "Request sent to AI...";

                            fetch('/analyze').then(() => {
                                setTimeout(() => {
                                    btn.disabled = false;
                                    btn.innerText = "🧠 Deep Analysis (NanoLLaVA)";
                                    status.innerText = "Check video feed for results.";
                                }, 5000); 
                            });
                        }
                    </script>
                </body>
                </html>
            """
            self.wfile.write(html_content.encode('utf-8'))

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle requests in a separate thread."""

def run_deep_analysis():
    global analyzing, analysis_result, latest_frame
    
    with frame_lock:
        if latest_frame is None: return
        img_for_ai = latest_frame.copy()
    
    analyzing = True
    analysis_result = "Analyzing..." # 界面状态更新
    print("\n🧠 [AI] 极速分析中...")

    try:
        start_time = time.time()
        
        # 【核弹优化 1】分辨率降至 96x96
        # 这已经是人类能看清物体的极限，也是 AI 速度的极限
        small_img = cv2.resize(img_for_ai, (96, 96))
        cv2.imwrite("temp_web.jpg", small_img)

        # 【核弹优化 2】提示词工程 (Prompt Engineering)
        # 不求"描述"，只求"命名"。这能极大减少废话。
        response = ollama.chat(
            model=OLLAMA_MODEL,
            messages=[{
                'role': 'user', 
                # 这种问法比 "List items" 更容易得到单词回答
                'content': 'What is the main object? Answer in 1 word.', 
                'images': ['temp_web.jpg']
            }],
            options={
                "num_ctx": 256,
                "num_thread": 4,
                "num_predict": 10,   # 进一步限制，防止它啰嗦
                "temperature": 0
            }
        )
        
        duration = time.time() - start_time
        # 暴力清洗：去掉所有标点和 "The"
        text = response['message']['content'].strip()
        text = text.replace("The image shows", "").replace("a ", "").replace(".", "").strip()
        
        time_str = f"⏱️{duration:.1f}s"
        print(f"✅ 完成! {time_str} | 结果: {text}")
        
        analysis_result = f"[{time_str}] {text}"

    except Exception as e:
        print(f"❌ Error: {e}")
        analysis_result = "Error"
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
        
        if not analyzing:
            results = yolo(current_frame, stream=True, verbose=False, imgsz=320)
            for r in results:
                current_frame = r.plot()
            status_text = "Real-time Detection"
            color = (0, 255, 0)
        else:
            status_text = "Deep Analysis Running..."
            color = (0, 0, 255)
            cv2.putText(current_frame, "AI THINKING...", (200, 240), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)

        cv2.rectangle(current_frame, (0, 0), (640, 40), (0,0,0), -1)
        cv2.putText(current_frame, status_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        
        cv2.rectangle(current_frame, (0, 440), (640, 480), (0,0,0), -1)
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
    print(f"🌍 服务已启动！请在浏览器访问: http://<树莓派IP>:{HOST_PORT}")
    print(f"==========================================\n")
    
    server = ThreadedHTTPServer(('0.0.0.0', HOST_PORT), VideoStreamHandler)
    server.serve_forever()

if __name__ == "__main__":
    main()