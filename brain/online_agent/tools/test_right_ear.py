#!/usr/bin/env python3
"""
右耳舵机（通道1）单独诊断测试
"""
import sys
import time

sys.path.insert(0, '/home/raspberrypi/Desktop/MyGraduationProject/brain/online_agent')

from adafruit_motor import servo
from modules.pca9685_manager import get_channel, PCA9685Manager

print("🐰 右耳舵机（通道1）诊断测试")
print("=" * 50)

def test_channel_raw(channel_num, name):
    """原始 PWM 测试"""
    print(f"\n📍 测试 {name} (通道 {channel_num}) - 原始 PWM 模式")
    print("-" * 40)
    
    try:
        ch = get_channel(channel_num)
        
        # 测试 1: 最小占空比
        print("  → 测试最小占空比 (约 0°)")
        ch.duty_cycle = 0x0666  # ~2.5% (0.5ms / 20ms)
        time.sleep(1)
        
        # 测试 2: 中间占空比
        print("  → 测试中间占空比 (约 15°)")
        ch.duty_cycle = 0x0CCC  # ~5% (1.0ms / 20ms)
        time.sleep(1)
        
        # 测试 3: 最大占空比
        print("  → 测试最大占空比 (约 30°+)")
        ch.duty_cycle = 0x1333  # ~7.5% (1.5ms / 20ms)
        time.sleep(1)
        
        # 关闭
        ch.duty_cycle = 0
        print(f"  ✅ {name} 原始 PWM 测试完成")
        return True
        
    except Exception as e:
        print(f"  ❌ {name} 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_servo_lib(channel_num, name):
    """使用 adafruit_servokit 测试"""
    print(f"\n📍 测试 {name} (通道 {channel_num}) - Servo 库模式")
    print("-" * 40)
    
    try:
        srv = servo.Servo(get_channel(channel_num), min_pulse=500, max_pulse=2500)
        
        print("  → 0°")
        srv.angle = 0
        time.sleep(1)
        
        print("  → 15°")
        srv.angle = 15
        time.sleep(1)
        
        print("  → 20°")
        srv.angle = 20
        time.sleep(1)
        
        print("  → 回到 0°")
        srv.angle = 0
        time.sleep(1)
        
        # 关闭 PWM
        get_channel(channel_num).duty_cycle = 0
        print(f"  ✅ {name} Servo 库测试完成")
        return True
        
    except Exception as e:
        print(f"  ❌ {name} 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

try:
    # 先重置所有通道
    print("🔧 重置 PCA9685...")
    PCA9685Manager.reset_all_channels()
    time.sleep(0.5)
    
    # 测试右耳（通道1）
    print("\n" + "=" * 50)
    print("开始测试右耳...")
    
    # 方法1: 原始 PWM 测试
    raw_ok = test_channel_raw(1, "右耳")
    
    time.sleep(0.5)
    
    # 方法2: Servo 库测试
    servo_ok = test_servo_lib(1, "右耳")
    
    # 总结
    print("\n" + "=" * 50)
    print("📊 测试结果:")
    print(f"  原始 PWM 测试: {'✅ 通过' if raw_ok else '❌ 失败'}")
    print(f"  Servo 库测试:  {'✅ 通过' if servo_ok else '❌ 失败'}")
    
    if not raw_ok and not servo_ok:
        print("\n⚠️ 两个测试都失败，可能是:")
        print("  1. 舵机硬件损坏")
        print("  2. 接线松动")
        print("  3. PCA9685 通道 1 损坏")
        print("\n建议: 尝试将右耳插到通道 4 测试")
    elif raw_ok and not servo_ok:
        print("\n⚠️ PWM 正常但 Servo 库失败，可能是库配置问题")
    else:
        print("\n✅ 右耳测试通过！")
    
except KeyboardInterrupt:
    print("\n\n⚠️ 测试被中断")
    
finally:
    print("\n🔌 清理...")
    PCA9685Manager.reset_all_channels()
    print("✅ 完成")
