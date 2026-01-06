import json
import os
import pygame
import threading

# 获取 online_agent 目录（images 文件夹在那里）
CURRENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 情绪到图片的映射（使用绝对路径）
EMOTION_IMAGES = {
    "happy": os.path.join(CURRENT_DIR, "images/happy.png"),
    "sad": os.path.join(CURRENT_DIR, "images/sad.png"),
    "angry": os.path.join(CURRENT_DIR, "images/angry.png"),
    "surprised": os.path.join(CURRENT_DIR, "images/surprised.png"),
    "neutral": os.path.join(CURRENT_DIR, "images/neutral.png"),
    "fear": os.path.join(CURRENT_DIR, "images/fear.png"),
}

class EmotionDisplay:
    """情绪显示管理器 - 单例模式，非阻塞"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        self.screen = None
        self.images = {}
        self.current_emotion = None
        self.running = False
        self._lock = threading.Lock()
        
    def start(self, fullscreen=True):
        """启动显示（在主线程调用一次）"""
        pygame.init()
        
        if fullscreen:
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        else:
            self.screen = pygame.display.set_mode((800, 480))
        
        pygame.display.set_caption("Emotion Display")
        self._preload_images()
        self.running = True
        
        # 默认显示 neutral
        self.update_emotion("neutral")
        
    def _preload_images(self):
        """预加载所有图片"""
        for emotion, path in EMOTION_IMAGES.items():
            if os.path.exists(path):
                try:
                    img = pygame.image.load(path)
                    self.images[emotion] = pygame.transform.scale(img, self.screen.get_size())
                    print(f"✅ 加载情绪图片: {emotion}")
                except Exception as e:
                    print(f"❌ 加载图片失败 {path}: {e}")
            else:
                print(f"⚠️ 图片不存在: {path}")
    
    def update_emotion(self, emotion):
        """更新显示的情绪（非阻塞）"""
        if not self.running or not self.screen:
            return
            
        emotion = emotion.lower() if emotion else "neutral"
        
        with self._lock:
            if emotion in self.images:
                self.current_emotion = emotion
                self.screen.fill((0, 0, 0))  # 清屏
                self.screen.blit(self.images[emotion], (0, 0))
                pygame.display.flip()
                print(f"😊 显示情绪: {emotion}")
            else:
                print(f"⚠️ 未找到情绪图片: {emotion}，使用 neutral")
                if "neutral" in self.images:
                    self.screen.blit(self.images["neutral"], (0, 0))
                    pygame.display.flip()
    
    def update_from_json(self, json_response):
        """从 JSON 响应更新情绪"""
        try:
            if isinstance(json_response, str):
                data = json.loads(json_response)
            else:
                data = json_response
            
            emotion = data.get("emotion", "neutral")
            self.update_emotion(emotion)
        except (json.JSONDecodeError, AttributeError):
            self.update_emotion("neutral")
    
    def process_events(self):
        """处理 pygame 事件（需要定期调用）"""
        if not self.running:
            return True
            
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
        return True
    
    def close(self):
        """关闭显示"""
        self.running = False
        if pygame.get_init():
            pygame.quit()


# 全局实例，方便其他模块调用
emotion_display = EmotionDisplay()


def parse_emotion_from_json(json_response):
    """从 LLM 的 JSON 响应中解析情绪"""
    try:
        if isinstance(json_response, str):
            data = json.loads(json_response)
        else:
            data = json_response
        
        emotion = data.get("emotion") 
        return emotion.lower() if emotion else "neutral"
    except json.JSONDecodeError:
        return "neutral"


# 测试用
if __name__ == "__main__":
    import time
    
    display = EmotionDisplay()
    display.start(fullscreen=False)  # 测试时用窗口模式
    
    emotions = ["happy", "sad", "angry", "neutral", "surprised"]
    
    for emotion in emotions:
        display.update_emotion(emotion)
        time.sleep(2)
        
        if not display.process_events():
            break
    
    display.close()
