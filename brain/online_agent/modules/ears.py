import time
import json
import os
import threading
from adafruit_motor import servo
from modules.pca9685_manager import get_channel

class EarController:
    def __init__(self):
        self.servo_left = None   # 左耳舵机
        self.servo_right = None  # 右耳舵机
        self.enabled = False
        self.motion_library = {}
        
        # 1. 加载 JSON 配置
        self.load_config()
        
        # 2. 初始化硬件（使用共享 PCA9685 实例）
        try:
            # 初始化两个舵机
            # 注意：通道 3 损坏，右耳改用通道 1
            self.servo_left = servo.Servo(get_channel(2), min_pulse=500, max_pulse=2500)   # 左耳 - 通道 2
            self.servo_right = servo.Servo(get_channel(1), min_pulse=500, max_pulse=2500)  # 右耳 - 通道 1（原通道 3 损坏）
            
            self.enabled = True
            print("✅ 耳朵舵机初始化成功")
            
            # 3. 归位
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
            
            angle_left = frame["angles"][0]
            angle_right = frame["angles"][1]
            delay = frame["delay"]
            
            try:
                # 限制角度在物理 0~30 度范围
                # 输入 0 -> 0度, 30 -> 30度
                def map_angle(val):
                    # 限制输入范围 0-30
                    val = max(0, min(30, val))
                    return val

                if self.servo_left: self.servo_left.angle = map_angle(angle_left)
                if self.servo_right: self.servo_right.angle = map_angle(angle_right)
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

    def stop(self):
        """停止耳朵控制器，关闭舵机输出"""
        print("🛑 正在停止耳朵控制器...")
        self.enabled = False
        # 关闭舵机 PWM 输出
        try:
            from modules.pca9685_manager import get_channel
            get_channel(1).duty_cycle = 0  # 右耳 - 通道 1
            get_channel(2).duty_cycle = 0  # 左耳 - 通道 2
            print("🔌 耳朵舵机已关闭")
        except Exception as e:
            print(f"⚠️ 关闭耳朵舵机时出错: {e}")