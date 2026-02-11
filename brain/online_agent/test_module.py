import time
import sys

# 确保能找到 modules 文件夹
sys.path.append(".") 

try:
    from modules.chassis import ChassisController
except ImportError:
    print("找不到 modules.chassis，请确保你在项目根目录下运行此脚本")
    sys.exit(1)

def test_logic():
    print("🛹 正在初始化 ChassisController...")
    # 假设插在通道 0
    controller = ChassisController(channel_index=0)
    
    print("\n=== 测试 1: 基础角度测试 ===")
    angles = [0, -45, 45, -90, 90, 0]
    
    for angle in angles:
        print(f"👉 发送逻辑角度: {angle}°")
        # 直接调用内部函数来测试映射逻辑
        controller._set_physical_servo(angle)
        time.sleep(1.5)

    print("\n=== 测试 2: 模拟 LLM 动作指令 ===")
    actions = ["look_away", "shake", "scan"]
    for act in actions:
        print(f"🎬 执行动作: {act}")
        controller.add_action(act)
        # 等待动作执行完 (估算时间)
        time.sleep(4) 

    print("\n✅ 所有测试结束，程序即将退出")
    controller.running = False # 停止后台线程

if __name__ == "__main__":
    try:
        test_logic()
    except KeyboardInterrupt:
        print("\n强制停止")