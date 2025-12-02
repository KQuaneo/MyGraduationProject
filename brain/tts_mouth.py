import asyncio
import edge_tts
import pygame
import os

# 初始化 pygame 的混音器，用来播放音频
pygame.mixer.init()

# 声音角色选择 (zh-CN-XiaoyiNeural 是很自然的中文女声)
# 你也可以换成 zh-CN-YunxiNeural (男声)
VOICE = "zh-CN-XiaoyiNeural"
OUTPUT_FILE = "reply.mp3"

async def _generate_audio(text):
    """(内部函数) 调用 Edge-TTS 生成 MP3"""
    communicate = edge_tts.Communicate(text, VOICE)
    await communicate.save(OUTPUT_FILE)

def speak(text):
    """
    主函数：输入文本，播放声音
    这是一个阻塞函数，说完话才会继续往下执行，
    防止小车听到自己说的话（自激啸叫）。
    """
    if not text:
        return

    print(f"🔊 正在说话: {text}")
    
    # 1. 生成音频文件 (异步转同步)
    try:
        asyncio.run(_generate_audio(text))
    except Exception as e:
        print(f"TTS 生成失败: {e}")
        return

    # 2. 播放音频
    if os.path.exists(OUTPUT_FILE):
        try:
            pygame.mixer.music.load(OUTPUT_FILE)
            pygame.mixer.music.play()
            
            # 等待播放结束 (阻塞)
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
                
            # 播放完后卸载文件，否则下次无法覆盖写入
            pygame.mixer.music.unload() 
            
        except Exception as e:
            print(f"播放失败: {e}")

if __name__ == "__main__":
    # 测试一下
    speak("你好呀，我是你的智能小助手，我们可以出发了吗？")