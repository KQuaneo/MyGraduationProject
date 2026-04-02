"""
main_agent.py - 使用 OpenClaw Agent 作为主脑的机器人主程序

这是 main.py 的修改版本，使用 brain_agent 模块替代原来的 brain 模块
通过 HTTP API 与 OpenClaw Gateway 通信

使用方法:
1. 确保 OpenClaw Gateway 正在运行: openclaw gateway status
2. 激活虚拟环境: source online_agent/.venv/bin/activate  
3. 运行: python main_agent.py
"""
import os
import sys
import json
import pyaudio
import threading
import time
import array 
from vosk import Model, KaldiRecognizer
import re

# === 1. 引入配置文件 ===
try:
    import config
except ImportError:
    print("错误：找不到 config.py")
    sys.exit(1)

# === 2. 引入功能模块 ===
# ⚠️ 关键修改：使用 brain_agent 替代 brain
try:
    from modules.brain_agent import chat_with_brain  # 使用 Agent 模式
    from modules.mouth import speak
    from modules.yolov8_qwen import VisionSystem 
except ImportError as e:
    print(f"导入核心模块失败: {e}")
    sys.exit(1)

# === 3. 引入眼睛显示模块 ===
try:
    from modules.emotion_animation_display import EyeDisplay
    EYE_DISPLAY_ENABLED = True
except ImportError as e:
    print(f"⚠️ 眼睛显示模块加载失败: {e}")
    EYE_DISPLAY_ENABLED = False

# === 4. 引入耳朵控制模块 ===
try:
    from modules.ears import EarController
except ImportError as e:
    print(f"⚠️ 耳朵模块加载失败: {e}")
    EarController = None

# === 5. 引入底盘控制模块 ===
try:
    from modules.chassis import ChassisController
except ImportError as e:
    print(f"⚠️ 底盘模块加载失败: {e}")
    ChassisController = None


