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

emotion_queue = queue.Queue()

# ==========================================
# 1. 物理弹簧类 (让动作Q弹的核心)
# ==========================================
class Spring:
    def __init__(self, val, k=0.1, d=0.8):
        self.target = val   # 目标值
        self.val = val      # 当前值
        self.vel = 0        # 当前速度
        self.k = k          # 刚度 (Stiffness): 越大越硬，回弹越快
        self.d = d          # 阻尼 (Damping): 0-1之间，越小摩擦力越小(晃得越久)

    def update(self):
        # 弹簧力公式: F = -k * x
        force = (self.target - self.val) * self.k
        self.vel += force
        self.vel *= self.d  # 摩擦力损耗
        self.val += self.vel
        return self.val

    def set(self, target):
        self.target = target

# ==========================================
# 2. 渲染主类
# ==========================================
class FaceRenderer:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
        pygame.display.set_caption("Robot Face V5 - Physics & Idle")
        self.clock = pygame.time.Clock()
        
        self.base_w = 150
        self.base_h = 190
        
        # 将每个属性都变成一个独立的弹簧对象
        # 参数调整技巧: k越大反应越快, d越小回弹越明显
        self.props = {
            "width":    Spring(self.base_w, k=0.08, d=0.75),
            "height":   Spring(self.base_h, k=0.08, d=0.75),
            "radius":   Spring(40.0, k=0.1, d=0.8),
            "angle":    Spring(0.0, k=0.05, d=0.7), # 旋转有些惯性
            "gap":      Spring(90.0, k=0.05, d=0.8),
            "y_off":    Spring(0.0, k=0.05, d=0.8),
            "pupil_x":  Spring(0.0, k=0.15, d=0.7), # 瞳孔动得很快
            "pupil_y":  Spring(0.0, k=0.15, d=0.7),
            "pupil_sz": Spring(30.0, k=0.1, d=0.8)
        }
        
        # 状态管理
        self.last_cmd_time = time.time()
        self.is_blinking = False
        self.next_blink = time.time() + 2
        
        # 待机动作计时器
        self.next_idle_move = time.time() + 2

    def update_target(self, emotion, intensity):
        """接收指令并设定弹簧的目标值"""
        print(f"[GUI] 切换: {emotion}")
        self.last_cmd_time = time.time() # 只要有指令，重置待机计时
        
        # 基础参数复位
        t_w, t_h = self.base_w, self.base_h
        t_r, t_a, t_g, t_y = 50, 0, 90, 0
        t_px, t_py, t_psz = 0, 0, 30

        # --- 情绪逻辑 (沿用 V4) ---
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

        # --- 防穿模 ---
        min_gap = (t_w / 2) + (SAFETY_MARGIN / 2)
        if t_g < min_gap: t_g = min_gap

        # --- 将目标值赋给弹簧 ---
        # 注意：这里我们不动 .val (当前值)，只动 .target (目标值)
        # 弹簧会在 update() 里自己算物理
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

    def process_idle_behavior(self):
        """如果没有指令，自己动一动"""
        now = time.time()
        # 如果超过 3 秒没有新指令，进入 Idle 模式
        if now - self.last_cmd_time > 3.0:
            if now > self.next_idle_move:
                # 随机生成一个动作：看左、看右、看上、回正
                action = random.choice(["look_left", "look_right", "look_up", "center", "squint"])
                print(f"[Idle] 自主动作: {action}")
                
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
                    p["height"].set(self.base_h) # 恢复高度
                elif action == "squint":
                    p["height"].set(self.base_h * 0.7) # 稍微眯眼思考
                    
                # 下次动作在 1~4 秒后
                self.next_idle_move = now + random.uniform(1.0, 4.0)

    def physics_step(self):
        # 1. 处理待机动作
        self.process_idle_behavior()

        # 2. 眨眼逻辑 (覆盖高度)
        curr_time = time.time()
        if not self.is_blinking and curr_time > self.next_blink:
            self.is_blinking = True
            self.blink_start = curr_time
            # 眨眼时，把弹簧的目标设为闭眼
            # 注意：这里我们临时修改弹簧目标，眨眼结束后要恢复
            self.pre_blink_h = self.props["height"].target 
            self.props["height"].set(5) 
        
        if self.is_blinking:
            if curr_time - self.blink_start > 0.15: # 眨眼结束
                self.is_blinking = False
                self.props["height"].set(self.pre_blink_h) # 恢复原来的目标高度
                self.next_blink = curr_time + random.uniform(2, 6)

        # 3. 更新所有弹簧
        for key in self.props:
            self.props[key].update()

    def draw_eye(self, cx, cy, is_left):
        # 从弹簧对象取 .val
        p = self.props
        w, h = p["width"].val, p["height"].val
        r = p["radius"].val
        angle = p["angle"].val
        
        s_size = int(max(w, h) * 1.6)
        surf = pygame.Surface((s_size, s_size), pygame.SRCALPHA)
        center = s_size // 2
        
        # 眼眶
        rect = pygame.Rect(0, 0, w, h)
        rect.center = (center, center)
        valid_r = max(0, min(abs(r), w/2, h/2))
        pygame.draw.rect(surf, EYE_COLOR, rect, border_radius=int(valid_r))
        
        # 瞳孔
        px = p["pupil_x"].val
        py = p["pupil_y"].val
        # 镜像处理
        final_px = center + (px if is_left else -px)
        final_py = center + py
        # 简单限制
        final_py = max(rect.top+10, min(rect.bottom-10, final_py))
        final_px = max(rect.left+10, min(rect.right-10, final_px))
        
        pygame.draw.circle(surf, PUPIL_COLOR, (int(final_px), int(final_py)), int(p["pupil_sz"].val))

        # 旋转
        rot_angle = angle if is_left else -angle
        rot_surf = pygame.transform.rotate(surf, rot_angle)
        
        # 定位
        gap = p["gap"].val
        y_off = p["y_off"].val
        screen_x = cx - gap if is_left else cx + gap
        screen_y = cy + y_off
        
        dest = rot_surf.get_rect(center=(screen_x, screen_y))
        self.screen.blit(rot_surf, dest)

    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT: running = False
            
            # 读取队列
            try:
                data = emotion_queue.get_nowait()
                self.update_target(data['e'], data['i'])
            except: pass

            # 物理计算
            self.physics_step()

            # 渲染
            self.screen.fill(BG_COLOR)
            cx, cy = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2
            self.draw_eye(cx, cy, True)
            self.draw_eye(cx, cy, False)
            
            pygame.display.flip()
            self.clock.tick(FPS)
        pygame.quit()

# --- 测试循环 ---
def test_loop():
    # 测试：先不动，看看 Idle 效果，然后突然给个表情
    print("等待 Idle 模式触发...")
    time.sleep(5) 
    
    seq = [
        ("happy", 1.0),
        ("neutral", 0),
        ("angry", 0.8),
        ("sad", 0.8),
        ("surprised", 1.0)
    ]
    i = 0
    while True:
        e, score = seq[i]
        emotion_queue.put({"e": e, "i": score})
        i = (i + 1) % len(seq)
        # 随机等待时间，如果等久了就会触发 Idle 观察
        time.sleep(random.uniform(2, 6))

if __name__ == "__main__":
    t = threading.Thread(target=test_loop, daemon=True)
    t.start()
    FaceRenderer().run()