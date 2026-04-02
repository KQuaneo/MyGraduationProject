#!/usr/bin/env python3
"""
快速测试耳朵动作库中的所有表情
"""
import sys
import time

sys.path.insert(0, '/home/raspberrypi/Desktop/MyGraduationProject/brain/online_agent')

from modules.ears import EarController

print("🐰 耳朵动作库测试")
print("=" * 40)

emotions = ["neutral", "happy", "surprise", "thinking", "sad"]

try:
    ear = EarController()
    
    if not ear.enabled:
        print("❌ 初始化失败")
        sys.exit(1)
    
    for emotion in emotions:
        print(f"\n🎭 表情: {emotion}")
        ear.update_emotion(emotion)
        time.sleep(3)
    
    print("\n" + "=" * 40)
    print("✅ 测试完成")
    ear.stop()
    
except Exception as e:
    print(f"❌ 错误: {e}")
    import traceback
    traceback.print_exc()
