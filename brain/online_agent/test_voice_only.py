#!/usr/bin/env python3
"""
test_voice_only.py - 纯语音链路测试脚本

只测试：麦克风 → 语音识别 → LLM → 语音输出
不包含：屏幕、舵机、视觉

使用方法:
    cd /home/raspberrypi/Desktop/MyGraduationProject/brain/online_agent
    source .venv/bin/activate
    python test_voice_only.py
"""

import os
import sys
import json
import time
import array
import queue
import threading

# 路径设置
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(SCRIPT_DIR)
sys.path.insert(0, SCRIPT_DIR)

print("=" * 60)
print("🎙️ 纯语音链路测试")
print("=" * 60)
print("功能: 麦克风 → Vosk识别 → 流式LLM → EdgeTTS")
print("不包含: 屏幕、舵机、视觉")
print("=" * 60)

# === 导入配置 ===
try:
    import config
    print(f"\n✅ 配置加载成功")
    print(f"   MIC_ID: {config.MIC_ID}")
    print(f"   SAMPLE_RATE: {config.SAMPLE_RATE}")
except ImportError as e:
    print(f"❌ 配置加载失败: {e}")
    sys.exit(1)

# === 导入语音模块 ===
try:
    import pyaudio
    from vosk import Model, KaldiRecognizer
    print("✅ PyAudio 和 Vosk 导入成功")
except ImportError as e:
    print(f"❌ 缺少依赖: {e}")
    print("   安装: pip install pyaudio vosk")
    sys.exit(1)

try:
    from modules.streaming_brain import StreamingBrain
    print("✅ 流式大脑模块导入成功")
except ImportError as e:
    print(f"❌ 大脑模块导入失败: {e}")
    sys.exit(1)

try:
    from modules.mouth import speak
    print("✅ TTS 模块导入成功")
except ImportError as e:
    print(f"❌ TTS 模块导入失败: {e}")
    sys.exit(1)


# ==========================================
#  TTS 队列管理器
# ==========================================
class TTSQueueManager:
    """后台 TTS 播放队列"""
    
    def __init__(self):
        self.queue = queue.Queue()
        self.is_speaking = False
        self.stop_flag = False
        self.thread = None
        
    def start(self):
        self.stop_flag = False
        self.thread = threading.Thread(target=self._worker, daemon=True)
        self.thread.start()
        print("🔊 TTS 队列管理器已启动")
        
    def stop(self):
        self.stop_flag = True
        while not self.queue.empty():
            try:
                self.queue.get_nowait()
            except:
                break
        if self.thread:
            self.thread.join(timeout=1)
            
    def _worker(self):
        while not self.stop_flag:
            try:
                sentence = self.queue.get(timeout=0.5)
                if sentence:
                    self.is_speaking = True
                    speak(sentence)
                    self.is_speaking = False
            except queue.Empty:
                continue
            except Exception as e:
                print(f"TTS 错误: {e}")
                self.is_speaking = False
                
    def add(self, sentence):
        if sentence and sentence.strip():
            self.queue.put(sentence.strip())
            
    def wait_done(self, timeout=None):
        start = time.time()
        while not self.queue.empty() or self.is_speaking:
            if timeout and (time.time() - start) > timeout:
                return False
            time.sleep(0.1)
        return True


# ==========================================
#  语音识别初始化
# ==========================================
def init_audio():
    """初始化麦克风"""
    print("\n🎤 初始化音频系统...")
    
    p = pyaudio.PyAudio()
    
    # 列出可用设备
    print("\n📋 可用音频输入设备:")
    mic_found = False
    for i in range(p.get_device_count()):
        info = p.get_device_info_by_index(i)
        if info['maxInputChannels'] > 0:
            marker = " 👈 配置选中" if i == config.MIC_ID else ""
            print(f"   ID {i}: {info['name']}{marker}")
            if i == config.MIC_ID:
                mic_found = True
    
    if not mic_found:
        print(f"⚠️ 警告: 配置的麦克风 ID {config.MIC_ID} 未找到，尝试使用默认设备")
    
    # 打开音频流
    target_mic_id = config.MIC_ID
    input_channels = 1
    
    try:
        dev_info = p.get_device_info_by_index(config.MIC_ID)
        hw_channels = int(dev_info['maxInputChannels'])
        input_channels = hw_channels if hw_channels >= 2 else 1
        print(f"\n✅ 使用麦克风 ID {config.MIC_ID}: {dev_info['name']}")
    except Exception as e:
        print(f"⚠️ 无法打开配置麦克风: {e}")
        try:
            default_info = p.get_default_input_device_info()
            target_mic_id = default_info['index']
            hw_channels = int(default_info['maxInputChannels'])
            input_channels = hw_channels if hw_channels >= 2 else 1
            print(f"✅ 切换到默认麦克风 ID {target_mic_id}")
        except Exception as e2:
            print(f"❌ 无法找到任何麦克风: {e2}")
            return None, None, None

    try:
        stream = p.open(
            format=pyaudio.paInt16,
            channels=input_channels,
            rate=config.SAMPLE_RATE,
            input=True,
            frames_per_buffer=8000,
            input_device_index=target_mic_id
        )
        stream.start_stream()
        print("✅ 音频流已打开")
        return p, stream, input_channels
    except Exception as e:
        print(f"❌ 打开音频流失败: {e}")
        return None, None, None


