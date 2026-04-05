#!/usr/bin/env python3
"""
底盘舵机保持力测试
保持舵机在中位，方便手动轻推测试回弹和保持力。
按 Ctrl+C 退出并释放 PCA9685。
"""
import sys
import time

sys.path.insert(0, "/home/raspberrypi/Desktop/MyGraduationProject/brain/online_agent")

from modules.chassis import ChassisController
from modules.pca9685_manager import PCA9685Manager


def main() -> int:
    print("=" * 50)
    print("底盘舵机保持力测试")
    print("=" * 50)
    print("1. 初始化底盘控制器...")

    chassis = ChassisController(channel_index=0)
    if not chassis.running:
        print("❌ 底盘初始化失败")
        return 1

    print("✅ 底盘初始化成功")
    print("2. 保持中位角度 0°")
    chassis.update_vision_data(0.0)
    time.sleep(0.2)

    print("3. 现在可以手动轻轻转动舵盘")
    print("   观察是否有保持力，松手后是否会尝试回到中位")
    print("   按 Ctrl+C 结束测试")

    try:
        while True:
            chassis._set_physical_servo(0.0)
            time.sleep(0.2)
    except KeyboardInterrupt:
        print("\n🛑 收到退出信号，正在释放底盘舵机...")
    finally:
        try:
            chassis.stop()
        finally:
            PCA9685Manager.deinit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
