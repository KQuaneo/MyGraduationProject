import os
import sys
import json
import pyaudio
import threading
import time
import array 
from vosk import Model, KaldiRecognizer

# === 1. 引入配置文件 ===
try:
    import config
except ImportError:
    print("错误：找不到 config.py")
    sys.exit(1)

# === 2. 引入功能模块 ===
try:
    from modules.brain import chat_with_brain
    from modules.mouth import speak
    # 引入视觉模块 (VisionSystem 稍后初始化)
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

# === 4. [新增] 引入耳朵控制模块 ===
try:
    from modules.ears import EarController
except ImportError as e:
    print(f"⚠️ 耳朵模块加载失败 (将跳过耳朵控制): {e}")
    EarController = None


# ==========================================
#  后台逻辑线程：负责 听觉 -> 视觉距离感知 -> 思考 -> 说话 -> 肢体
# ==========================================
def audio_logic_thread(eye_display): 
    print("🎧 语音/逻辑线程已启动...")
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    model_path = os.path.join(current_dir, "model")

    if not os.path.exists(model_path):
        print(f"错误：找不到模型文件夹 -> {model_path}")
        return

    # 变量初始化
    stream = None
    p = None
    vision_system = None
    ear_controller = None  # 耳朵控制器对象
    
    # 状态标志位
    is_interacting = False      # 是否正在对话/思考/说话 (如果是，则暂停闲时表情控制)
    last_vision_emotion = ""    # 记录上一次视觉触发的表情，防止重复刷新UI
    
    try:
        # === 0. [新增] 初始化耳朵 ===
        if EarController:
            print("🐰 正在初始化耳朵舵机...")
            try:
                ear_controller = EarController()
            except Exception as e:
                print(f"⚠️ 耳朵初始化出错: {e}")
                ear_controller = None

        # === 1. 初始化音频 (PyAudio) ===
        # 必须先于摄像头启动，防止底层资源冲突 (ALSA vs Libcamera)
        print("🎙️ 正在初始化麦克风...")
        p = pyaudio.PyAudio()
        
        # 智能麦克风寻找逻辑
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

        # === 2. 避让冲突 (关键步骤) ===
        print("⏳ 等待音频驱动稳定 (2秒)...")
        time.sleep(2) 

        # === 3. 初始化视觉 (Vision) ===
        print("👁️ 正在启动视觉系统...")
        try:
            vision_system = VisionSystem()
            print("✅ 视觉系统挂载成功！(YOLO 距离感知运行中)")
        except Exception as e:
            print(f"⚠️ 视觉启动失败 (不影响语音): {e}")

        # 加载 Vosk 语音模型
        print("📚 加载语音识别模型...")
        model = Model(model_path)
        rec = KaldiRecognizer(model, config.SAMPLE_RATE)
        
        print("\n=== ✨ 具身智能小车已就绪 (主动感知模式) ✨ ===\n")
        
        # === 进入主循环 ===
        while True:
            # 检查 GUI 是否被用户关闭
            if EYE_DISPLAY_ENABLED and eye_display and not eye_display.running:
                break

            # --- [A] 闲时视觉检测逻辑 (距离感知) ---
            # 只有在 "没在对话" 且 "视觉系统正常" 时运行
            if not is_interacting and vision_system and vision_system.running:
                # 读取 vision_module 计算好的人体面积占比 (0.0 ~ 1.0)
                area = vision_system.closest_person_area
                
                target_emotion = "neutral"
                
                # === 📏 距离判断阈值 ===
                if area > 0.35: 
                    # 面积超过 35% -> 贴脸了 -> 惊讶
                    target_emotion = "surprise" 
                elif area > 0.05: 
                    # 面积超过 5% -> 正常看到人 -> 开心
                    target_emotion = "happy"
                else:
                    # 面积太小或没人 -> 待机
                    target_emotion = "neutral"
                
                # 只有状态改变时才更新，避免画面闪烁和舵机抽搐
                if target_emotion != last_vision_emotion:
                    # 1. 更新屏幕
                    if eye_display: eye_display.update_emotion(target_emotion)
                    # 2. [新增] 更新耳朵动作
                    if ear_controller: ear_controller.update_emotion(target_emotion)
                    
                    last_vision_emotion = target_emotion
            # ---------------------------

            # --- [B] 读取音频 ---
            data = stream.read(8000, exception_on_overflow=False)
            
            # 声道转换 (如果麦克风是双声道的)
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
                    
                    # 1. 进入交互模式 (锁定表情控制权，防止闲时逻辑打断)
                    is_interacting = True 
                    stream.stop_stream() # 暂停听
                    
                    # 2. 思考状态
                    print("🤔 正在思考...")
                    if eye_display: eye_display.update_emotion("thinking") 
                    if ear_controller: ear_controller.update_emotion("thinking") # [新增] 耳朵动起来
                    
                    # 3. 大脑决策
                    command = chat_with_brain(text)
                    
                    if command:
                        action = command.get('action')
                        reply = command.get('reply')
                        emotion = command.get('emotion', 'neutral')
                        
                        print(f"🤖 决策: {action} | 回复: {reply} | 情绪: {emotion}")

                        # 4. 执行决策 (说话 + 表情 + 耳朵)
                        if eye_display: eye_display.update_emotion(emotion)
                        if ear_controller: ear_controller.update_emotion(emotion) # [新增] 耳朵做对应情绪
                        
                        speak(reply)

                        # 5. 特殊动作：Look (视觉问答)
                        if action == "look":
                            if vision_system:
                                if eye_display: eye_display.update_emotion("thinking")
                                print("📷 正在调用云端视觉...")
                                
                                # 使用更简练的提示词
                                vision_desc = vision_system.analyze_now(prompt="用中文一句话告诉我画面中最显眼的东西是什么，不要超过20个字。")
                                
                                print(f"👀 视觉反馈: {vision_desc}")
                                
                                # 看完后开心
                                if eye_display: eye_display.update_emotion("happy")
                                if ear_controller: ear_controller.update_emotion("happy") # [新增]
                                
                                speak(f"我看到了：{vision_desc}")
                            else:
                                speak("我的眼睛好像还没睁开。")

                        # 6. 特殊动作：运动控制 (预留)
                        elif action in ["move_forward", "turn_left", "stop"]:
                            # 这里可以调用你的电机控制函数
                            pass 
                        
                    # 7. 交互结束，恢复听觉，释放闲时检测锁
                    stream.start_stream()
                    is_interacting = False
                    # 重置状态，让下一轮循环重新判断距离
                    last_vision_emotion = "" 
                        
    except Exception as e:
        print(f"❌ 逻辑线程出错: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 清理资源
        if vision_system: 
            vision_system.running = False
        if stream: stream.stop_stream(); stream.close()
        if p: p.terminate()

# ==========================================
#  主线程：只负责 UI 渲染
# ==========================================
def main():
    # 1. 准备眼睛 UI
    eye_display = None
    if EYE_DISPLAY_ENABLED:
        eye_display = EyeDisplay()
        eye_display.running = True

    # 2. 启动逻辑线程 (把 eye_display 传进去控制)
    t = threading.Thread(target=audio_logic_thread, args=(eye_display,), daemon=True)
    t.start()

    # 3. 运行 GUI (主线程阻塞在这里)
    if eye_display:
        try:
            eye_display._run_loop(fullscreen=True) 
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