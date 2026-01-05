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
# 🧠 线程 1：AI 专门处理线程 (EMA 平滑稳定版)
# -----------------------------------------------------------
def ai_worker():
    global latest_frame_for_ai, ai_result_emotion, ai_result_score, ai_result_box
    
    # 1. 平滑系数 (0.1 ~ 0.3)
    SMOOTH_FACTOR = 0.2
    
    # 2. 【核心新增】情绪校准权重 (人为修正模型的偏见)
    # 现在的逻辑是：模型太爱报 sad 了，我们惩罚 sad，奖励 happy 和 neutral
    EMOTION_WEIGHTS = {
        'angry': 1.0, 
        'disgust': 0.0, 
        'fear': 1.0, 
        'happy': 3.0,    # 快乐加倍：让微笑更容易被识别
        'sad': 0.5,      # 悲伤打3折：除非真的痛哭流涕，否则很难触发 sad
        'surprise': 0.0, 
        'neutral': 2.0   # 中性加成：让“面无表情”更优先判定为 neutral 而不是 sad
    }
    
    # 初始化惯性分数
    ema_scores = {k: 0.0 for k in EMOTION_WEIGHTS}

    print(f"🧠 [后台] AI 启动 | 启用权重校准: Sad x{EMOTION_WEIGHTS['sad']}, Happy x{EMOTION_WEIGHTS['happy']}")
    
    try:
        dummy = np.zeros((100, 100, 3), dtype=np.uint8)
        DeepFace.analyze(dummy, actions=['emotion'], detector_backend='ssd', enforce_detection=False, silent=True)
        print("🧠 [后台] 模型就绪")
        with data_lock: ai_result_emotion = "Ready"
    except:
        pass

    while True:
        frame_to_analyze = None
        with data_lock:
            if latest_frame_for_ai is not None:
                frame_to_analyze = latest_frame_for_ai.copy()
        
        if frame_to_analyze is None:
            time.sleep(0.1)
            continue

        try:
            results = DeepFace.analyze(
                img_path = frame_to_analyze, 
                actions = ['emotion'], 
                detector_backend = 'ssd', 
                enforce_detection = False,
                silent = True
            )
            
            with data_lock:
                if results and len(results) > 0:
                    res = results[0]
                    if res['region']['w'] > 0:
                        raw_scores = res['emotion'] # 原始分数
                        
                        # =========================================
                        # 🔧 步骤 1: 权重校准 (解决 Sad 太多、微笑不识别的问题)
                        # =========================================
                        calibrated_scores = {}
                        for emo, score in raw_scores.items():
                            # 乘上我们需要的人为权重
                            calibrated_scores[emo] = score * EMOTION_WEIGHTS.get(emo, 1.0)
                        
                        # 特殊逻辑：如果快乐分数有一点苗头(>10)，就直接屏蔽掉 Sad
                        # 防止“苦笑”被识别成 Sad
                        if raw_scores['happy'] > 10.0:
                            calibrated_scores['sad'] = 0.0

                        # =========================================
                        # 🔧 步骤 2: EMA 动量平滑 (解决数值乱跳)
                        # =========================================
                        for emo, score in calibrated_scores.items():
                            ema_scores[emo] = (score * SMOOTH_FACTOR) + (ema_scores[emo] * (1.0 - SMOOTH_FACTOR))
                        
                        # 3. 选出冠军
                        winner_emotion = max(ema_scores, key=ema_scores.get)
                        
                        # 4. 计算显示的百分比 (因为我们加权了，所以要重新归一化一下，不然可能超过100%)
                        total_score = sum(ema_scores.values())
                        if total_score > 0:
                            final_percentage = (ema_scores[winner_emotion] / total_score) * 100
                        else:
                            final_percentage = 0.0

                        ai_result_emotion = winner_emotion
                        ai_result_score = final_percentage
                        
                        # 坐标
                        region = res['region']
                        ai_result_box = (region['x'], region['y'], region['w'], region['h'])
                    else:
                        ai_result_box = None
                        for k in ema_scores: ema_scores[k] *= 0.8
                else:
                    ai_result_box = None
                    for k in ema_scores: ema_scores[k] *= 0.8
                        
        except Exception:
            pass
            
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