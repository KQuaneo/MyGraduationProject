import os
import sys
import json
import pyaudio
from vosk import Model, KaldiRecognizer

# === 1. 引入配置文件 ===
try:
    import config
except ImportError:
    print("错误：找不到 config.py，请确保它在项目根目录下。")
    sys.exit(1)

# === 2. 引入大脑和嘴巴 ===
try:
    from modules.brain import chat_with_brain
    from modules.mouth import speak
except ImportError as e:
    print(f"导入模块失败: {e}")
    sys.exit(1)

# === 3. 引入眼睛显示模块（替换原来的 emotion_display）===
try:
    from modules.eyes import EyeDisplay
    EYE_DISPLAY_ENABLED = True
except ImportError as e:
    print(f"⚠️ 眼睛显示模块加载失败: {e}")
    EYE_DISPLAY_ENABLED = False


def run_voice_control():
    # ...existing code... (路径设置、模型加载等保持不变)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    model_path = os.path.join(current_dir, "model")

    if not os.path.exists(model_path):
        print(f"错误：找不到模型文件夹 -> {model_path}")
        sys.exit(1)
    
    SAMPLE_RATE = config.SAMPLE_RATE
    MIC_ID = config.MIC_ID
    
    print(f"正在加载语音模型...")
    
    model = Model(model_path)
    rec = KaldiRecognizer(model, SAMPLE_RATE)

    p = pyaudio.PyAudio()
    stream = p.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=SAMPLE_RATE,
        input=True,
        frames_per_buffer=8000,
        input_device_index=MIC_ID
    )
    stream.start_stream()
    
    # === 初始化眼睛显示 ===
    eye_display = None
    if EYE_DISPLAY_ENABLED:
        try:
            eye_display = EyeDisplay()
            fullscreen = getattr(config, 'EYE_FULLSCREEN', True)
            eye_display.start(fullscreen=fullscreen)
        except Exception as e:
            print(f"⚠️ 眼睛显示初始化失败: {e}")
            eye_display = None
    
    print("\n=== ✨ 具身智能小车已就绪 ✨ ===")

    try:
        while True:
            # 检查眼睛显示是否还在运行
            if eye_display and not eye_display.running:
                print("用户关闭了显示窗口")
                break
            
            data = stream.read(8000, exception_on_overflow=False)
            
            if rec.AcceptWaveform(data):
                result = json.loads(rec.Result())
                text = result.get("text", "").replace(" ", "")
                
                if len(text) > 1:
                    print(f"\n👂 听到: {text}")
                    stream.stop_stream()
                    
                    command = chat_with_brain(text)
                    
                    if command:
                        action = command.get('action')
                        reply = command.get('reply')
                        emotion = command.get('emotion', 'neutral')
                        
                        print(f"🤖 决策: {action} | 情绪: {emotion}")
                        
                        # === 更新眼睛表情 ===
                        if eye_display:
                            eye_display.update_emotion(emotion)
                        
                        speak(reply)
                    
                    if stream.is_stopped():
                        stream.start_stream()

    except KeyboardInterrupt:
        print("\n再见！")
    finally:
        if eye_display:
            eye_display.close()
        stream.stop_stream()
        stream.close()
        p.terminate()


if __name__ == "__main__":
    run_voice_control()