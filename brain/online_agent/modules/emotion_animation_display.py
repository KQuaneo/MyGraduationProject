import pygame
import threading
import queue
import time
import math
import random
import os

# --- 全局配置 ---
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768
BG_COLOR = (50, 50, 60) 
EYE_COLOR = (255, 191, 0)
PUPIL_COLOR = (255, 255, 255)
FPS = 60
SAFETY_MARGIN = 30 

class Spring:
    """物理弹簧类 (保持不变)"""
    def __init__(self, val, k=0.1, d=0.8):
        self.target = val
        self.val = val
        self.vel = 0
        self.k = k
        self.d = d

    def update(self):
        force = (self.target - self.val) * self.k
        self.vel += force
        self.vel *= self.d
        self.val += self.vel
        return self.val

    def set(self, target):
        self.target = target

class EyeDisplay:
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
        self.clock = None
        self.running = False
        self._lock = threading.Lock()
        self._emotion_queue = queue.Queue()
        
        self.base_w = 190
        self.base_h = 240
        
        self.props = None
        self.last_cmd_time = time.time()
        
        # --- 眨眼控制 ---
        self.is_blinking = False
        self.next_blink = time.time() + 2
        self.pre_blink_h = 190
        self.blink_duration = 0.15

        # --- 新增：情绪待机控制 ---
        self.current_emotion = "neutral"      # 当前情绪状态
        self.emotion_idle_end_time = 0        # 情绪待机结束的时间戳
        self.next_micro_move = time.time()    # 下一次微动作的时间
        
    def _init_props(self):
        # 保持原有参数初始化
        self.props = {
            "width":    Spring(self.base_w, k=0.08, d=0.75),
            "height":   Spring(self.base_h, k=0.08, d=0.75),
            "radius":   Spring(50.0, k=0.1, d=0.8),
            "angle":    Spring(0.0, k=0.05, d=0.7),
            "gap":      Spring(110.0, k=0.05, d=0.8),
            "y_off":    Spring(0.0, k=0.05, d=0.8),
            "pupil_x":  Spring(0.0, k=0.15, d=0.7),
            "pupil_y":  Spring(0.0, k=0.15, d=0.7),
            "pupil_sz": Spring(40.0, k=0.1, d=0.8)
        }

    def _run_loop(self, fullscreen=True):
        os.environ["SDL_VIDEODRIVER"] = "x11"
        pygame.init()
        flags = pygame.NOFRAME
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), flags)
        pygame.display.set_caption("Robot Eyes")
        pygame.mouse.set_visible(False)

        self.clock = pygame.time.Clock()
        self._init_props()
        self.running = True
        
        print("👀 眼睛渲染循环已启动")
        
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.running = False
            
            # 读取新指令
            try:
                data = self._emotion_queue.get_nowait()
                self._apply_emotion_command(data['emotion'], data['intensity'])
            except queue.Empty:
                pass

            # 物理与行为计算
            self._physics_step()

            # 渲染
            self.screen.fill(BG_COLOR)
            cx = self.screen.get_width() // 2
            cy = self.screen.get_height() // 2
            
            self._draw_eye(cx, cy, True)
            self._draw_eye(cx, cy, False)
            
            pygame.display.flip()
            self.clock.tick(FPS)
        
        pygame.quit()

    def update_emotion(self, emotion, intensity=1.0):
        emotion = emotion.lower() if emotion else "neutral"
        self._emotion_queue.put({"emotion": emotion, "intensity": intensity})
        print(f"👀 收到表情指令: {emotion}")

    def _apply_emotion_command(self, emotion, intensity):
        """应用表情指令并设置待机时间"""
        self.last_cmd_time = time.time()
        self.current_emotion = emotion
        
        # 设定该表情的保持时间：10 到 20 秒之间随机
        duration = random.uniform(10.0, 20.0)
        self.emotion_idle_end_time = time.time() + duration
        
        # 立即执行表情变化（调用原来的逻辑）
        self._update_target(emotion, intensity)

    def _update_target(self, emotion, intensity):
        # ... (此处代码与你原来的一致，省略以节省篇幅，保持原来的逻辑即可) ...
        # 为了演示，这里简写几个关键的，实际请保留你原来的完整逻辑
        t_w, t_h = self.base_w, self.base_h
        t_r, t_a, t_g, t_y = 50, 0, 110, 0
        t_px, t_py, t_psz = 0, 0, 40

        if emotion == "happy":
            t_h = self.base_h * (1.0 + 0.15 * intensity)
            t_w = self.base_w * (1.0 + 0.1 * intensity)
            t_r, t_y = 100, -15 * intensity
            t_psz, t_py = 45 + 10 * intensity, -10
        elif emotion == "sad":
            t_a = 15 * intensity
            t_h, t_w = self.base_h * 0.9, self.base_w * 0.95
            t_y, t_py, t_px = 20 * intensity, 25 * intensity, -15 * intensity
        elif emotion == "angry":
            t_a = -25 * intensity
            t_h = self.base_h * 0.8
            t_r, t_y, t_g = 10, 10, 90
            t_psz, t_py = 25, 5
        elif emotion == "surprised":
            t_h = self.base_h * 1.3
            t_w = self.base_w * 0.85
            t_r, t_g, t_psz = 60, 130, 20
        # ... 其他表情保持不变 ...
        
        # 赋值给弹簧
        p = self.props
        p["width"].set(t_w)
        p["height"].set(t_h)
        p["radius"].set(t_r)
        p["angle"].set(t_a)
        p["gap"].set(t_g)
        p["y_off"].set(t_y)
        p["pupil_x"].set(t_px)
        p["pupil_y"].set(t_py)
        p["pupil_sz"].set(t_psz)

    # --- 核心修改：分层待机逻辑 ---
    
    def _physics_step(self):
        now = time.time()
        
        # 1. 只有当没有新指令 2秒后，才开始介入 Idle 行为 (给动作执行留出时间)
        if now - self.last_cmd_time > 2.0:
            if now < self.emotion_idle_end_time:
                # 处于 [情绪待机] 阶段
                self._process_emotion_idle(self.current_emotion, now)
            else:
                # 处于 [普通待机] 阶段 (原来的随机乱看)
                self._process_generic_idle(now)

        # 2. 眨眼逻辑 (保持不变)
        if not self.is_blinking and now > self.next_blink:
            self.is_blinking = True
            self.blink_start = now
            self.pre_blink_h = self.props["height"].target
            # 眨眼时高度设为 5
            self.props["height"].set(5) 
        
        if self.is_blinking:
            if now - self.blink_start > self.blink_duration:
                self.is_blinking = False
                self.props["height"].set(self.pre_blink_h)
                self.next_blink = now + random.uniform(2, 6)

        # 3. 物理更新
        if self.props:
            for key in self.props:
                self.props[key].update()

    def _process_emotion_idle(self, emotion, now):
        """特定情绪的待机微动作"""
        if now < self.next_micro_move:
            return

        p = self.props
        
        if emotion == "happy":
            # Happy 待机：像是在笑，偶尔上下浮动，保持眼神向上
            action = random.choice(["bob_up", "bob_down", "wiggle"])
            if action == "bob_up":
                p["y_off"].set(-20) # 向上跳一点
            elif action == "bob_down":
                p["y_off"].set(-10) # 回落
            elif action == "wiggle":
                p["angle"].set(random.uniform(-5, 5)) # 微微晃头
            
            # 保持瞳孔在上方
            p["pupil_y"].set(-10)
            self.next_micro_move = now + random.uniform(0.5, 1.5)

        elif emotion == "angry":
            # Angry 待机：警惕，快速扫视，眼睛眯得更紧
            action = random.choice(["scan_left", "scan_right", "narrow", "twitch"])
            if action == "scan_left":
                p["pupil_x"].set(-20)
            elif action == "scan_right":
                p["pupil_x"].set(20)
            elif action == "narrow":
                curr_h = p["height"].target
                p["height"].set(curr_h * 0.9) # 眯眼
            elif action == "twitch":
                 p["gap"].set(p["gap"].target - 5) # 眉心紧缩
            
            self.next_micro_move = now + random.uniform(0.3, 1.0) # 愤怒时动作频率快

        elif emotion == "sad":
            # Sad 待机：低头，发呆，动作极慢
            action = random.choice(["look_down_L", "look_down_R", "sigh"])
            if action == "look_down_L":
                p["pupil_x"].set(-15)
                p["pupil_y"].set(30)
            elif action == "look_down_R":
                p["pupil_x"].set(15)
                p["pupil_y"].set(30)
            elif action == "sigh":
                # 叹气效果：眼睛略微闭合再张开
                p["height"].set(self.base_h * 0.8)
            
            self.next_micro_move = now + random.uniform(2.0, 5.0) # 悲伤时动作很慢

        elif emotion == "surprised":
            # Surprised 待机：慢慢回神，偶尔看看周围
            p["height"].set(self.base_h * 1.1) # 保持睁大
            if random.random() < 0.5:
                p["pupil_x"].set(random.uniform(-10, 10))
            self.next_micro_move = now + random.uniform(1.0, 3.0)

        else:
            # 如果是 Neutral 或 Thinking，直接进入普通待机
            self._process_generic_idle(now)

    def _process_generic_idle(self, now):
        """普通待机：就是你原来的随机乱看逻辑"""
        if now < self.next_micro_move:
            return
            
        action = random.choice(["look_left", "look_right", "look_up", "center", "squint"])
        p = self.props
        
        # 恢复默认状态
        p["y_off"].set(0)
        p["angle"].set(0)
        p["gap"].set(110)
        p["radius"].set(50)

        if action == "look_left":
            p["pupil_x"].set(-30)
            p["pupil_y"].set(0)
        elif action == "look_right":
            p["pupil_x"].set(30)
            p["pupil_y"].set(0)
        elif action == "look_up":
            p["pupil_x"].set(0)
            p["pupil_y"].set(-30)
        elif action == "center":
            p["pupil_x"].set(0)
            p["pupil_y"].set(0)
            p["height"].set(self.base_h)
        elif action == "squint":
            p["height"].set(self.base_h * 0.7)
            
        self.next_micro_move = now + random.uniform(1.5, 4.0)

    def _draw_eye(self, cx, cy, is_left):
        # 保持原有的绘制逻辑不变
        p = self.props
        w, h = p["width"].val, p["height"].val
        r = p["radius"].val
        angle = p["angle"].val
        
        s_size = int(max(w, h) * 1.6)
        surf = pygame.Surface((s_size, s_size), pygame.SRCALPHA)
        center = s_size // 2
        
        rect = pygame.Rect(0, 0, w, h)
        rect.center = (center, center)
        valid_r = max(0, min(abs(r), w/2, h/2))
        pygame.draw.rect(surf, EYE_COLOR, rect, border_radius=int(valid_r))
        
        px = p["pupil_x"].val
        py = p["pupil_y"].val
        final_px = center + (px if is_left else -px)
        final_py = center + py
        final_py = max(rect.top+10, min(rect.bottom-10, final_py))
        final_px = max(rect.left+10, min(rect.right-10, final_px))
        
        pygame.draw.circle(surf, PUPIL_COLOR, (int(final_px), int(final_py)), int(p["pupil_sz"].val))

        rot_angle = angle if is_left else -angle
        rot_surf = pygame.transform.rotate(surf, rot_angle)
        
        gap = p["gap"].val
        y_off = p["y_off"].val
        screen_x = cx - gap if is_left else cx + gap
        screen_y = cy + y_off
        
        dest = rot_surf.get_rect(center=(screen_x, screen_y))
        self.screen.blit(rot_surf, dest)

    def close(self):
        self.running = False