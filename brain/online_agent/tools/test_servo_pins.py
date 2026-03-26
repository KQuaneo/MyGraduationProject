#!/usr/bin/env python3
"""
测试 PCA9685 各引脚舵机
用于诊断 1 号引脚异响问题
"""
import time
import board
import busio
from adafruit_pca9685 import PCA9685
from adafruit_motor import servo

def test_servo(channel, name="测试舵机"):
    """测试指定通道的舵机"""
    print(f"\n{'='*40}")
    print(f"测试 {name} (通道 {channel})")
    print(f"{'='*40}")
    
    try:
        i2c = board.I2C()
        pca = PCA9685(i2c)
        pca.frequency = 50
        
        # 初始化舵机
        test_servo = servo.Servo(
            pca.channels[channel],
            actuation_range=270,
            min_pulse=500,
            max_pulse=2500
        )
        
        print(f"✅ 初始化成功")
        print(f"   当前角度: {test_servo.angle}")
        
        # 测试转动
        print("\n测试转动...")
        angles = [0, 45, 90, 135, 90, 45, 0]
        for angle in angles:
            print(f"   -> 转到 {angle}°")
            test_servo.angle = angle
            time.sleep(0.5)
        
        # 释放（设置为0占空比）
        print(f"\n释放舵机 (channel {channel}.duty_cycle = 0)")
        pca.channels[channel].duty_cycle = 0
        
        pca.deinit()
        print(f"✅ {name} 测试完成")
        return True
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False

if __name__ == "__main__":
    print("PCA9685 舵机引脚测试工具")
    print("="*40)
    
    # 测试 0 号引脚（已知正常）
    test_servo(0, "0号引脚-底盘舵机")
    time.sleep(1)
    
    # 测试 1 号引脚（问题引脚）
    test_servo(1, "1号引脚-问题舵机")
    time.sleep(1)
    
    # 测试 2 号引脚（已知正常）
    test_servo(2, "2号引脚-耳朵舵机")
    
    print("\n" + "="*40)
    print("所有测试完成")
    print("="*40)
