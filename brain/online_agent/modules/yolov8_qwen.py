import cv2
import time
import threading
import dashscope
import os
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn
from picamera2 import Picamera2
from ultralytics import YOLO
from http import HTTPStatus

# === 尝试导入配置 ===
try:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(current_dir)
    sys.path.append(root_dir)
    import config
    DASHSCOPE_API_KEY = config.DASHSCOPE_API_KEY
    CLOUD_MODEL = "qwen-vl-plus" 
    YOLO_MODEL = "yolov8n.pt"
except:
    # 备用配置
    DASHSCOPE_API_KEY = "sk-c77cfbdc9a5643d8b3d7ac8c6cfd1572" 
    CLOUD_MODEL = "qwen-vl-plus"
    YOLO_MODEL = "yolov8n.pt"

HOST_PORT = 8000

# === 全局变量 ===
latest_frame = None
output_frame = None
frame_lock = threading.Lock()
analysis_result = "Ready."
is_analyzing = False

class VideoStreamHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global analysis_result
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
                    time.sleep(0.05)
            except Exception:
                pass
        else:
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(b'<h1>Robot Vision Running</h1><img src="/stream.mjpg" />')

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle requests in a separate thread."""

class VisionSystem:
    def __init__(self):
        dashscope.api_key = DASHSCOPE_API_KEY
        self.yolo = None
        self.running = True
        
        # 存储最近的人体面积占比 (0.0 ~ 1.0)
        self.closest_person_area = 0.0 
        
        # [修改 1] 新增：最近的人体中心点坐标 
        # Range: -1.0 (最左) ~ 0.0 (正中) ~ 1.0 (最右)
        # None 表示没看到人
        self.closest_person_center_x = None 
        
        # 启动后台线程
        threading.Thread(target=self._camera_loop, daemon=True).start()
        threading.Thread(target=self._ai_loop, daemon=True).start()
        threading.Thread(target=self._server_loop, daemon=True).start()
        
        print("✅ [Vision] 视觉系统已启动 (YOLO 距离+方向感知 + 云端识别)")

    def _camera_loop(self):
        global latest_frame
        picam2 = Picamera2()
        # 注意：这里设定了采集分辨率为 640x480
        config = picam2.create_preview_configuration(
            main={"size": (640, 480), "format": "RGB888"},
            controls={"AfMode": 2}
        )
        picam2.configure(config)
        picam2.start()
        while self.running:
            img_rgb = picam2.capture_array()
            with frame_lock:
                latest_frame = img_rgb
                # 如果颜色反了，解开下面这行
                # latest_frame = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)
            time.sleep(0.03)
        picam2.stop()

    def _ai_loop(self):
        global output_frame, analysis_result, latest_frame
        print("🚀 [Vision] Loading YOLO...")
        self.yolo = YOLO(YOLO_MODEL)
        
        # 画面尺寸 (必须与 _camera_loop 中的一致)
        FRAME_WIDTH = 640
        FRAME_HEIGHT = 480
        TOTAL_PIXELS = FRAME_WIDTH * FRAME_HEIGHT
        
        while self.running:
            with frame_lock:
                if latest_frame is None:
                    time.sleep(0.1)
                    continue
                current_frame = latest_frame.copy()

            # YOLO 推理
            results = self.yolo(current_frame, stream=True, verbose=False, imgsz=320)
            
            # 初始化本帧的数据
            max_area_ratio = 0.0
            target_center_x = None # 默认没找到人
            
            for r in results:
                current_frame = r.plot()
                
                for box in r.boxes:
                    cls_id = int(box.cls[0])
                    
                    if cls_id == 0: # 0 代表 person
                        # 获取坐标 (x1, y1, x2, y2)
                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy() # 确保转为 numpy 处理
                        
                        # 计算面积
                        width = x2 - x1
                        height = y2 - y1
                        area = width * height
                        
                        # 计算占比
                        ratio = float(area) / TOTAL_PIXELS
                        
                        # [修改 2] 核心逻辑：找最大（最近）的人，并记录它的中心点
                        if ratio > max_area_ratio:
                            max_area_ratio = ratio
                            
                            # 计算中心点像素坐标 (0 ~ 640)
                            center_pixel_x = (x1 + x2) / 2
                            
                            # 归一化到 -1.0 ~ 1.0
                            # (当前x - 图宽一半) / 图宽一半
                            target_center_x = (center_pixel_x - FRAME_WIDTH / 2) / (FRAME_WIDTH / 2)
            
            # [修改 3] 更新全局变量供 Main 使用
            self.closest_person_area = max_area_ratio
            self.closest_person_center_x = target_center_x

            # 绘制状态文字
            status_text = f"Area: {max_area_ratio:.2f}"
            if target_center_x is not None:
                status_text += f" | X: {target_center_x:.2f}"
            else:
                status_text += " | No Target"
                
            cv2.putText(current_frame, status_text, (10, 450), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            
            cv2.putText(current_frame, analysis_result, (10, 475), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

            with frame_lock:
                output_frame = current_frame
            time.sleep(0.01)

    def _server_loop(self):
        server = ThreadedHTTPServer(('0.0.0.0', HOST_PORT), VideoStreamHandler)
        print(f"📡 [Vision] 视频流地址: http://<IP>:{HOST_PORT}/stream.mjpg")
        server.serve_forever()

    def analyze_now(self, prompt="请用中文描述你看到的画面。"):
        global analysis_result, latest_frame, is_analyzing
        
        if is_analyzing:
            return "我正在看呢，请稍等..."
        
        with frame_lock:
            if latest_frame is None:
                return "摄像头还没准备好。"
            img_to_upload = latest_frame.copy()

        is_analyzing = True
        analysis_result = "Thinking (Cloud AI)..."
        print(f"☁️ [Vision] 正在请求通义千问... (Prompt: {prompt})")

        try:
            # 路径处理: 存到 temp 文件夹
            current_file_dir = os.path.dirname(os.path.abspath(__file__))
            root_path = os.path.dirname(current_file_dir)
            temp_dir = os.path.join(root_path, "temp")
            
            if not os.path.exists(temp_dir):
                os.makedirs(temp_dir)

            temp_file_path = os.path.join(temp_dir, "vision_cache.jpg")
            
            # 保存图片
            cv2.imwrite(temp_file_path, img_to_upload)
            img_path_for_api = f"file://{temp_file_path}"

            # 调用 DashScope API
            response = dashscope.MultiModalConversation.call(
                model=CLOUD_MODEL,
                messages=[{
                    "role": "user",
                    "content": [
                        {"image": img_path_for_api},
                        {"text": prompt} 
                    ]
                }]
            )

            if response.status_code == HTTPStatus.OK:
                text = response.output.choices[0].message.content[0]['text']
                print(f"✅ [Vision] 识别结果: {text}")
                
                # 更新画面上的文字显示
                display_text = text[:15] + "..." if len(text) > 15 else text
                analysis_result = display_text
                
                return text
            else:
                print(f"Error: {response.code} - {response.message}")
                return "看不清，云端出错了。"

        except Exception as e:
            print(f"❌ [Vision] Error: {e}")
            return "眼睛出问题了。"
        finally:
            is_analyzing = False