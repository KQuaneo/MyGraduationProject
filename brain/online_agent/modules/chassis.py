import time
import threading
import board
import busio
from adafruit_pca9685 import PCA9685
from adafruit_motor import servo

class ChassisController:
    def __init__(self, channel_index=0):
        """
        初始化底盘控制器
        :param channel_index: 舵机插在 PCA9685 板上的第几个口 (0-15)
        """
        self.running = True
        
        # === 1. 初始化 I2C 和 PCA9685 ===
        # 使用板载 I2C 接口
        i2c = board.I2C() 
        self.pca = PCA9685(i2c)
        self.pca.frequency = 50 # 舵机标准频率 50Hz
        
        # === 2. 初始化 DS3115 270度舵机 ===
        # ⚠️ 关键设置：DS3115 通常需要 500us-2500us 的脉宽来实现 0-270 度
        # actuation_range=270: 告诉库这是一个270度的舵机
        self.servo = servo.Servo(
            self.pca.channels[channel_index], 
            actuation_range=270, 
            min_pulse=500, 
            max_pulse=2500
        )
        
        # === 3. 机械参数 ===
        self.gear_ratio = 1.5    # 齿轮比: 270(舵机) / 180(底盘)
        self.current_toy_angle = 0.0 # 逻辑角度 (-90 左 ~ +90 右)
        
        # === 4. 控制变量 ===
        self.face_error_x = None  # 视觉误差
        self.llm_action_queue = [] # 动作队列
        
        # 初始回正
        self._set_physical_servo(0)
        
        # 启动后台控制线程
        self.thread = threading.Thread(target=self._control_loop, daemon=True)
        self.thread.start()
        print(f"🛹 底盘控制器已启动 (通道 {channel_index}, 270°舵机模式)")

    def _set_physical_servo(self, toy_angle):
        """
        将玩具的逻辑角度 (-90~90) 映射到 270度舵机角度
        """
        # 1. 软件限位 (-90 到 90)
        toy_angle = max(-90, min(90, toy_angle))

        # 2. 计算目标角度 (0 ~ 270)
        # 逻辑 0度 -> 舵机 135度
        servo_target = (toy_angle + 90) * self.gear_ratio

        # 3. 写入舵机 (加个 try-catch 防止 I2C 通信偶尔报错)
        try:
            self.servo.angle = servo_target
            self.current_toy_angle = toy_angle

        except Exception as e:
            print(f"⚠️ 舵机I2C写入失败: {e}")

    def update_vision_data(self, error_x):
        """由主程序调用：更新视觉误差 (-1.0 ~ 1.0)"""
        self.face_error_x = error_x

    def add_action(self, action_name):
        """由主程序调用：执行动作指令"""
        print(f"🛹 底盘接收指令: {action_name}")
        self.llm_action_queue.append(action_name)

    def _control_loop(self):
        """后台控制循环"""
        while self.running:
            # === 优先级 1: LLM 动作指令 ===
            if self.llm_action_queue:
                action = self.llm_action_queue.pop(0)
                self._perform_scripted_motion(action)
                # 动作做完后，稍微停顿一下再回主循环
                time.sleep(0.5)
                continue

            # === 优先级 2: 视觉跟随 (PID的 P控制) ===
            if self.face_error_x is not None:
                # 调整这个 KP 值来改变灵敏度
                kp = 5.0 
                dead_zone = 0.05 # 死区
                
                if abs(self.face_error_x) > dead_zone:
                    # 计算需要转动的增量
                    # 如果发现方向反了，把这里的 += 改成 -=
                    delta = self.face_error_x * kp
                    
                    # 平滑更新
                    new_angle = self.current_toy_angle + delta
                    self._set_physical_servo(new_angle)
            
            # === 优先级 3: 待机 (可选) ===
            # else:
            #    pass

            time.sleep(0.04) # 25Hz 刷新率，保证流畅

    def _perform_scripted_motion(self, action):
        """执行预设动作"""
        base_angle = self.current_toy_angle
        
        if action == "look_away" or action == "turn_away": 
            # 傲娇转头：猛地转到侧面
            target = 60 if base_angle < 0 else -60
            self._set_physical_servo(target)
            time.sleep(2.0) # 保持 2 秒
            
        elif action == "shake" or action == "no": 
            # 摇头：快速左右摆动
            for _ in range(3):
                self._set_physical_servo(base_angle + 15)
                time.sleep(0.15)
                self._set_physical_servo(base_angle - 15)
                time.sleep(0.15)
            self._set_physical_servo(base_angle) # 回位
            
        elif action == "scan":
            # 搜索模式：慢速扫描
            for angle in range(-45, 46, 5):
                self._set_physical_servo(angle)
                time.sleep(0.1)