import pyaudio

p = pyaudio.PyAudio()

print("\n---------------------------------------------------")
print(f"检测到设备总数: {p.get_device_count()}")
print("正在扫描所有可用设备 (跳过损坏设备)...")
print("---------------------------------------------------")

found = False

# 遍历所有可能的设备 ID
for i in range(p.get_device_count()):
    try:
        # 尝试读取设备信息，如果读不到（比如设备损坏）就跳过，不让程序崩溃
        info = p.get_device_info_by_index(i)
        
        # 只显示【麦克风】（即输入通道 > 0 的设备）
        if info['maxInputChannels'] > 0:
            found = True
            print(f"✅ ID [{i}] : {info['name']}")
            print(f"     -> 最大输入通道: {info['maxInputChannels']}")
            print(f"     -> 默认采样率:   {int(info['defaultSampleRate'])} Hz")
            print("---------------------------------------------------")
            
    except Exception as e:
        # 遇到坏设备，静默跳过
        pass

if not found:
    print("❌ 警告：未检测到任何麦克风！")
    print("请检查：")
    print("1. USB 麦克风是否插好？")
    print("2. 尝试拔插一下麦克风")
    
p.terminate()