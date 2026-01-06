import sys
import os
import asyncio
import edge_tts
import subprocess

# === 同样加入路径引用代码 ===
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
sys.path.append(root_dir)

import config  # 导入配置

# === 👇 修改开始：定义临时文件夹路径 👇 ===

# 1. 定义 temp 文件夹的具体位置 (online_agent/temp)
TEMP_DIR = os.path.join(root_dir, "temp")

# 2. 确保这个文件夹一定存在，没有就自动创建
if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)

# 使用 config 中的配置
VOICE = config.TTS_VOICE

# 3. 强制更改输出路径：只取 config 中的文件名，拼接到 temp 文件夹里
# 这样无论 config.py 里写的是 "reply.mp3" 还是别的，都会被强制放到 temp 目录下
OUTPUT_FILE = os.path.join(TEMP_DIR, os.path.basename(config.TTS_FILE))

# === 👆 修改结束 👆 ===

# USB 音箱设备
AUDIO_DEVICE = "plughw:3,0"

# 重试配置
MAX_RETRIES = 3
RETRY_DELAY = 1

async def _generate_audio(text):
    """(内部函数) 调用 Edge-TTS 生成 MP3，带重试机制"""
    for attempt in range(MAX_RETRIES):
        try:
            communicate = edge_tts.Communicate(text, VOICE)
            await communicate.save(OUTPUT_FILE)
            return
        except Exception as e:
            if attempt < MAX_RETRIES - 1:
                print(f"TTS 连接失败，正在重试 ({attempt + 1}/{MAX_RETRIES})...")
                await asyncio.sleep(RETRY_DELAY)
            else:
                raise e

def speak(text):
    """
    主函数：输入文本，播放声音
    使用 mpg123 通过 USB 音箱播放
    """
    if not text:
        return

    print(f"🔊 正在说话: {text}")
    
    # 1. 生成音频文件
    try:
        asyncio.run(_generate_audio(text))
    except Exception as e:
        print(f"TTS 生成失败: {e}")
        return

    # 2. 播放音频 (通过 USB 音箱)
    if os.path.exists(OUTPUT_FILE):
        try:
            subprocess.run(
                ['mpg123', '-q', '-a', AUDIO_DEVICE, OUTPUT_FILE],
                check=True
            )
        except FileNotFoundError:
            print("请安装 mpg123: sudo apt install mpg123")
        except Exception as e:
            print(f"播放失败: {e}")

if __name__ == "__main__":
    speak("你好呀，我是你的智能小助手，我们可以出发了吗？")