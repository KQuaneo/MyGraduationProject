import os
import sys
import json
import pyaudio
from vosk import Model, KaldiRecognizer

# === 1. 引入配置文件 ===
# (确保 config.py 在同一目录下)
try:
    import config
except ImportError:
    print("错误：找不到 config.py，请确保它在项目根目录下。")
    sys.exit(1)

# === 2. 引入大脑和嘴巴 (从 modules 文件夹) ===
try:
    from modules.brain import chat_with_brain
    from modules.mouth import speak
except ImportError as e:
    print(f"导入模块失败: {e}")
    print("请确认 modules 文件夹下有 brain.py, mouth.py 和 __init__.py")
    sys.exit(1)

def run_voice_control():
    # === 路径设置 ===
    # 获取当前脚本(main.py)所在的绝对路径
    current_dir = os.path.dirname(os.path.abspath(__file__))
    model_path = os.path.join(current_dir, "model")

    if not os.path.exists(model_path):
        print(f"错误：找不到模型文件夹 -> {model_path}")
        print("请确认你已经下载并解压了 Vosk 模型到该目录下。")
        sys.exit(1)
    
    # === 从 Config 读取参数 ===
    SAMPLE_RATE = config.SAMPLE_RATE
    MIC_ID = config.MIC_ID
    
    print(f"正在加载语音模型 (采样率: {SAMPLE_RATE}, 麦克风ID: {MIC_ID})...")
    
    # 加载模型
    try:
        model = Model(model_path)
    except Exception as e:
        print(f"模型加载失败: {e}")
        sys.exit(1)

    # 告诉 Vosk 我们现在的采样率
    rec = KaldiRecognizer(model, SAMPLE_RATE)

    p = pyaudio.PyAudio()
    
    # === 录音流配置 ===
    stream_kwargs = {
        'format': pyaudio.paInt16,
        'channels': 1,
        'rate': SAMPLE_RATE,
        'input': True,
        'frames_per_buffer': 8000,
        'input_device_index': MIC_ID  # <--- 使用配置文件的 ID
    }
    
    try:
        stream = p.open(**stream_kwargs)
    except OSError as e:
        print(f"\n无法打开麦克风 (ID: {MIC_ID}): {e}")
        print("建议：")
        print("1. 检查 config.py 里的 MIC_ID 和 SAMPLE_RATE 是否正确")
        print("2. 运行 tools/check_mic.py 重新查看设备 ID")
        sys.exit(1)

    stream.start_stream()
    
    print("\n=== ✨ 具身智能小车已就绪 (树莓派版) ✨ ===")
    print(f"当前角色: {config.TTS_VOICE}")
    print("请对着麦克风说话...")

    try:
        while True:
            # 读取数据
            data = stream.read(8000, exception_on_overflow=False)
            
            # Vosk 识别
            if rec.AcceptWaveform(data):
                result = json.loads(rec.Result())
                text = result.get("text", "").replace(" ", "")
                
                if len(text) > 1:
                    print(f"\n👂 听到: {text}")
                    
                    # 1. === 暂停录音 ===
                    stream.stop_stream()
                    
                    # 2. === 大脑思考 ===
                    command = chat_with_brain(text)
                    
                    if command:
                        action = command.get('action')
                        speed = command.get('speed')
                        reply = command.get('reply')
                        
                        print(f"🤖 决策: {action} | 速度: {speed}")
                        
                        # 3. === 嘴巴说话 ===
                        speak(reply)
                        
                        # 4. === 执行动作 (未来加 GPIO) ===
                        if action == "dance":
                            print(">>> 💃 小车正在跳舞...")
                        elif action == "stop":
                            print(">>> 🛑 停车")
                        elif action == "move_forward":
                            print(">>> ⬆️ 前进")
                        
                    # 5. === 恢复录音 ===
                    if stream.is_stopped():
                         stream.start_stream()
                    
                    print("...继续监听...")

    except KeyboardInterrupt:
        print("\n再见！")
    finally:
        if 'stream' in locals():
            stream.stop_stream()
            stream.close()
        p.terminate()
        # 清理临时音频文件 (文件名也从 config 读，保持统一)
        if hasattr(config, 'TTS_FILE') and os.path.exists(config.TTS_FILE):
            try:
                os.remove(config.TTS_FILE)
            except:
                pass
        elif os.path.exists("reply.mp3"): # 兼容旧配置
             try: os.remove("reply.mp3") 
             except: pass

if __name__ == "__main__":
    run_voice_control()