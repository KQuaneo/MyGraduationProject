#!/usr/bin/env python3
"""
强制重置 PCA9685 舵机控制板
用于解决程序异常退出后舵机异响问题
"""
import time
import board
from adafruit_pca9685 import PCA9685

print("🔧 正在强制重置 PCA9685...")

try:
    # 初始化 I2C
    i2c = board.I2C()
    
    # 创建 PCA9685 实例
    pca = PCA9685(i2c)
    pca.frequency = 50
    
    # 关闭所有 16 个通道的 PWM 输出
    print("🔌 正在关闭所有舵机通道...")
    for i in range(16):
        pca.channels[i].duty_cycle = 0
        
    time.sleep(0.2)
    
    # 释放资源
    pca.deinit()
    
    print("✅ PCA9685 已重置，所有舵机已关闭")
    
except Exception as e:
    print(f"❌ 重置失败: {e}")
    print("提示：可能需要 sudo 权限运行")
