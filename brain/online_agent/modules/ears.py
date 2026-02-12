import time
import json
import os
import threading
import board
from adafruit_pca9685 import PCA9685
from adafruit_motor import servo

class EarController:
    def __init__(self):
        self.pca = None
        self.servo0 = None
        self.servo3 = None
        self.enabled = False
        self.motion_library = {}
        
        # 1. 加载 JSON 配置
        self.load_config()
        
        # 2. 初始化硬件
        try:
            i2c = board.I2C()
            self.pca = PCA9685(i2c)
            self.pca.frequency = 50
            
            # 初始化两个舵机
            self.servo0 = servo.Servo(self.pca.channels[2], min_pulse=500, max_pulse=2500)
            self.servo3 = servo.Servo(self.pca.channels[3], min_pulse=500, max_pulse=2500)
            
            self.enabled = True
            print("✅ 耳朵舵机初始化成功")
            
            # 3. 归位 (这里修复了函数名错误)
            # 使用 _animate 直接执行，不开启线程，确保启动时归位完成
            self._animate("neutral") 
            
        except Exception as e:
            print(f"⚠️ 耳朵舵机初始化失败: {e}")
            self.enabled = False

    def load_config(self):
        """加载动作库"""
        try:
            current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            config_path = os.path.join(current_dir, "ears_config.json")
            with open(config_path, 'r', encoding='utf-8') as f:
                self.motion_library = json.load(f)
            # print("✅ 耳朵动作库加载完成")
        except Exception as e:
            print(f"❌ 无法加载耳朵动作库: {e}")
            # 给一个默认的
            self.motion_library = {"neutral": [{"angles": [0, 0], "delay": 1}]}

    def _animate(self, emotion_name):
        """实际执行动作的内部函数"""
        if not self.enabled:
            return

        frames = self.motion_library.get(emotion_name, self.motion_library.get("neutral"))
        
        if not frames:
            return

        for frame in frames:
            # 再次检查，防止运行中硬件断开
            if not self.enabled: break
            
            angle0 = frame["angles"][0]
            angle3 = frame["angles"][1]
            delay = frame["delay"]
            
            try:
                # 限制角度在安全范围 0-180
                if self.servo0: self.servo0.angle = max(0, min(180, angle0))
                if self.servo3: self.servo3.angle = max(0, min(180, angle3))
                time.sleep(delay)
            except Exception as e:
                print(f"舵机驱动错误: {e}")

    def update_emotion(self, emotion_name):
        """外部调用的主接口"""
        if not self.enabled: return
        
        # print(f"🐰 耳朵动作: {emotion_name}")
        
        # 开启新线程执行动作，防止卡住主程序
        t = threading.Thread(target=self._animate, args=(emotion_name,))
        t.start()