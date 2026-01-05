import time
import io
import cv2
import numpy as np
import threading
import sys
import subprocess
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from picamera2 import Picamera2
from deepface import DeepFace
from collections import deque, Counter

# ================= 配置区域 =================
HOST_NAME = '0.0.0.0'
PORT_NUMBER = 8000

# 【升级1】不再缩小图片，使用原图识别，大幅提升准确率
AI_SCALE = 1.0 

# 【升级2】检测频率。SSD 模型稍慢，我们降低检测频率来保证不过热
# 0.1 表示每 10 秒只让它全速跑 0.1 秒？不是，这里用于 sleep
# 我们在代码里控制频率
# ===========================================

# 全局变量
data_lock = threading.Lock()
latest_frame_for_ai = None
ai_result_emotion = "Initializing..." 
ai_result_score = 0.0
ai_result_box = None

# AI 历史队列 (加长队列，让结果更稳定)
emotion_history = deque(maxlen=7)

# -----------------------------------------------------------
# 🧠 线程 1：AI 专门处理线程 (鹰眼模式)
# -----------------------------------------------------------
def ai_worker():
    global latest_frame_for_ai, ai_result_emotion, ai_result_score, ai_result_box, emotion_history
    
    print("🧠 [后台] AI 线程启动 | 模式: High Accuracy (SSD)")
    
    # 预热模型 (这次会加载 SSD 模型，可能需要几秒钟)
    try:
        dummy = np.zeros((100, 100, 3), dtype=np.uint8)
        DeepFace.analyze(
            img_path=dummy, 
            actions=['emotion'], 
            detector_backend='ssd', # 【关键升级】使用 SSD 检测器
            enforce_detection=False, 
            silent=True
        )
        print("🧠 [后台] SSD 模型加载完毕，准备就绪！")
        with data_lock: ai_result_emotion = "Ready"
    except Exception as e:
        print(f"预热警告: {e}")

    while True:
        frame_to_analyze = None
        with data_lock:
            if latest_frame_for_ai is not None:
                frame_to_analyze = latest_frame_for_ai.copy()
        
        if frame_to_analyze is None:
            time.sleep(0.1)
            continue

        try:
            # 根据配置缩放 (现在是 1.0 原图)
            if AI_SCALE != 1.0:
                input_frame = cv2.resize(frame_to_analyze, (0, 0), fx=AI_SCALE, fy=AI_SCALE)
            else:
                input_frame = frame_to_analyze

            # --- 核心识别 ---
            results = DeepFace.analyze(
                img_path = input_frame, 
                actions = ['emotion'], 
                # 【关键升级】这里改成了 'ssd'，它是准确率的关键！
                # 如果觉得 Pi 5 实在太烫，可以改回 'opencv'，但为了准确率建议保留 ssd
                detector_backend = 'ssd', 
                enforce_detection = False,
                silent = True
            )
            
            with data_lock:
                if results and len(results) > 0:
                    res = results[0]
                    
# -------------------------------------------------------
                    # 替换开始：带有“快乐滤镜”的逻辑
                    # -------------------------------------------------------
                    if res['region']['w'] > 0:
                        # 获取所有表情的原始分数 (字典: {'angry': 20.1, 'happy': 15.5, ...})
                        emotions_dict = res['emotion']
                        
                        # 1. 人工修正：如果“开心”的分数超过 5%，就屏蔽掉“生气”
                        # 因为在正常交互中，微弱的开心比微弱的生气更常见，且容易混淆
                        if emotions_dict['happy'] > 5.0:
                            emotions_dict['angry'] = 0.0
                        
                        # 2. 重新计算最大值对应的表情
                        # max(字典, key=字典.get) 会返回分数最高的那个键
                        adjusted_emotion = max(emotions_dict, key=emotions_dict.get)
                        
                        # 3. 只有当置信度比较高时才采纳，否则算 Neutral
                        if emotions_dict[adjusted_emotion] < 40.0:
                             adjusted_emotion = 'neutral'

                        # 加入历史队列
                        emotion_history.append(adjusted_emotion)
                        
                        if len(emotion_history) > 0:
                            # 投票
                            most_common = Counter(emotion_history).most_common(1)[0]
                            ai_result_emotion = most_common[0]
                            # 获取修正后的分数
                            ai_result_score = emotions_dict[ai_result_emotion]
                            
                            # 坐标还原
                            region = res['region']
                            scale = 1 / AI_SCALE
                            ai_result_box = (
                                int(region['x'] * scale),
                                int(region['y'] * scale),
                                int(region['w'] * scale),
                                int(region['h'] * scale)
                            )
                    # -------------------------------------------------------
                    # 替换结束
                    # -------------------------------------------------------
                    else:
                        ai_result_box = None
                else:
                    ai_result_box = None
                    # 只有连续多次没检测到，才显示 No Face (防闪烁)
                    if len(emotion_history) > 0: emotion_history.popleft()
                    else: ai_result_emotion = "Scanning..."
                        
        except Exception as e:
            # print(f"AI Log: {e}") # 调试时可打开
            pass
            
        # 识别间隔：SSD 比较耗资源，每次识别完休息 0.05秒
        # 这样既保证了识别率，又不会卡死 CPU
        time.sleep(0.05)

