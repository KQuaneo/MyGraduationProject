import pygame
import threading
import queue
import time
import math
import random

# --- 全局配置 (调优后的配色方案) ---
# 根据实际屏幕分辨率设置 (HDMI 屏幕为 1024x600)
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 600

# 配色：赛博/二次元风格
BG_COLOR = (20, 20, 28)           # 深邃背景
SCLERA_COLOR = (245, 248, 255)    # 稍微带冷色调的眼白
SCLERA_SHADOW = (180, 180, 200)   # 眼白投影
# 虹膜配色方案 (宝石蓝)
IRIS_TOP = (20, 40, 90)           # 虹膜顶部（深邃）
IRIS_BOTTOM = (60, 160, 240)      # 虹膜底部（透光）
IRIS_RIM = (10, 20, 50)           # 虹膜外圈轮廓
PUPIL_COLOR = (10, 10, 20)        # 瞳孔
HIGHLIGHT_MAIN = (255, 255, 255)  # 主高光
HIGHLIGHT_SEC = (200, 230, 255)   # 次高光
OUTLINE_COLOR = (20, 20, 30)      # 睫毛/眼线颜色

FPS = 60

class Spring:
    """物理弹簧类 (保持不变，参数已调优)"""
    def __init__(self, val, k=0.15, d=0.75, precision=0.001):
        self.target = val
        self.val = val
        self.vel = 0
        self.k = k
        self.d = d
        self.precision = precision

    def update(self):
        force = (self.target - self.val) * self.k
        self.vel += force
        self.vel *= self.d
        if abs(self.vel) < self.precision and abs(self.target - self.val) < self.precision:
            self.val = self.target
            self.vel = 0
        else:
            self.val += self.vel
        return self.val

    def set(self, target):
        self.target = target
    
    def set_immediate(self, val):
        self.target = val
        self.val = val
        self.vel = 0

