import time
import os
import cv2
import ollama
import threading
from picamera2 import Picamera2

# ================= 配置 =================
TEMP_IMAGE = "trigger_view.jpg"
# 提示词保持简短
PROMPT = "List the main objects visible." 
# =======================================

latest_frame = None
camera_running = True

def camera_thread():
    """ 摄像头后台线程 """
    global latest_frame, camera_running
    picam2 = Picamera2()
    # 稍微降低一点预览分辨率以节省带宽内存
    config = picam2.create_preview_configuration(
        main={"size": (640, 480), "format": "RGB888"},
        controls={"AfMode": 2}
    )
    picam2.configure(config)
    picam2.start()
    
    while camera_running:
        try:
            image_rgb = picam2.capture_array()
            # 原地转换，减少拷贝
            latest_frame = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR)
            time.sleep(0.05)
        except:
            pass
    picam2.stop()

def main():
    global latest_frame, camera_running
    
    # 启动摄像头
    t = threading.Thread(target=camera_thread)
    t.daemon = True
    t.start()
    time.sleep(2) # 等待摄像头

    print("\n" + "="*40)
    print("🚀 极速版 (内存优化开启)")
    print("👉 按 [回车] 识别 | 输入 'q' 退出")
    print("="*40)

    # 预热：强制带上参数，让 Ollama 知道我们要省内存
    print("🔥 正在加载模型 (请关注 htop 内存变化)...")
    try:
        ollama.chat(
            model='moondream', 
            messages=[{'role':'user','content':'hi'}],
            options={"num_ctx": 256, "num_thread": 4} # 预热时就锁定配置
        )
        print("✅ 模型已入驻内存！")
    except Exception as e:
        print(f"预热失败: {e}")

    try:
        while True:
            cmd = input("\nWaiting... (Enter/q): ")
            if cmd.lower() == 'q': break
            
            if latest_frame is None:
                print("❌ 摄像头忙")
                continue

            print("⚡ 计算中...", end="", flush=True)
            start_time = time.time()
            
            # 极致压缩输入图：256x256 对 Moondream 识别物体足够了
            # 图片越小，Visual Encoder 也就是“看”的过程越快
            small_frame = cv2.resize(latest_frame, (256, 256))
            cv2.imwrite(TEMP_IMAGE, small_frame)

            try:
                response = ollama.chat(
                    model='qnguyen3/nanollava',
                    messages=[{
                        'role': 'user',
                        'content': PROMPT,
                        'images': [TEMP_IMAGE]
                    }],
                    options={
                        "num_ctx": 2512,      # 【核心】上下文窗口极小化
                        "num_predict": 40,   # 【核心】少说废话
                        "temperature": 0.1,  # 【核心】无需创造性
                        "num_thread": 4      # 【核心】跑满4核
                    }
                )
                
                duration = time.time() - start_time
                result = response['message']['content'].strip()
                
                # 打印结果
                color_code = "\033[1;32m" if duration < 10 else "\033[1;31m"
                print(f"\r✅ {color_code}耗时: {duration:.1f}s\033[0m | 结果: {result}")

            except Exception as e:
                print(f"\n❌ 错误: {e}")

    except KeyboardInterrupt:
        pass
    finally:
        camera_running = False
        t.join()

if __name__ == "__main__":
    main()