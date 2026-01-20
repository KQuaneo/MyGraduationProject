import time
import board
from adafruit_pca9685 import PCA9685
from adafruit_motor import servo

i2c = board.I2C()
pca = PCA9685(i2c)
pca.frequency = 50

print("正在初始化...")
# 必须分别为两个通道创建对象
servo0 = servo.Servo(pca.channels[0], min_pulse=500, max_pulse=2500)
servo3 = servo.Servo(pca.channels[3], min_pulse=500, max_pulse=2500)

print("开始测试！")
while True:
    print("通道0 -> 0度,  通道3 -> 0度")
    servo0.angle = 0
    servo3.angle = 0
    time.sleep(1)
    
    print("通道0 -> 90度, 通道3 -> 90度")
    servo0.angle = 90
    servo3.angle = 90
    time.sleep(1)