class EyeDisplay:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized: return
        self._initialized = True
        self.screen = None
        self.clock = None
        self.running = False
        self._emotion_queue = queue.Queue()
        
        self.base_w = 210
        self.base_h = 170
        
        self.props = None
        self.last_cmd_time = time.time()
        self.start_time = time.time()
        
        # --- 状态控制 ---
        self.is_blinking = False
        self.next_blink = time.time() + 2
        self.pre_blink_h = self.base_h
        self.pre_blink_lid = 0
        self.blink_duration = 0.12
        self.blink_phase = 0
        self.blink_start = 0

        self.current_emotion = "neutral"
        self.emotion_idle_end_time = 0
        self.next_micro_move = time.time()
        
        # --- 渲染特效变量 ---
        self.breath_phase = 0
        self.highlight_alpha = 255
        
    def _init_props(self):
        # 参数经过微调，使运动更Q弹
        self.props = {
            "width":      Spring(self.base_w, k=0.12, d=0.70),
            "height":     Spring(self.base_h, k=0.12, d=0.70),
            "angle":      Spring(0.0, k=0.1, d=0.65),
            "gap":        Spring(120.0, k=0.08, d=0.75),
            "y_off":      Spring(0.0, k=0.08, d=0.75),
            "pupil_x":    Spring(0.0, k=0.20, d=0.60), # 瞳孔响应更快
            "pupil_y":    Spring(0.0, k=0.20, d=0.60),
            "pupil_sz":   Spring(38.0, k=0.15, d=0.7),
            "lid_top":    Spring(0.0, k=0.25, d=0.55), # 眼睑稍微欠阻尼，有点回弹
            "lid_bottom": Spring(0.0, k=0.20, d=0.65),
            "squint":     Spring(0.0, k=0.15, d=0.70),
            "brow_angle": Spring(0.0, k=0.12, d=0.65),
        }

    def _run_loop(self, fullscreen=True):
        pygame.init()
        print(f"🖥️ 初始化显示: 全屏={fullscreen}, 分辨率={SCREEN_WIDTH}x{SCREEN_HEIGHT}")
        flags = pygame.FULLSCREEN if fullscreen else pygame.NOFRAME
        if not fullscreen:
            # 如果不是全屏，设置一个合理的窗口大小
            self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), flags)
        else:
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
            
        pygame.display.set_caption("Anime Robot Eyes")
        pygame.mouse.set_visible(False)
        print(f"✅ 显示初始化成功: 屏幕尺寸={self.screen.get_size()}")
        self.clock = pygame.time.Clock()
        self._init_props()
        self.running = True
        self.start_time = time.time()
        
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT: self.running = False
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE: self.running = False
            
            try:
                data = self._emotion_queue.get_nowait()
                self._apply_emotion_command(data['emotion'], data['intensity'])
            except queue.Empty: pass

            self._physics_step()
            self._render_frame()
            pygame.display.flip()
            self.clock.tick(FPS)
        
        pygame.quit()

    def update_emotion(self, emotion, intensity=1.0):
        self._emotion_queue.put({"emotion": emotion.lower(), "intensity": intensity})

    def _apply_emotion_command(self, emotion, intensity):
        self.last_cmd_time = time.time()
        self.current_emotion = emotion
        self.emotion_idle_end_time = time.time() + random.uniform(8.0, 15.0)
        
        # 默认值复位
        t_w, t_h = self.base_w, self.base_h
        t_a, t_g, t_y = 0, 120, 0
        t_px, t_py, t_psz = 0, 0, 38
        t_lid_top, t_lid_bottom, t_squint, t_brow = 0, 0, 0, 0

        # --- 情绪映射逻辑 (优化了表情张力) ---
        if emotion == "happy":
            t_h = self.base_h * 1.05       # 高度稍微增加一点点即可
            # 关键修改：
            t_lid_top = 0.10 * intensity   # 上眼皮几乎不动 (或者只动 10%)，保持 U 形
            t_lid_bottom = 0.60 * intensity # 下眼皮大幅度向上拱起！这是笑眼的核心
            
            t_squint = 0.4 * intensity     # 稍微眯一点眼角
            t_brow = -6 * intensity        # 眉毛微抬
            t_psz = 42                     # 瞳孔微大
            
        elif emotion == "sad":
            t_a = 15 * intensity           # 八字眼
            t_brow = 25 * intensity        # 眉毛八字
            t_lid_top = 0.3 * intensity    # 没什么精神
            t_py = 15 * intensity          # 向下看
            t_psz = 42
            
        elif emotion == "angry":
            t_a = -15 * intensity          # 吊眼角
            t_brow = -30 * intensity       # 愤怒眉毛
            t_lid_top = 0.25 * intensity
            t_squint = 0.5 * intensity
            t_psz = 25                     # 瞳孔收缩
            t_g = 100                      # 眼睛间距变窄（聚焦）

        elif emotion == "surprised":
            t_h = self.base_h * 1.35
            t_w = self.base_w * 0.95
            t_psz = 20                     # 极度收缩
            t_brow = 15                    # 眉毛高挑
            
        elif emotion == "thinking":
            t_px = 35                      # 向右上/左上看
            t_py = -25
            t_lid_top = 0.2
            t_squint = 0.2
            
        elif emotion == "sleepy":
            t_h = self.base_h * 0.8
            t_lid_top = 0.75               # 就要闭上了
            t_brow = 5

        # 应用目标值
        p = self.props
        p["width"].set(t_w); p["height"].set(t_h)
        p["angle"].set(t_a); p["gap"].set(t_g); p["y_off"].set(t_y)
        p["pupil_x"].set(t_px); p["pupil_y"].set(t_py); p["pupil_sz"].set(t_psz)
        p["lid_top"].set(t_lid_top); p["lid_bottom"].set(t_lid_bottom)
        p["squint"].set(t_squint); p["brow_angle"].set(t_brow)

    def _physics_step(self):
        now = time.time()
        # 呼吸正弦波 (0.0 ~ 1.0)
        self.breath_phase = (math.sin(now * 2.5) + 1) * 0.5
        
        # 眨眼逻辑 (两阶段：快速闭合 -> 弹性张开)
        if not self.is_blinking and now > self.next_blink:
            self.is_blinking = True
            self.blink_start = now
            self.blink_phase = 0
            self.pre_blink_h = self.props["height"].target
            self.pre_blink_lid = self.props["lid_top"].target
            
        if self.is_blinking:
            elapsed = now - self.blink_start
            if self.blink_phase == 0: # 闭眼
                self.props["lid_top"].set(1.05) # 稍微过冲一点确保完全闭合
                self.props["height"].set(self.base_h * 0.4)
                if elapsed > self.blink_duration * 0.35:
                    self.blink_phase = 1
            else: # 睁眼
                self.props["lid_top"].set(self.pre_blink_lid)
                self.props["height"].set(self.pre_blink_h)
                if elapsed > self.blink_duration:
                    self.is_blinking = False
                    self.next_blink = now + random.uniform(1.5, 4.5)

        # 闲置时的微动作 (Saccades)
        if now > self.next_micro_move and not self.is_blinking:
            if self.current_emotion == "neutral":
                offset_x = random.uniform(-5, 5)
                offset_y = random.uniform(-5, 5)
                self.props["pupil_x"].set(offset_x)
                self.props["pupil_y"].set(offset_y)
            self.next_micro_move = now + random.uniform(0.5, 2.0)

        # 更新所有弹簧
        for k in self.props:
            self.props[k].update()

    def _draw_gradient_rect(self, surf, color_top, color_bot, rect):
        """绘制垂直渐变矩形"""
        colour_rect = pygame.Surface((2, 2))
        pygame.draw.line(colour_rect, color_top, (0, 0), (1, 0))
        pygame.draw.line(colour_rect, color_bot, (0, 1), (1, 1))
        colour_rect = pygame.transform.smoothscale(colour_rect, (rect.width, rect.height))
        surf.blit(colour_rect, rect)

    def _draw_eye(self, cx, cy, is_left):
        p = self.props
        # 呼吸缩放效果
        breath_scale = 1.0 + self.breath_phase * 0.015
        
        w = p["width"].val * breath_scale
        h = p["height"].val * breath_scale
        
        # 创建画布 (Super-sampling 抗锯齿技巧: 画大一倍，再缩小)
        scale_factor = 2 
        canvas_size = int(max(w, h) * 3)
        surf = pygame.Surface((canvas_size * scale_factor, canvas_size * scale_factor), pygame.SRCALPHA)
        center_x = surf.get_width() // 2
        center_y = surf.get_height() // 2
        
        # 1. 眼白 (Sclera)
        sclera_rect = pygame.Rect(0, 0, w * scale_factor, h * scale_factor)
        sclera_rect.center = (center_x, center_y)
        pygame.draw.ellipse(surf, SCLERA_COLOR, sclera_rect)
        
        # 2. 虹膜 (Iris) - 宝石质感核心
        px = p["pupil_x"].val * scale_factor
        py = p["pupil_y"].val * scale_factor
        # 限制虹膜在眼白内
        max_r = (w/2 - p["pupil_sz"].val) * scale_factor
        dist = math.hypot(px, py)
        if dist > max_r:
            angle = math.atan2(py, px)
            px = math.cos(angle) * max_r
            py = math.sin(angle) * max_r
            
        iris_pos = (int(center_x + (px if is_left else -px)), int(center_y + py))
        iris_radius = int(p["pupil_sz"].val * 2.2 * scale_factor)
        
        # 2.1 虹膜外轮廓
        pygame.draw.circle(surf, IRIS_RIM, iris_pos, iris_radius)
        
        # 2.2 虹膜内部渐变 (模拟上深下浅)
        iris_inner_r = int(iris_radius * 0.92)
        # 技巧：用一系列从上到下颜色变浅的圆叠加，或者直接画一个mask
        iris_surf = pygame.Surface((iris_inner_r*2, iris_inner_r*2), pygame.SRCALPHA)
        # 绘制深色背景
        pygame.draw.circle(iris_surf, IRIS_TOP, (iris_inner_r, iris_inner_r), iris_inner_r)
        # 绘制底部的亮色U型 (Subsurface Scattering)
        u_rect = pygame.Rect(0, iris_inner_r, iris_inner_r*2, iris_inner_r)
        pygame.draw.ellipse(iris_surf, IRIS_BOTTOM, u_rect)
        # 模糊混合一下 (可选，这里用简单的层叠模拟)
        
        surf.blit(iris_surf, (iris_pos[0]-iris_inner_r, iris_pos[1]-iris_inner_r), special_flags=pygame.BLEND_ALPHA_SDL2)
        
        # 3. 瞳孔 (Pupil)
        pupil_r = int(p["pupil_sz"].val * scale_factor)
        pygame.draw.circle(surf, PUPIL_COLOR, iris_pos, pupil_r)
        
        # 4. 高光 (Highlights) - 关键的灵魂
        # 主高光 (左上)
        hl_size = int(pupil_r * 0.5)
        hl_offset_x = -pupil_r * 0.5
        hl_offset_y = -pupil_r * 0.5
        hl_pos = (iris_pos[0] + hl_offset_x, iris_pos[1] + hl_offset_y)
        pygame.draw.circle(surf, HIGHLIGHT_MAIN, hl_pos, hl_size)
        
        # 次高光 (右下，小一点，锐利一点)
        hl2_size = int(pupil_r * 0.25)
        hl2_pos = (iris_pos[0] - hl_offset_x * 0.8, iris_pos[1] - hl_offset_y * 0.8)
        pygame.draw.circle(surf, HIGHLIGHT_SEC, hl2_pos, hl2_size)
        
        # 5. 眼白内部阴影 (顶部投影，增加立体感)
        shadow_h = int(h * 0.25 * scale_factor)
        shadow_rect = pygame.Rect(sclera_rect.left, sclera_rect.top, sclera_rect.width, shadow_h)
        # 使用Clip mask技巧只画在眼白里(这里简化处理，直接画弧形)
        pygame.draw.arc(surf, (150,150,170), sclera_rect, 0, 3.14, int(10*scale_factor))

