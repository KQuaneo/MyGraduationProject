#!/usr/bin/env python3
"""
耳朵舵机物理角度测试
分别测试左耳和右耳从 0度 到 30度 的运动
"""
import sys
import os
import time

# 确保模块路径正确
sys.path.insert(0, '/home/raspberrypi/Desktop/MyGraduationProject/brain/online_agent')

from adafruit_motor import servo
from modules.pca9685_manager import get_channel

print("🐰 耳朵舵机物理角度测试")
print("=" * 50)
print("左耳 = 通道 2，右耳 = 通道 1")
print("测试范围: 0° ~ 20°")
print("=" * 50)

def test_servo(name, channel_num, min_angle=0, max_angle=30):
    """测试单个舵机"""
    print(f"\n📍 测试{name} (通道 {channel_num})")
    print("-" * 30)
    
    try:
        # 初始化舵机
        srv = servo.Servo(get_channel(channel_num), min_pulse=500, max_pulse=2500)
        
        # 回到 0 度
        print(f"  → 归位到 0°")
        srv.angle = min_angle
        time.sleep(1)
        
        # 逐步增加到 30 度
        for angle in range(min_angle + 5, max_angle + 1, 3):
            print(f"  → 移动到 {angle}°")
            srv.angle = angle
            time.sleep(0.5)
        
        # 保持 30 度
        print(f"  → 保持 20° 2秒")
        time.sleep(2)
        
        # 回到 0 度
        print(f"  → 回到 0°")
        srv.angle = min_angle
        time.sleep(1)
        
        # 关闭 PWM
        get_channel(channel_num).duty_cycle = 0
        print(f"  ✅ {name}测试完成")
        
    except Exception as e:
        print(f"  ❌ {name}测试失败: {e}")
        import traceback
        traceback.print_exc()

try:
    # 测试左耳 (通道 2)
    test_servo("左耳", 2)
    
    time.sleep(1)
    
    # 测试右耳 (通道 1)
    test_servo("右耳", 1)
    
    print("\n" + "=" * 50)
    print("✅ 所有测试完成！")
    
except KeyboardInterrupt:
    print("\n\n⚠️ 测试被中断")
    
finally:
    # 确保所有通道关闭
    print("\n🔌 关闭所有舵机通道...")
    for i in range(16):
        try:
            get_channel(i).duty_cycle = 0
        except:
            pass
    print("✅ 已清理")
