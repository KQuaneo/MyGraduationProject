from adafruit_servokit import ServoKit
import time

# 初始化 PCA9685，它有16个通道
kit = ServoKit(channels=16)

print("正在初始化舵机...")

# --- 关键设置 ---
# DS3120 的脉宽通常是 500us 到 2500us
# 如果你不设置这个，舵机可能只能转 90 度或者转动范围很小
# 通道 0 对应插在板子 '0' 位置的舵机
kit.servo[0].set_pulse_width_range(500, 2500)

# 设置你的舵机最大角度 (如果是270度版就写270，180度版写180)
# 这一步是为了让 kit.servo[0].angle = X 的时候，X 是真实的角度
kit.servo[0].actuation_range = 270

try:
    while True:
        print("归零 (0度)")
        kit.servo[0].angle = 0
        time.sleep(2)

        print("居中 (135度)")
        kit.servo[0].angle = 135
        time.sleep(2)

        print("最大 (270度)")
        kit.servo[0].angle = 270
        time.sleep(2)
        
        # 归中准备安装
        print("归中锁定，准备安装齿轮...")
        kit.servo[0].angle = 135
        time.sleep(5) # 给你5秒钟时间确认

except KeyboardInterrupt:
    # PCA9685没有像GPIO那样的cleanup，
    # 我们可以把舵机扭力释放（设为None），或者什么都不做
    kit.servo[0].angle = None 
    print("测试结束")