# ==========================================
#  后台逻辑线程
# ==========================================
def audio_logic_thread(eye_display): 
    print("🎧 语音/逻辑线程已启动...")
    print("🧠 模式: OpenClaw Agent 主脑")
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    model_path = os.path.join(current_dir, "model")

    if not os.path.exists(model_path):
        print(f"错误：找不到模型文件夹 -> {model_path}")
        return

    # 变量初始化
    stream = None
    p = None
    vision_system = None
    ear_controller = None
    chassis_controller = None
    
    # 状态标志位
    is_interacting = False
    last_vision_emotion = ""
    
    # 唤醒词相关状态
    is_awake = False
    AWAKE_TIMEOUT = 15
    last_awake_time = 0
    
    # 唤醒词列表
    WAKE_WORDS = ["小灰", "小辉", "小慧", "小惠", "晓灰", "晓辉"]
    
    def check_wake_word(text):
        """检查是否包含唤醒词"""
        text = text.lower().replace(" ", "")
        for word in WAKE_WORDS:
            if word in text:
                return True
        return False
    
    try:
        # === 0. 初始化耳朵 ===
        if EarController:
            print("🐰 正在初始化耳朵舵机...")
            try:
                ear_controller = EarController()
            except Exception as e:
                print(f"⚠️ 耳朵初始化出错: {e}")
                ear_controller = None

        # === 初始化底盘 ===
        if ChassisController:
            print("🛹 正在初始化底盘舵机 (PCA9685)...")
            try:
                chassis_controller = ChassisController(channel_index=0)
            except Exception as e:
                print(f"⚠️ 底盘初始化失败: {e}")
                chassis_controller = None

        # === 1. 初始化音频 ===
        print("🎙️ 正在初始化麦克风...")
        p = pyaudio.PyAudio()
        
        target_mic_id = config.MIC_ID
        input_channels = 1
        
        try:
            dev_info = p.get_device_info_by_index(config.MIC_ID)
            hw_channels = int(dev_info['maxInputChannels'])
            input_channels = hw_channels if hw_channels >= 2 else 1
            print(f"🎤 使用配置麦克风 ID: {config.MIC_ID}")
        except Exception:
            try:
                default_info = p.get_default_input_device_info()
                target_mic_id = default_info['index']
                hw_channels = int(default_info['maxInputChannels'])
                input_channels = hw_channels if hw_channels >= 2 else 1
                print(f"🎤 切换到默认麦克风 ID: {target_mic_id}")
            except Exception:
                print("❌ 致命错误：找不到任何麦克风！")
                return

        stream = p.open(
            format=pyaudio.paInt16,
            channels=input_channels,
            rate=config.SAMPLE_RATE,
            input=True,
            frames_per_buffer=8000,
            input_device_index=target_mic_id
        )
        stream.start_stream()
        print("✅ 音频系统就绪！")

        # === 2. 避让冲突 ===
        print("⏳ 等待音频驱动稳定 (2秒)...")
        time.sleep(2) 

        # === 3. 初始化视觉 ===
        print("👁️ 正在启动视觉系统...")
        try:
            vision_system = VisionSystem()
            print("✅ 视觉系统挂载成功！")
        except Exception as e:
            print(f"⚠️ 视觉启动失败: {e}")

        # 加载 Vosk 语音模型
        print("📚 加载语音识别模型...")
        model = Model(model_path)
        rec = KaldiRecognizer(model, config.SAMPLE_RATE)
        
        print("\n" + "="*50)
        print("✨ 具身智能小车已就绪 (Agent 模式) ✨")
        print("💤 睡眠模式：呼叫'小灰小灰'唤醒我")
        print("="*50 + "\n")
        
        # === 进入主循环 ===
        while True:
            if EYE_DISPLAY_ENABLED and eye_display and not eye_display.running:
                break

            # --- [A] 闲时视觉检测逻辑 ---
            if not is_interacting and vision_system and vision_system.running:
                center_x = getattr(vision_system, 'closest_person_center_x', None)
                
                if chassis_controller:
                    chassis_controller.update_vision_data(center_x)

                area = vision_system.closest_person_area
                target_emotion = "neutral"
                
                if area > 0.35: 
                    target_emotion = "surprise" 
                elif area > 0.05: 
                    target_emotion = "happy"
                else:
                    target_emotion = "neutral"
                
                if target_emotion != last_vision_emotion:
                    if eye_display: eye_display.update_emotion(target_emotion)
                    if ear_controller: ear_controller.update_emotion(target_emotion)
                    last_vision_emotion = target_emotion

            # --- [B] 读取音频 ---
            data = stream.read(8000, exception_on_overflow=False)
            
            if input_channels > 1:
                shorts = array.array('h', data)
                mono_shorts = shorts[::input_channels]
                data = mono_shorts.tobytes()

            # --- [C] 语音识别命中 ---
            if rec.AcceptWaveform(data):
                result = json.loads(rec.Result())
                text = result.get("text", "").replace(" ", "")
                
                if len(text) > 1:
                    print(f"\n👂 听到: {text}")
                    
                    # === 唤醒词检测逻辑 ===
                    if not is_awake:
                        if check_wake_word(text):
                            print("🔔 唤醒词检测成功！")
                            is_awake = True
                            last_awake_time = time.time()
                            
                            if eye_display: eye_display.update_emotion("happy")
                            if ear_controller: ear_controller.update_emotion("happy")
                            speak("我在")
                            print("💬 回复：我在")
                            print("🎤 唤醒成功，开始监听指令...")
                        else:
                            print(f"💤 睡眠中，忽略非唤醒词")
                        continue
                    
                    # === 已唤醒状态 ===
                    if time.time() - last_awake_time > AWAKE_TIMEOUT:
                        print("⏰ 唤醒超时，进入睡眠模式...")
                        is_awake = False
                        if eye_display: eye_display.update_emotion("neutral")
                        if ear_controller: ear_controller.update_emotion("neutral")
                        continue
                    
                    last_awake_time = time.time()
                    
                    # 1. 进入交互模式
                    is_interacting = True 
                    stream.stop_stream()
                    
                    # 2. 思考状态
                    print("🤔 正在思考...")
                    if eye_display: eye_display.update_emotion("thinking") 
                    if ear_controller: ear_controller.update_emotion("thinking")
                    
                    # 3. 大脑决策 - 使用 Agent 模式！
                    command = chat_with_brain(text)
                    
                    if command:
                        action = command.get('action', 'none')
                        reply = command.get('reply', '我在')
                        emotion = command.get('emotion', 'neutral')
                        
                        print(f"🤖 决策: {action} | 回复: {reply} | 情绪: {emotion}")

                        # 4. 激活身体动作
                        if chassis_controller and action and action not in ["none", "look"]:
                            chassis_controller.add_action(action)

                        # 5. 执行表情 & 耳朵
                        if eye_display: eye_display.update_emotion(emotion)
                        if ear_controller: ear_controller.update_emotion(emotion)
                        
                        # 6. 开口说话
                        speak(reply)

                        # 7. 特殊动作：Look (视觉问答)
                        if action == "look":
                            if vision_system:
                                if chassis_controller:
                                    center_x = getattr(vision_system, 'closest_person_center_x', 0)
                                    if center_x is not None:
                                        chassis_controller.update_vision_data(center_x)
                                    else:
                                        chassis_controller.update_vision_data(0)
                                    time.sleep(0.5)

                                if eye_display: eye_display.update_emotion("thinking")
                                if ear_controller: ear_controller.update_emotion("thinking")
                                
                                print(f"📷 正在调用云端视觉...")

                                if len(text) < 4 or text in ["看看", "看一眼", "前面是什么", "描述一下"]:
                                    dynamic_prompt = "请用中文简短描述一下你看到的画面，重点关注最显眼的物体。"
                                    print("👀 模式：通用描述")
                                else:
                                    dynamic_prompt = f"请根据画面回答用户的问题：{text}？请用中文简短回答。"
                                    print(f"👀 模式：精准问答 (问题: {text})")

                                vision_desc = vision_system.analyze_now(prompt=dynamic_prompt)
                                print(f"👀 视觉反馈: {vision_desc}")
                                
                                if eye_display: eye_display.update_emotion("happy")
                                if ear_controller: ear_controller.update_emotion("happy")
                                
                                speak(vision_desc)
                            else:
                                speak("我的眼睛好像还没睁开。")
                        
                    # 8. 交互结束，恢复听觉
                    try:
                        stream.start_stream()
                    except OSError as e:
                        print(f"⚠️ 麦克风连接中断: {e}")
                        print("🔄 正在尝试重建音频流...")
                        try:
                            stream.close()
                            stream = p.open(
                                format=pyaudio.paInt16,
                                channels=input_channels,
                                rate=config.SAMPLE_RATE,
                                input=True,
                                frames_per_buffer=8000,
                                input_device_index=target_mic_id
                            )
                            stream.start_stream()
                            print("✅ 麦克风重连成功！")
                        except Exception as e2:
                            print(f"❌ 无法恢复麦克风: {e2}")
                            break

                    is_interacting = False
                    
                    if chassis_controller and vision_system:
                        center_x = getattr(vision_system, 'closest_person_center_x', None)
                        chassis_controller.update_vision_data(center_x)
                        print("🔄 底盘追踪已恢复。")
                        
                    last_vision_emotion = ""
                        
    except Exception as e:
        print(f"❌ 逻辑线程出错: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if vision_system: 
            vision_system.running = False
        if stream: stream.stop_stream(); stream.close()
        if p: p.terminate()
        
        if chassis_controller:
            try:
                chassis_controller.stop()
            except Exception as e:
                print(f"⚠️ 停止底盘时出错: {e}")
        
        if ear_controller:
            try:
                ear_controller.stop()
            except Exception as e:
                print(f"⚠️ 停止耳朵时出错: {e}")
        
        try:
            from modules.pca9685_manager import PCA9685Manager
            PCA9685Manager.deinit()
        except Exception as e:
            print(f"⚠️ PCA9685 释放时出错: {e}")


# ==========================================
#  主线程
# ==========================================
def main():
    # 1. 准备眼睛 UI
    eye_display = None
    if EYE_DISPLAY_ENABLED:
        eye_display = EyeDisplay()
        eye_display.running = True

    # 2. 启动逻辑线程
    t = threading.Thread(target=audio_logic_thread, args=(eye_display,), daemon=True)
    t.start()

    # 3. 运行 GUI
    if eye_display:
        try:
            eye_display._run_loop(fullscreen=config.EYE_FULLSCREEN) 
        except KeyboardInterrupt:
            pass
        finally:
            eye_display.running = False
    else:
        try:
            while True: time.sleep(1)
        except KeyboardInterrupt:
            pass

if __name__ == "__main__":
    main()
