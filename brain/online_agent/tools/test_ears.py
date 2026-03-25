#!/usr/bin/env python3
"""
耳朵舵机测试脚本 (物理 0°~30° 版本)
测试耳朵舵机的基本运动和情感动作
"""

import time
import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from modules.ears import EarController
except ImportError as e:
    print(f"❌ 导入失败: {e}")
    print("请确保在项目根目录下运行此脚本")
    sys.exit(1)


def test_basic_movement():
    """测试基本角度运动"""
    print("\n" + "="*50)
    print("🐰 耳朵舵机基本运动测试 (物理 0°~30° 范围)")
    print("="*50)
    
    ears = EarController()
    
    if not ears.enabled:
        print("❌ 耳朵控制器初始化失败，请检查硬件连接")
        return
    
    print("✅ 初始化成功！")
    print("\n注意：物理角度范围 0° ~ 30°")
    time.sleep(1)
    
    # 测试1: 归中位置 (0°, 0°)
    print("\n【测试1】归中位置 (0°, 0°)")
    ears._animate("neutral")
    time.sleep(1)
    
    # 测试2: 双耳最大角度 (30°, 30°)
    print("【测试2】双耳最大角度 (30°, 30°)")
    ears.servo0.angle = 30
    ears.servo3.angle = 30
    time.sleep(2)
    
    # 测试3: 左耳最大，右耳归中
    print("【测试3】左耳30°，右耳0°")
    ears.servo0.angle = 30
    ears.servo3.angle = 0
    time.sleep(2)
    
    # 测试4: 左耳归中，右耳最大
    print("【测试4】左耳0°，右耳30°")
    ears.servo0.angle = 0
    ears.servo3.angle = 30
    time.sleep(2)
    
    # 测试5: 范围扫描 (0° 到 30°)
    print("【测试5】范围扫描 (0° 到 30°)")
    for angle in range(0, 31, 5):
        print(f"  角度: {angle}°")
        ears.servo0.angle = angle
        ears.servo3.angle = angle
        time.sleep(0.5)
    
    # 归中
    print("\n归中...")
    ears._animate("neutral")
    
    print("\n✅ 基本运动测试完成！")


def test_emotion_actions():
    """测试情感动作"""
    print("\n" + "="*50)
    print("🎭 耳朵情感动作测试")
    print("="*50)
    
    ears = EarController()
    
    if not ears.enabled:
        print("❌ 耳朵控制器初始化失败")
        return
    
    emotions = ["neutral", "happy", "surprise", "thinking", "sad"]
    
    for emotion in emotions:
        print(f"\n【测试】{emotion}")
        ears.update_emotion(emotion)
        time.sleep(3)
    
    print("\n✅ 情感动作测试完成！")


def test_single_servo():
    """单独测试每个舵机"""
    print("\n" + "="*50)
    print("🔧 单独测试每个舵机 (物理 0°~30° 范围)")
    print("="*50)
    
    ears = EarController()
    
    if not ears.enabled:
        print("❌ 初始化失败")
        return
    
    # 测试左耳 (通道2)
    print("\n【测试左耳 - 通道2】")
    print("  0° -> 15° -> 30° -> 0°")
    for angle in [0, 15, 30, 0]:
        print(f"  角度: {angle}°")
        ears.servo0.angle = angle
        time.sleep(1)
    
    # 测试右耳 (通道1)
    print("\n【测试右耳 - 通道1】")
    print("  0° -> 15° -> 30° -> 0°")
    for angle in [0, 15, 30, 0]:
        print(f"  角度: {angle}°")
        ears.servo3.angle = angle
        time.sleep(1)
    
    print("\n✅ 单独测试完成！")


def interactive_test():
    """交互式测试"""
    print("\n" + "="*50)
    print("🎮 交互式测试模式")
    print("="*50)
    print("物理角度范围: 0° ~ 30°")
    print("\n命令:")
    print("  0-30   - 设置双耳物理角度")
    print("  l0-30  - 设置左耳物理角度")
    print("  r0-30  - 设置右耳物理角度")
    print("  n      - 归中 (neutral)")
    print("  h      - 开心 (happy)")
    print("  s      - 惊讶 (surprise)")
    print("  t      - 思考 (thinking)")
    print("  d      - 悲伤 (sad)")
    print("  q      - 退出")
    print("="*50)
    
    ears = EarController()
    
    if not ears.enabled:
        print("❌ 初始化失败")
        return
    
    while True:
        try:
            cmd = input("\n输入命令: ").strip().lower()
            
            if cmd == 'q':
                print("退出测试...")
                ears._animate("neutral")
                break
            elif cmd == 'n':
                ears.update_emotion("neutral")
            elif cmd == 'h':
                ears.update_emotion("happy")
            elif cmd == 's':
                ears.update_emotion("surprise")
            elif cmd == 't':
                ears.update_emotion("thinking")
            elif cmd == 'd':
                ears.update_emotion("sad")
            elif cmd.startswith('l'):
                angle = int(cmd[1:])
                angle = max(0, min(30, angle))
                ears.servo0.angle = angle
                print(f"  左耳: {angle}°")
            elif cmd.startswith('r'):
                angle = int(cmd[1:])
                angle = max(0, min(30, angle))
                ears.servo3.angle = angle
                print(f"  右耳: {angle}°")
            elif cmd.isdigit():
                angle = int(cmd)
                angle = max(0, min(30, angle))
                ears.servo0.angle = angle
                ears.servo3.angle = angle
                print(f"  双耳: {angle}°")
            else:
                print("  未知命令")
                
        except ValueError:
            print("  无效输入")
        except KeyboardInterrupt:
            print("\n退出...")
            ears._animate("neutral")
            break


def main():
    """主菜单"""
    print("\n" + "="*50)
    print("🐰 耳朵舵机测试工具 (物理 0°~30° 版本)")
    print("="*50)
    print("\n请选择测试模式:")
    print("  1. 基本运动测试 (推荐)")
    print("  2. 情感动作测试")
    print("  3. 单独舵机测试")
    print("  4. 交互式测试")
    print("  5. 全部测试")
    print("  q. 退出")
    
    choice = input("\n输入选项 (1-5/q): ").strip()
    
    if choice == '1':
        test_basic_movement()
    elif choice == '2':
        test_emotion_actions()
    elif choice == '3':
        test_single_servo()
    elif choice == '4':
        interactive_test()
    elif choice == '5':
        test_basic_movement()
        test_emotion_actions()
        test_single_servo()
    elif choice == 'q':
        print("再见！")
    else:
        print("无效选项")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n测试被中断")
        sys.exit(0)
