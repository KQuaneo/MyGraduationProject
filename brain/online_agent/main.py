import os
import sys
import json
import pyaudio
import threading
import time
import array  # 用于替代 audioop 做声道转换
from vosk import Model, KaldiRecognizer

# === 1. 引入配置文件 ===
try:
    import config
except ImportError:
    print("错误：找不到 config.py")
    sys.exit(1)

# === 2. 引入大脑和嘴巴 ===
try:
    from modules.brain import chat_with_brain
    from modules.mouth import speak
except ImportError as e:
    print(f"导入模块失败: {e}")
    sys.exit(1)

# === 3. 引入眼睛显示模块 ===
try:
    from modules.emotion_animation_display import EyeDisplay
    EYE_DISPLAY_ENABLED = True
except ImportError as e:
    print(f"⚠️ 眼睛显示模块加载失败: {e}")
    EYE_DISPLAY_ENABLED = False


# ==========================================
#  后台线程：负责听觉、思考和说话
# ==========================================
def audio_logic_thread(eye_display):
    print("🎧 语音线程已启动...")
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    model_path = os.path.join(current_dir, "model")

    if not os.path.exists(model_path):
        print(f"错误：找不到模型文件夹 -> {model_path}")
        return

    # 初始化语音识别
    stream = None
    p = None
    
    try:
        model = Model(model_path)
        SAMPLE_RATE = config.SAMPLE_RATE
        MIC_ID = config.MIC_ID
        rec = KaldiRecognizer(model, SAMPLE_RATE)
        
        p = pyaudio.PyAudio()
        
        # --- 智能麦克风选择逻辑 (修复 ID 报错) ---
        target_mic_id = MIC_ID
        input_channels = 1
        
        try:
            # 1. 尝试获取指定 ID 的信息
            dev_info = p.get_device_info_by_index(MIC_ID)
            hw_channels = int(dev_info['maxInputChannels'])
            # 硬件至少2个声道就申请2个，否则申请1个
            input_channels = hw_channels if hw_channels >= 2 else 1
            print(f"🎤 尝试使用指定麦克风 ID: {MIC_ID}, 声道: {input_channels}")
            
        except Exception as e:
            # 2. 如果指定 ID 失败，尝试寻找系统默认设备
            print(f"⚠️ 指定 ID {MIC_ID} 无效，尝试使用系统默认麦克风... ({e})")
            try:
                default_info = p.get_default_input_device_info()
                target_mic_id = default_info['index'] # 更新为默认 ID
                hw_channels = int(default_info['maxInputChannels'])
                input_channels = hw_channels if hw_channels >= 2 else 1
                print(f"🎤 已切换到默认麦克风 ID: {target_mic_id} ({default_info['name']})")
            except Exception as e2:
                print(f"❌ 致命错误：找不到任何麦克风！{e2}")
                return # 彻底没救了，退出线程

        # 3. 打开音频流
        stream = p.open(
            format=pyaudio.paInt16,
            channels=input_channels,
            rate=SAMPLE_RATE,
            input=True,
            frames_per_buffer=8000,
            input_device_index=target_mic_id
        )
        stream.start_stream()
        
        print("\n=== ✨ 具身智能小车已就绪 (语音后台运行中) ✨ ===")
        
        while True:
            # 如果主线程的眼睛关闭了，这里也退出
            if EYE_DISPLAY_ENABLED and eye_display and not eye_display.running:
                print("检测到界面关闭，停止语音线程")
                break

            data = stream.read(8000, exception_on_overflow=False)
            
            # --- 修复 audioop 缺失问题 (Python 3.13) ---
            if input_channels > 1:
                # 使用 array 库高效处理二进制音频数据
                # 将原始字节流转换为 16-bit 整数数组 'h'
                shorts = array.array('h', data)
                # 提取左声道 (每隔 input_channels 个采样取一个)
                mono_shorts = shorts[::input_channels]
                # 转回字节流
                data = mono_shorts.tobytes()
            # ---------------------------

            if rec.AcceptWaveform(data):
                result = json.loads(rec.Result())
                text = result.get("text", "").replace(" ", "")
                
                if len(text) > 1:
                    print(f"\n👂 听到: {text}")
                    # 思考时暂停听觉
                    stream.stop_stream()
                    
                    # 1. 思考状态
                    if eye_display: eye_display.update_emotion("thinking") 
                    
                    # 2. 调用大脑
                    command = chat_with_brain(text)
                    
                    if command:
                        action = command.get('action')
                        reply = command.get('reply')
                        emotion = command.get('emotion', 'neutral')
                        
                        print(f"🤖 决策: {action} | 情绪: {emotion}")
                        
                        # 3. 更新表情
                        if eye_display:
                            eye_display.update_emotion(emotion)
                        
                        # 4. 说话
                        speak(reply)
                    
                    # 恢复听觉
                    if stream.is_stopped():
                        stream.start_stream()
                        
    except Exception as e:
        print(f"❌ 语音线程出错: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if stream: 
            stream.stop_stream()
            stream.close()
        if p: 
            p.terminate()

# ==========================================
#  主线程：只负责 UI (Pygame)
# ==========================================
def main():
    # 1. 准备眼睛对象
    eye_display = None
    if EYE_DISPLAY_ENABLED:
        eye_display = EyeDisplay()
        # 注意：这里我们不调用 start()，因为不要它自己开线程
        # 我们只是创建实例，稍后手动在主线程跑循环
        eye_display.running = True # 手动标记为运行中

    # 2. 启动语音后台线程
    t = threading.Thread(target=audio_logic_thread, args=(eye_display,), daemon=True)
    t.start()

    # 3. 在主线程运行 GUI (必须这样做！)
    if eye_display:
        try:
            # 这里的 fullscreen=True/False 根据你的需要调整
            # 建议使用 True 以获得全屏效果
            eye_display._run_loop(fullscreen=True) 
        except KeyboardInterrupt:
            pass
        finally:
            eye_display.running = False # 通知子线程退出
    else:
        # 如果没有眼睛模块，主线程就傻等，防止程序退出
        try:
            while True: time.sleep(1)
        except KeyboardInterrupt:
            pass

if __name__ == "__main__":
    main()