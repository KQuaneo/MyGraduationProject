#!/usr/bin/env python3
"""
紧急停止所有舵机（用于异响时快速修复）
"""
import sys
sys.path.insert(0, '/home/raspberrypi/Desktop/MyGraduationProject/brain/online_agent')

from modules.pca9685_manager import PCA9685Manager

print("🛑 紧急停止所有舵机...")
PCA9685Manager.reset_all_channels()
print("✅ 所有舵机已停止")
