import time
import sys

# 确保能找到 modules 文件夹
sys.path.append(".") 

try:
    from modules.chassis import ChassisController
except ImportError:
    print("❌ 找不到 modules.chassis，请确保在项目根目录下运行")
    sys.exit(1)

def test_calibration():
    print("🛹 正在初始化底盘 (ChassisController)...")
    # ⚠️ 如果你改了通道，记得这里也要改 (例如 channel_index=15)
    controller = ChassisController(channel_index=0)
    
    # === 第一步：归中测试 ===
    print("\n" + "="*40)
    print("1️⃣  【归中测试】发送逻辑角度 0°")
    print("👀 请观察：摄像头是否【正对前方】？")
    print("="*40)
    controller._set_physical_servo(0)
    time.sleep(5) # 给你5秒钟观察

    # === 第二步：左转测试 ===
    print("\n" + "="*40)
    print("2️⃣  【左转测试】发送逻辑角度 -90° (或你的最大左角)")
    print("👀 请观察：摄像头是否转到了【身体左侧】？")
    print("="*40)
    controller._set_physical_servo(-90)
    time.sleep(3)

    # === 第三步：右转测试 ===
    print("\n" + "="*40)
    print("3️⃣  【右转测试】发送逻辑角度 +90° (或你的最大右角)")
    print("👀 请观察：摄像头是否转到了【身体右侧】？")
    print("="*40)
    controller._set_physical_servo(90)
    time.sleep(3)

    # === 第四步：回中 ===
    print("\n✅ 测试结束，正在回中...")
    controller._set_physical_servo(0)
    controller.running = False # 停止后台线程

if __name__ == "__main__":
    try:
        test_calibration()
    except KeyboardInterrupt:
        print("\n🚫 强制停止")