#!/usr/bin/env python3
"""
底盘舵机独立测试
不依赖视觉系统，直接测试底盘转动功能
"""
import sys
import time
sys.path.insert(0, '/home/raspberrypi/Desktop/MyGraduationProject/brain/online_agent')

from modules.chassis import ChassisController

print("="*50)
print("底盘舵机独立测试")
print("="*50)

try:
    # 初始化底盘（使用共享 PCA9685）
    print("\n1. 初始化底盘控制器...")
    chassis = ChassisController(channel_index=0)
    
    if not chassis.running:
        print("❌ 底盘初始化失败")
        sys.exit(1)
    
    print("✅ 底盘初始化成功")
    
    # 测试 1: 直接动作指令
    print("\n2. 测试动作指令 (shake - 摇头)...")
    chassis.add_action("shake")
    time.sleep(3)  # 等待动作完成
    
    # 测试 2: 视觉跟随模拟
    print("\n3. 测试视觉跟随模拟...")
    print("   模拟人脸在左边 (error_x = -0.5)")
    chassis.update_vision_data(-0.5)
    time.sleep(2)
    
    print("   模拟人脸在右边 (error_x = 0.5)")
    chassis.update_vision_data(0.5)
    time.sleep(2)
    
    print("   模拟人脸在中间 (error_x = 0)")
    chassis.update_vision_data(0)
    time.sleep(2)
    
    print("   模拟无人 (error_x = None)")
    chassis.update_vision_data(None)
    time.sleep(1)
    
    # 测试 3: 其他动作
    print("\n4. 测试其他动作...")
    print("   look_away 动作")
    chassis.add_action("look_away")
    time.sleep(2)
    
    print("   wiggle 动作")
    chassis.add_action("wiggle")
    time.sleep(2)
    
    print("\n✅ 所有测试完成")
    
    # 释放资源
    chassis.running = False
    time.sleep(0.5)
    
    from modules.pca9685_manager import PCA9685Manager
    PCA9685Manager.deinit()
    print("🔌 PCA9685 已释放")
    
except Exception as e:
    print(f"\n❌ 测试出错: {e}")
    import traceback
    traceback.print_exc()