# -----------------------------------------------------------
# 📷 主程序初始化
# -----------------------------------------------------------
print("📷 正在初始化摄像头 (开启自动对焦)...")
try:
    picam2 = Picamera2()
    
    # 【升级3】开启连续自动对焦 (AfMode: 2)
    # 这对于 Module 3 至关重要，否则脸是糊的，神仙也识别不出来
    config = picam2.create_preview_configuration(
        main={"size": (640, 480), "format": "RGB888"},
        controls={"AfMode": 2} 
    )
    picam2.configure(config)
    picam2.start()
    print("✅ 摄像头已启动 | 自动对焦: ON")
    
    threading.Thread(target=ai_worker, daemon=True).start()
    
except Exception as e:
    print(f"❌ 启动失败: {e}")
    sys.exit(1)

# -----------------------------------------------------------
# 🌐 Web 服务器
# -----------------------------------------------------------
class StreamingHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global latest_frame_for_ai
        
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"""
                <html>
                <head><title>Pi 5 High-Res AI</title></head>
                <body style="background: #222; margin: 0; display: flex; flex-direction: column; justify-content: center; align-items: center; height: 100vh; color: #fff; font-family: sans-serif;">
                    <h2>Emotion AI (SSD Model + Autofocus)</h2>
                    <img src="/stream.mjpg" style="max-width: 100%; border: 4px solid #444; border-radius: 8px;" />
                </body>
                </html>
            """)
        elif self.path == '/stream.mjpg':
            self.send_response(200)
            self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=FRAME')
            self.end_headers()
            
            try:
                while True:
                    image = picam2.capture_array()
                    image_bgr = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
                    
                    # 更新 AI 数据
                    with data_lock:
                        latest_frame_for_ai = image_bgr
                        curr_emo = ai_result_emotion
                        curr_score = ai_result_score
                        curr_box = ai_result_box

                    # --- 绘制 UI ---
                    # 状态栏
                    overlay = image_bgr.copy()
                    cv2.rectangle(overlay, (0, 0), (640, 50), (0, 0, 0), -1)
                    image_bgr = cv2.addWeighted(overlay, 0.6, image_bgr, 0.4, 0)
                    
                    status_text = f"AI: {curr_emo.upper()}"
                    if curr_box: status_text += f" ({curr_score:.0f}%)"
                    
                    # 颜色逻辑
                    color = (200, 200, 200)
                    if curr_emo in ["happy", "surprise"]: color = (0, 255, 0) # 绿
                    elif curr_emo in ["sad", "fear", "angry"]: color = (0, 0, 255) # 红
                    elif curr_emo == "neutral": color = (0, 255, 255) # 黄
                    
                    cv2.putText(image_bgr, status_text, (15, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)

                    # 人脸框
                    if curr_box:
                        x, y, w, h = curr_box
                        cv2.rectangle(image_bgr, (x, y), (x+w, y+h), color, 2)

                    # 发送
                    image_final = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
                    ret, jpeg = cv2.imencode('.jpg', image_final)
                    if ret:
                        frame_data = jpeg.tobytes()
                        self.wfile.write(b'--FRAME\r\n')
                        self.send_header('Content-Type', 'image/jpeg')
                        self.send_header('Content-Length', len(frame_data))
                        self.end_headers()
                        self.wfile.write(frame_data)
                        self.wfile.write(b'\r\n')
                    
                    time.sleep(0.02) # 30-50 FPS Video Stream
                    
            except Exception as e:
                pass

if __name__ == '__main__':
    print("-" * 50)
    print(f"🚀 高精度服务启动中...")
    try:
        ip = subprocess.check_output(['hostname', '-I']).decode('utf-8').split()[0]
        print(f"👉 访问地址: http://{ip}:{PORT_NUMBER}")
    except:
        print(f"👉 访问地址: http://localhost:{PORT_NUMBER}")
    print("-" * 50)
        
    server = ThreadingHTTPServer((HOST_NAME, PORT_NUMBER), StreamingHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        picam2.stop()
        server.server_close()