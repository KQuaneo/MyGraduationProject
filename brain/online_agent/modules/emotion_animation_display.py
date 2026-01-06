import pygame
import threading
import queue
import time
import math
import random

# --- 全局配置 ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 480
BG_COLOR = (10, 10, 22)
EYE_COLOR = (255, 191, 0)
PUPIL_COLOR = (255, 255, 255)
FPS = 60
SAFETY_MARGIN = 30 


class Spring:
    """物理弹簧类 - 让动作Q弹的核心"""
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
    """眼睛显示管理器 - 单例模式"""
    
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
        self._render_thread = None
        self._emotion_queue = queue.Queue()
        
        self.base_w = 150
        self.base_h = 190
        
        # 弹簧属性
        self.props = None
        
        # 状态管理
        self.last_cmd_time = time.time()
        self.is_blinking = False
        self.next_blink = time.time() + 2
        self.next_idle_move = time.time() + 2
        self.pre_blink_h = 190

    def _init_props(self):
        """初始化弹簧属性"""
        self.props = {
            "width":    Spring(self.base_w, k=0.08, d=0.75),
            "height":   Spring(self.base_h, k=0.08, d=0.75),
            "radius":   Spring(40.0, k=0.1, d=0.8),
            "angle":    Spring(0.0, k=0.05, d=0.7),
            "gap":      Spring(90.0, k=0.05, d=0.8),
            "y_off":    Spring(0.0, k=0.05, d=0.8),
            "pupil_x":  Spring(0.0, k=0.15, d=0.7),
            "pupil_y":  Spring(0.0, k=0.15, d=0.7),
            "pupil_sz": Spring(30.0, k=0.1, d=0.8)
        }

    def start(self, fullscreen=True):
        """启动显示（在后台线程运行）"""
        if self.running:
            return
        
        self.running = True
        self._render_thread = threading.Thread(target=self._run_loop, args=(fullscreen,), daemon=True)
        self._render_thread.start()
        
        # 等待初始化完成
        time.sleep(0.5)
        print("✅ 眼睛显示已启动")

    def _run_loop(self, fullscreen):
        """渲染主循环（在子线程运行）"""
        pygame.init()
        
        if fullscreen:
            self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
        else:
            self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        
        pygame.display.set_caption("Robot Eyes")
        self.clock = pygame.time.Clock()
        self._init_props()
        
        while self.running:
            # 处理事件
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.running = False
            
            # 读取情绪队列
            try:
                data = self._emotion_queue.get_nowait()
                self._update_target(data['emotion'], data['intensity'])
            except queue.Empty:
                pass

            # 物理计算
            self._physics_step()

            # 渲染
            self.screen.fill(BG_COLOR)
            cx, cy = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2
            self._draw_eye(cx, cy, True)
            self._draw_eye(cx, cy, False)
            
            pygame.display.flip()
            self.clock.tick(FPS)
        
        pygame.quit()

    def update_emotion(self, emotion, intensity=1.0):
        """更新情绪（非阻塞，线程安全）"""
        if not self.running:
            return
        
        emotion = emotion.lower() if emotion else "neutral"
        self._emotion_queue.put({"emotion": emotion, "intensity": intensity})
        print(f"👀 眼睛表情: {emotion}")

    def _update_target(self, emotion, intensity):
        """接收指令并设定弹簧的目标值"""
        self.last_cmd_time = time.time()
        
        t_w, t_h = self.base_w, self.base_h
        t_r, t_a, t_g, t_y = 50, 0, 90, 0
        t_px, t_py, t_psz = 0, 0, 30

        if emotion == "happy":
            t_h = self.base_h * (1.0 + 0.15 * intensity)
            t_w = self.base_w * (1.0 + 0.1 * intensity)
            t_r = 100 
            t_y = -15 * intensity 
            t_psz = 35 + 10 * intensity 
            t_py = -10 

        elif emotion == "sad":
            t_a = 15 * intensity 
            t_h = self.base_h * 0.9
            t_w = self.base_w * 0.95
            t_y = 20 * intensity
            t_py = 25 * intensity
            t_px = -15 * intensity

        elif emotion == "angry":
            t_a = -25 * intensity
            t_h = self.base_h * (0.8 - 0.2 * intensity)
            t_w = self.base_w * 1.0 
            t_r = 10
            t_y = 10 
            t_g = 90 - 15 * intensity 
            t_psz = 20
            t_py = 5 

        elif emotion == "surprised":
            t_h = self.base_h * 1.3
            t_w = self.base_w * 0.85
            t_r = 60
            t_g = 100 
            t_psz = 15
        
        elif emotion == "fear":
            t_h = self.base_h * 0.85
            t_w = self.base_w * 0.9
            t_psz = 20
            t_py = 10

        # 防穿模
        min_gap = (t_w / 2) + (SAFETY_MARGIN / 2)
        if t_g < min_gap:
            t_g = min_gap

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

    def _process_idle_behavior(self):
        """待机自主动作"""
        now = time.time()
        if now - self.last_cmd_time > 3.0:
            if now > self.next_idle_move:
                action = random.choice(["look_left", "look_right", "look_up", "center", "squint"])
                
                p = self.props
                if action == "look_left":
                    p["pupil_x"].set(-25)
                    p["pupil_y"].set(0)
                elif action == "look_right":
                    p["pupil_x"].set(25)
                    p["pupil_y"].set(0)
                elif action == "look_up":
                    p["pupil_x"].set(0)
                    p["pupil_y"].set(-20)
                elif action == "center":
                    p["pupil_x"].set(0)
                    p["pupil_y"].set(0)
                    p["height"].set(self.base_h)
                elif action == "squint":
                    p["height"].set(self.base_h * 0.7)
                    
                self.next_idle_move = now + random.uniform(1.0, 4.0)

    def _physics_step(self):
        """物理更新"""
        self._process_idle_behavior()

        curr_time = time.time()
        if not self.is_blinking and curr_time > self.next_blink:
            self.is_blinking = True
            self.blink_start = curr_time
            self.pre_blink_h = self.props["height"].target 
            self.props["height"].set(5) 
        
        if self.is_blinking:
            if curr_time - self.blink_start > 0.15:
                self.is_blinking = False
                self.props["height"].set(self.pre_blink_h)
                self.next_blink = curr_time + random.uniform(2, 6)

        for key in self.props:
            self.props[key].update()

    def _draw_eye(self, cx, cy, is_left):
        """绘制单个眼睛"""
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
        """关闭显示"""
        self.running = False
        if self._render_thread:
            self._render_thread.join(timeout=1.0)


# 全局实例
eye_display = EyeDisplay()


# 测试用
if __name__ == "__main__":
    display = EyeDisplay()
    display.start(fullscreen=False)
    
    emotions = ["happy", "sad", "angry", "neutral", "surprised", "fear"]
    
    for emotion in emotions:
        display.update_emotion(emotion)
        time.sleep(3)
    
    display.close()