# --- 6. 绘制眼睑 (重构版：拒绝诡异的倒拱形) ---
        
        # 参数获取
        lid_top = p["lid_top"].val
        lid_bot = p["lid_bottom"].val
        squint = p["squint"].val
        
        # [关键修复1] 上眼睑逻辑回归正常
        # 不再通过 brow_angle 判断是否反转曲线，永远保持自然的下垂弧度 (U形)
        # 这样能保证眼神的稳重和可爱，不会出现“疯狂眼神”
        closure = lid_top + squint * 0.3
        
        # 基础坐标
        base_y = sclera_rect.top
        # 这种算法让眼皮两边低，中间稍微高一点点，形成自然的弧度
        curve_depth = 20 * scale_factor # 弧度深度
        
        # 计算贝塞尔控制点
        # 随着闭合度增加，整体下降
        current_y_mid = base_y + (h * scale_factor * closure)
        
        # 左右顶点 (稍微比中间低，形成 U 形)
        left_pt = (sclera_rect.left - 15 * scale_factor, current_y_mid - curve_depth)
        right_pt = (sclera_rect.right + 15 * scale_factor, current_y_mid - curve_depth)
        # 控制点 (在中间，比两边低，拉出弧度)
        ctrl_pt_top = (sclera_rect.centerx, current_y_mid + curve_depth)

        # 生成上眼睑曲线点
        curve_points_top = []
        steps = 20
        for i in range(steps + 1):
            t = i / steps
            bx = (1-t)**2 * left_pt[0] + 2*(1-t)*t * ctrl_pt_top[0] + t**2 * right_pt[0]
            by = (1-t)**2 * left_pt[1] + 2*(1-t)*t * ctrl_pt_top[1] + t**2 * right_pt[1]
            curve_points_top.append((bx, by))
            
        # 绘制上眼睑遮罩
        mask_poly_top = [(0,0), (surf.get_width(), 0)] + list(reversed(curve_points_top)) + [(0,0)]
        pygame.draw.polygon(surf, BG_COLOR, mask_poly_top)
        
        # 绘制上睫毛
        if closure < 0.9:
            # 睁眼时画曲线
            pygame.draw.lines(surf, OUTLINE_COLOR, False, curve_points_top, int(14 * scale_factor))
        else:
            # 闭眼时画一条横线（看起来像睡觉）
            pygame.draw.line(surf, OUTLINE_COLOR, left_pt, right_pt, int(12 * scale_factor))

        # --- 7. 下眼睑 (关键修复2：让它变成微笑曲线) ---
        # 如果是 Happy 状态，lid_bottom 会变大
        # 我们让下眼睑向上拱起 (∩ 形)，模拟脸颊肉挤压
        
        if lid_bot > 0.01:
            # 计算下眼睑的高度
            bot_rise = h * scale_factor * lid_bot * 0.8
            bot_base_y = sclera_rect.bottom
            
            # 左点、右点
            bot_left = (sclera_rect.left - 10 * scale_factor, bot_base_y - bot_rise * 0.5)
            bot_right = (sclera_rect.right + 10 * scale_factor, bot_base_y - bot_rise * 0.5)
            
            # 控制点：要在两点上方，形成 ∩ 拱形！这才是笑眼的关键！
            # bot_rise 越大，拱得越高
            bot_ctrl = (sclera_rect.centerx, bot_base_y - bot_rise * 1.5)
            
            # 计算下眼睑曲线
            curve_points_bot = []
            for i in range(steps + 1):
                t = i / steps
                bx = (1-t)**2 * bot_left[0] + 2*(1-t)*t * bot_ctrl[0] + t**2 * bot_right[0]
                by = (1-t)**2 * bot_left[1] + 2*(1-t)*t * bot_ctrl[1] + t**2 * bot_right[1]
                curve_points_bot.append((bx, by))
            
            # 绘制下眼睑遮罩 (遮住下方)
            mask_poly_bot = [
                (0, surf.get_height()), 
                (surf.get_width(), surf.get_height()), 
                (surf.get_width(), bot_right[1]),
            ] + list(reversed(curve_points_bot)) + [(0, bot_left[1])]
            
            pygame.draw.polygon(surf, BG_COLOR, mask_poly_bot)
            
            # 绘制下眼线
            pygame.draw.lines(surf, OUTLINE_COLOR, False, curve_points_bot, int(8 * scale_factor))

        # --- 8. 眉毛 (简单优化位置) ---
        # 眉毛位置随上眼皮微调，避免穿模
        brow_y_adj = -20 * scale_factor
        if lid_top > 0.5: brow_y_adj += 30 * scale_factor # 闭眼时眉毛下降
        
        brow_y = sclera_rect.top + brow_y_adj + (p["brow_angle"].val * 2 * scale_factor)
        # ... (眉毛绘制代码保持之前的即可) ...
        brow_rot = p["brow_angle"].val * 0.5
        brow_cx = sclera_rect.centerx
        brow_L = (brow_cx - 80 * scale_factor, brow_y + (brow_rot if is_left else -brow_rot) * 2)
        brow_R = (brow_cx + 80 * scale_factor, brow_y - (brow_rot if is_left else -brow_rot) * 2)
        pygame.draw.line(surf, OUTLINE_COLOR, brow_L, brow_R, int(10 * scale_factor))

        # --- 后续的缩放和blit保持不变 ---
        surf = pygame.transform.smoothscale(surf, (canvas_size, canvas_size))
        rot_angle = p["angle"].val if is_left else -p["angle"].val
        if abs(rot_angle) > 0.1:
            surf = pygame.transform.rotate(surf, rot_angle)
        dest_rect = surf.get_rect(center=(cx - p["gap"].val if is_left else cx + p["gap"].val, cy + p["y_off"].val))
        self.screen.blit(surf, dest_rect)

    def _render_frame(self):
        self.screen.fill(BG_COLOR)
        
        # 绘制简单的晕影背景 (Vignette) 增加氛围
        # 这里用一种廉价的方式：画几个透明度极低的大圆
        cx, cy = self.screen.get_width()//2, self.screen.get_height()//2
        # pygame.draw.circle(self.screen, (30, 30, 45), (cx, cy), 400)
        
        self._draw_eye(cx, cy, True)   # 左
        self._draw_eye(cx, cy, False)  # 右

if __name__ == "__main__":
    eyes = EyeDisplay()
    
    # 测试线程
    def command_thread():
        time.sleep(1)
        emotions = ["happy", "surprised", "angry", "sad", "thinking", "neutral"]
        while True:
            emo = random.choice(emotions)
            eyes.update_emotion(emo)
            time.sleep(random.uniform(3, 5))

    t = threading.Thread(target=command_thread, daemon=True)
    t.start()
    
    # 启动全屏显示 (按 ESC 退出)
    eyes._run_loop(fullscreen=False)