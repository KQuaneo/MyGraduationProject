"""
brain_agent.py - OpenClaw Agent 连接模块
通过文件通信方式与当前运行的 Agent 会话交互

工作原理:
1. 机器人将用户语音写入 /tmp/robot_input.txt
2. 当前 Agent 会话读取并处理
3. Agent 将回复写入 /tmp/robot_output.json
4. 机器人读取回复并执行

使用方法：
在 main.py 中导入: from modules.brain_agent import chat_with_brain
"""
import sys
import os
import json
import time
import threading

# === 路径设置 ===
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
sys.path.append(root_dir)

# === 通信文件路径 ===
INPUT_FILE = "/tmp/robot_input.txt"
OUTPUT_FILE = "/tmp/robot_output.json"
LOCK_FILE = "/tmp/robot_brain.lock"

# === 系统提示词（当使用备选方案时）===
SYSTEM_PROMPT = """你是一个具身智能陪伴机器人。你拥有电机控制权限和视觉能力,你的底盘可以左右旋转 270 度。
用户会用自然语言给你指令，你需要理解意图并输出 JSON 格式的控制代码。

【重要规则】
1. 必须严格只返回 JSON 格式。
2. JSON 字段说明：
   - "action": 字符串。
     - 运动类: "shake", "look_away", "wiggle", "scan", "turn_away", "no"
     - 视觉类: "look" (当用户问"你看到了什么"、"这是什么"、"描述环境"时使用)
   - "reply": 字符串。回复必须简短口语化(10字内)。
     - 如果 action 是 "look"，reply 请回答 "让我看看" 或 "好的，我看一下"。
   - "emotion": 字符串 ("happy", "angry", "fear", "neutral", "sad", "surprise", "thinking")

【示例】
用户："前面有什么？"
返回：{"action": "look", "reply": "让我仔细看看", "emotion": "curious"}

用户："向左转"
返回：{"action": "turn_left", "reply": "左转啦", "emotion": "happy"}
"""


def _wait_for_file(filepath, timeout=30, check_interval=0.1):
    """等待文件出现"""
    start_time = time.time()
    while time.time() - start_time < timeout:
        if os.path.exists(filepath):
            return True
        time.sleep(check_interval)
    return False


def _read_and_delete_file(filepath):
    """读取文件内容并删除"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        os.remove(filepath)
        return content
    except Exception as e:
        print(f"[BrainAgent] ⚠️ 读取文件失败: {e}")
        return None


def _write_file(filepath, content):
    """写入文件"""
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    except Exception as e:
        print(f"[BrainAgent] ⚠️ 写入文件失败: {e}")
        return False


def _acquire_lock(timeout=5):
    """获取锁"""
    start_time = time.time()
    while time.time() - start_time < timeout:
        if not os.path.exists(LOCK_FILE):
            try:
                with open(LOCK_FILE, 'w') as f:
                    f.write(str(os.getpid()))
                return True
            except:
                pass
        time.sleep(0.05)
    return False


def _release_lock():
    """释放锁"""
    try:
        if os.path.exists(LOCK_FILE):
            os.remove(LOCK_FILE)
    except:
        pass


def _send_via_file_communication(user_text):
    """
    通过文件通信发送消息到 Agent
    
    协议:
    1. 写入 INPUT_FILE
    2. 等待 OUTPUT_FILE 出现
    3. 读取并删除 OUTPUT_FILE
    4. 返回结果
    """
    # 清理旧文件
    for f in [INPUT_FILE, OUTPUT_FILE]:
        if os.path.exists(f):
            try:
                os.remove(f)
            except:
                pass
    
    # 获取锁
    if not _acquire_lock():
        print("[BrainAgent] ⚠️ 无法获取锁")
        return None
    
    try:
        # 写入输入文件
        if not _write_file(INPUT_FILE, user_text):
            return None
        
        print(f"[BrainAgent] 📤 已写入输入文件，等待响应...")
        
        # 等待输出文件
        if _wait_for_file(OUTPUT_FILE, timeout=30):
            content = _read_and_delete_file(OUTPUT_FILE)
            if content:
                try:
                    return json.loads(content)
                except json.JSONDecodeError:
                    print(f"[BrainAgent] ⚠️ 输出文件不是有效 JSON")
                    return None
        else:
            print("[BrainAgent] ⚠️ 等待响应超时")
            return None
            
    finally:
        _release_lock()
        # 清理输入文件
        if os.path.exists(INPUT_FILE):
            try:
                os.remove(INPUT_FILE)
            except:
                pass


def _fallback_llm_call(user_text):
    """
    备选方案：直接调用配置好的 LLM API
    """
    try:
        import config
        from openai import OpenAI
        
        client = OpenAI(
            api_key=config.API_KEY,
            base_url=config.BASE_URL
        )
        
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_text}
            ],
            temperature=0.1,
            stream=False
        )
        
        content = response.choices[0].message.content
        content = content.replace("```json", "").replace("```", "").strip()
        
        result = json.loads(content)
        
        if "action" not in result:
            result["action"] = "none"
        if "reply" not in result:
            result["reply"] = content[:50]
        if "emotion" not in result:
            result["emotion"] = "neutral"
        
        return result
        
    except Exception as e:
        print(f"[BrainAgent] ❌ 备选方案失败: {e}")
        return {
            "action": "none",
            "reply": "我的大脑连接有点问题",
            "emotion": "sad"
        }


# === 主接口（供 main.py 调用）===
def chat_with_brain(user_text):
    """
    主函数：同步接口，供 main.py 调用
    
    参数:
        user_text: 用户的语音输入文本
        
    返回格式: 
        {"action": str, "reply": str, "emotion": str}
    """
    print(f"[BrainAgent] 🧠 处理: '{user_text}'")
    
    try:
        # 尝试文件通信
        response = _send_via_file_communication(user_text)
        
        if response and isinstance(response, dict):
            # 确保必要字段
            if "action" not in response:
                response["action"] = "none"
            if "reply" not in response:
                response["reply"] = "我在"
            if "emotion" not in response:
                response["emotion"] = "neutral"
            
            print(f"[BrainAgent] ✅ 结果: {response}")
            return response
        
        # 如果文件通信失败，使用备选方案
        print("[BrainAgent] ⚠️ 文件通信失败，使用备选方案")
        return _fallback_llm_call(user_text)
            
    except Exception as e:
        print(f"[BrainAgent] ❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return _fallback_llm_call(user_text)


# === 测试代码 ===
if __name__ == "__main__":
    print("=" * 50)
    print("BrainAgent 测试模式")
    print("=" * 50)
    print(f"输入文件: {INPUT_FILE}")
    print(f"输出文件: {OUTPUT_FILE}")
    print("\n注意: 此模式需要另一个 Agent 会话监听输入文件")
    print("=" * 50)
    
    test_inputs = [
        "你好呀",
        "向右转",
        "你看到了什么？"
    ]
    
    for test_text in test_inputs:
        print(f"\n{'='*40}")
        print(f"测试: {test_text}")
        print('='*40)
        result = chat_with_brain(test_text)
        print(f"\n结果:")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        time.sleep(1)
