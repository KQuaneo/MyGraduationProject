import time
import sys
import signal

# 确保能找到 modules 文件夹
sys.path.append(".") 

try:
    from modules.yolov8_qwen import VisionSystem
    from modules.chassis import ChassisController
except ImportError as e:
    print(f"❌ 导入模块失败: {e}")
    sys.exit(1)

def signal_handler(sig, frame):
    print("\n🛑 程序已停止")
    sys.exit(0)

def test_tracking_loop():
    # === 1. 初始化视觉系统 ===
    print("👁️ 正在启动视觉系统 (YOLO)...")
    # VisionSystem 会自动启动后台线程运行 YOLO
    vision = VisionSystem()
    
    # 给一点时间让摄像头预热
    time.sleep(2)

    # === 2. 初始化底盘系统 ===
    print("🛹 正在启动底盘系统...")
    try:
        # ⚠️ 如果你的舵机插在其他通道，请修改 channel_index
        chassis = ChassisController(channel_index=0)
    except Exception as e:
        print(f"❌ 底盘启动失败: {e}")
        return

    print("\n=== ✨ 追踪测试开始 ✨ ===")
    print("按 Ctrl+C 退出程序")
    print("------------------------------------------------")
    print(f"{'视觉误差 (X)':<15} | {'当前角度':<15} | {'状态'}")

    # 捕获 Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)

    while True:
        # 1. 获取视觉数据 (-1.0 ~ 1.0)
        # 注意：这里需要你的 VisionSystem 已经按照之前修改过，有这个变量
        error_x = getattr(vision, 'closest_person_center_x', None)
        
        # 2. 传递给底盘
        chassis.update_vision_data(error_x)
        
        # 3. 打印调试信息
        current_angle = chassis.current_toy_angle
        
        if error_x is not None:
            # 有人，显示误差方向
            direction = "<< 左" if error_x < -0.1 else ("右 >>" if error_x > 0.1 else "OK")
            print(f"{error_x: .4f}          | {current_angle: .2f}°        | 🟢 锁定 {direction}")
        else:
            # 没人
            print(f"{'---':<15} | {current_angle: .2f}°        | ⚪ 搜索中...")
        
        # 4. 控制刷新率 (不要太快，视觉帧率通常 30fps)
        time.sleep(0.05)

if __name__ == "__main__":
    test_tracking_loop()