def init_vosk():
    """初始化 Vosk 语音识别"""
    print("\n🗣️ 初始化语音识别...")
    
    model_path = os.path.join(SCRIPT_DIR, "model")
    if not os.path.exists(model_path):
        print(f"❌ 错误: 找不到模型文件夹 {model_path}")
        print("   请下载 Vosk 中文模型并解压到 model/ 目录")
        return None
    
    try:
        model = Model(model_path)
        rec = KaldiRecognizer(model, config.SAMPLE_RATE)
        print("✅ Vosk 语音识别已加载")
        return rec
    except Exception as e:
        print(f"❌ 加载 Vosk 失败: {e}")
        return None


# ==========================================
#  流式对话处理
# ==========================================
def process_conversation(text, brain, tts_manager):
    """
    处理单轮对话：流式 LLM + 流式 TTS
    """
    print(f"\n{'='*60}")
    print(f"👤 用户: {text}")
    print(f"{'='*60}")
    
    start_time = time.time()
    first_sentence_time = None
    sentence_count = 0
    full_reply = []
    
    # 流式生成回调
    def on_header(action, emotion):
        print(f"🤖 决策: action={action}, emotion={emotion}")
    
    def on_sentence(sentence, is_last):
        nonlocal first_sentence_time, sentence_count
        if first_sentence_time is None:
            first_sentence_time = time.time() - start_time
        sentence_count += 1
        print(f"🔊 句子{sentence_count}{'[完]' if is_last else ''}: {sentence}")
        tts_manager.add(sentence)
        full_reply.append(sentence)
    
    def on_complete(full):
        pass
    
    # 执行流式对话
    print("⏳ 流式生成中...")
    for event in brain.chat_streaming(text, on_header, on_sentence, on_complete):
        if event['type'] == 'error':
            print(f"❌ 错误: {event.get('error')}")
            return None
    
    # 等待 TTS 完成
    tts_manager.wait_done(timeout=30)
    
    total_time = time.time() - start_time
    print(f"\n📊 统计:")
    print(f"   首句延迟: {first_sentence_time:.2f}s" if first_sentence_time else "   首句延迟: N/A")
    print(f"   总耗时: {total_time:.2f}s")
    print(f"   句子数: {sentence_count}")
    print(f"   完整回复: {''.join(full_reply)}")
    
    return ''.join(full_reply)


# ==========================================
#  主循环
# ==========================================
def main():
    # 初始化
    p, stream, input_channels = init_audio()
    if not p:
        print("\n❌ 音频初始化失败，退出")
        return
    
    rec = init_vosk()
    if not rec:
        print("\n❌ 语音识别初始化失败，退出")
        stream.stop_stream()
        stream.close()
        p.terminate()
        return
    
    # 初始化流式大脑和 TTS
    brain = StreamingBrain()
    tts_manager = TTSQueueManager()
    tts_manager.start()
    
    print("\n" + "=" * 60)
    print("✅ 系统就绪！请对麦克风说话")
    print("=" * 60)
    print("提示:")
    print("  - 说话前等待 '听到:' 提示")
    print("  - 按 Ctrl+C 退出")
    print("=" * 60 + "\n")
    
    try:
        while True:
            # 读取音频
            data = stream.read(8000, exception_on_overflow=False)
            
            # 声道转换
            if input_channels > 1:
                shorts = array.array('h', data)
                mono_shorts = shorts[::input_channels]
                data = mono_shorts.tobytes()
            
            # 语音识别
            if rec.AcceptWaveform(data):
                result = json.loads(rec.Result())
                text = result.get("text", "").replace(" ", "")
                
                if len(text) > 1:
                    # 处理对话
                    process_conversation(text, brain, tts_manager)
                    print("\n" + "-" * 60)
                    print("⏳ 等待下一次输入...")
                    print("-" * 60)
                    
    except KeyboardInterrupt:
        print("\n\n👋 用户中断，正在关闭...")
    except Exception as e:
        print(f"\n❌ 运行错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 清理
        tts_manager.stop()
        if stream:
            stream.stop_stream()
            stream.close()
        if p:
            p.terminate()
        print("✅ 已清理资源，退出")


if __name__ == "__main__":
    main()
