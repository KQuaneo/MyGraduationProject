#!/usr/bin/env python3
"""测试耳朵舵机功能"""
import sys
import os
import time

# 确保模块路径正确
sys.path.insert(0, '/home/raspberrypi/Desktop/MyGraduationProject/brain/online_agent')

from modules.ears import EarController

print("🐰 测试耳朵舵机...")
print("=" * 40)

try:
    # 初始化
    print("1️⃣ 初始化耳朵控制器...")
    ear = EarController()
    
    if not ear.enabled:
        print("❌ 耳朵控制器初始化失败")
        sys.exit(1)
    
    print("2️⃣ 等待 1 秒...")
    time.sleep(1)
    
    # 测试 happy 动作
    print("3️⃣ 执行 'happy' 动作...")
    ear.update_emotion('happy')
    time.sleep(3)
    
    # 测试 surprise 动作
    print("4️⃣ 执行 'surprise' 动作...")
    ear.update_emotion('surprise')
    time.sleep(2)
    
    # 回到 neutral
    print("5️⃣ 回到 neutral...")
    ear.update_emotion('neutral')
    time.sleep(1)
    
    # 停止
    print("6️⃣ 停止耳朵控制器...")
    ear.stop()
    
    print("=" * 40)
    print("✅ 测试完成！")
    
except Exception as e:
    print(f"❌ 测试出错: {e}")
    import traceback
    traceback.print_exc()
