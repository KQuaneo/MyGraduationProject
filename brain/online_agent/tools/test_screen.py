import os
import pygame
import time

# --- 这里是关键变量 ---
# 尝试 1: 注释掉下一行（让系统自动选）
# 尝试 2: 改为 "x11"
# 尝试 3: 改为 "wayland"
# 尝试 4: 改为 "kmsdrm" (直接写显存，不经过桌面)
os.environ["SDL_VIDEODRIVER"] = "x11" 

pygame.init()

# 强制设为红色背景，绝不会看错
W, H = 1024, 768
screen = pygame.display.set_mode((W, H), pygame.NOFRAME)

running = True
print("开始测试屏幕... 应该是全红的")

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            
    # 填充纯红色
    screen.fill((255, 0, 0))
    
    # 画一个蓝圆圈证明在刷新
    pygame.draw.circle(screen, (0, 0, 255), (W//2, H//2), 100)
    
    pygame.display.flip()
    time.sleep(0.01)