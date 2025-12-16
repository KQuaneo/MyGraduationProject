import os
import sys
import json
import pyaudio
from vosk import Model, KaldiRecognizer

# === 引入大脑和嘴巴 ===
from llm_brain import chat_with_brain
from tts_mouth import speak

def run_voice_control():
    model_path = "model"
    if not os.path.exists(model_path):
        print("请检查 model 文件夹")
        sys.exit(1)
    
    print("正在加载语音模型...")
    model = Model(model_path)
    rec = KaldiRecognizer(model, 16000)

    p = pyaudio.PyAudio()
    
    # 定义录音流配置
    stream_kwargs = {
        'format': pyaudio.paInt16,
        'channels': 1,
        'rate': 16000,
        'input': True,
        'frames_per_buffer': 4000
    }
    
    stream = p.open(**stream_kwargs)
    stream.start_stream()
    
    print("\n=== ✨ 具身智能小车已就绪 ✨ ===")

    try:
        while True:
            data = stream.read(4000, exception_on_overflow=False)
            
            if rec.AcceptWaveform(data):
                result = json.loads(rec.Result())
                text = result.get("text", "").replace(" ", "")
                
                if len(text) > 1:
                    print(f"\n👂 听到: {text}")
                    
                    # 1. === 暂停录音 (防止听到自己说话) ===
                    stream.stop_stream()
                    
                    # 2. === 大脑思考 ===
                    command = chat_with_brain(text)
                    
                    if command:
                        action = command.get('action')
                        speed = command.get('speed')
                        reply = command.get('reply')
                        
                        print(f"🤖 决策: {action} | 速度: {speed}")
                        
                        # 3. === 嘴巴说话 ===
                        # 这里会阻塞，直到说完
                        speak(reply)
                        
                        # 4. === 执行动作 (未来加 GPIO) ===
                        if action == "dance":
                            print(">>> 💃 小车正在跳舞...")
                        
                    # 5. === 恢复录音 ===
                    # 清空一下刚才说话期间可能产生的缓存
                    # (不同系统表现不同，这行为了保险)
                    if stream.is_stopped():
                         stream.start_stream()
                    
                    print("...继续监听...")

    except KeyboardInterrupt:
        print("\n再见！")
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()
        # 删除临时音频文件
        if os.path.exists("reply.mp3"):
            os.remove("reply.mp3")

if __name__ == "__main__":
    run_voice_control()