#!/usr/bin/env python3
"""
robot_brain_listener.py - 机器人大脑监听器
在当前 Agent 会话中运行，监听机器人的输入并处理

改进版本：对于需要联网的查询，标记为需要外部处理
"""
import os
import sys
import json
import time
import re

# 添加项目路径以导入 config
sys.path.insert(0, '/home/raspberrypi/Desktop/MyGraduationProject/brain/online_agent')

# === 通信文件路径 ===
INPUT_FILE = "/tmp/robot_input.txt"
OUTPUT_FILE = "/tmp/robot_output.json"
NEED_HELP_FILE = "/tmp/robot_need_help.txt"  # 标记需要我处理的请求
LOCK_FILE = "/tmp/robot_brain.lock"

# === 系统提示词 ===
SYSTEM_PROMPT = """你是一个具身智能陪伴机器人。你拥有电机控制权限和视觉能力,你的底盘可以左右旋转 270 度。
用户会用自然语言给你指令，你需要理解意图并输出 JSON 格式的控制代码。

【重要规则】
1. 必须严格只返回 JSON 格式，不要有其他文字说明。
2. JSON 字段说明：
   - "action": 字符串。
     - 运动类: "shake"(摇头), "look_away"(扭头), "wiggle"(摆动), "scan"(扫描), "turn_away"(转身), "no"(拒绝动作), "turn_left", "turn_right"
     - 视觉类: "look" (当用户问"你看到了什么"、"这是什么"、"描述环境"时使用)
     - 其他: "none" (无动作)
   - "reply": 字符串。回复必须简短口语化，10字以内。
   - "emotion": 字符串 ("happy", "angry", "fear", "neutral", "sad", "surprise", "thinking")
   - "need_help": 布尔值 (true/false)。当用户询问需要实时信息的问题（如时间、天气、新闻）时设为 true

【示例】
用户："前面有什么？"
返回：{"action": "look", "reply": "让我看看", "emotion": "curious", "need_help": false}

用户："向左转"
返回：{"action": "turn_left", "reply": "左转啦", "emotion": "happy", "need_help": false}

用户："现在几点了"
返回：{"action": "none", "reply": "让我查一下", "emotion": "thinking", "need_help": true}
"""


def wait_for_file(filepath, timeout=None, check_interval=0.1):
    """等待文件出现"""
    start_time = time.time()
    while True:
        if os.path.exists(filepath):
            return True
        if timeout and time.time() - start_time > timeout:
            return False
        time.sleep(check_interval)


def read_and_delete_file(filepath):
    """读取文件内容并删除"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        os.remove(filepath)
        return content
    except Exception as e:
        print(f"[Listener] ⚠️ 读取文件失败: {e}")
        return None


def write_file(filepath, content):
    """写入文件"""
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    except Exception as e:
        print(f"[Listener] ⚠️ 写入文件失败: {e}")
        return False


def needs_external_help(user_text):
    """
    判断是否需要外部帮助（联网查询）
    """
    # 时间相关
    time_patterns = [
        r'现在几点', r'当前时间', r'.*时间.*', r'.*几点.*',
        r'伦敦.*时间', r'北京.*时间', r'纽约.*时间',
    ]
    
    # 天气相关
    weather_patterns = [
        r'.*天气.*', r'.*温度.*', r'.*下雨.*', r'.*下雪.*',
        r'.*晴天.*', r'.*阴天.*',
    ]
    
    # 新闻/实时信息
    news_patterns = [
        r'.*新闻.*', r'.*最新.*', r'.*今天.*发生.*',
    ]
    
    all_patterns = time_patterns + weather_patterns + news_patterns
    
    for pattern in all_patterns:
        if re.search(pattern, user_text):
            return True
    
    return False


def call_deepseek(user_text):
    """
    调用 DeepSeek API 获取回复
    """
    try:
        from openai import OpenAI
        import config
        
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
        
        # 清理可能的 Markdown 标记
        content = content.replace("```json", "").replace("```", "").strip()
        
        # 解析 JSON
        result = json.loads(content)
        
        # 确保必要字段
        if "action" not in result:
            result["action"] = "none"
        if "reply" not in result:
            result["reply"] = content[:50]
        if "emotion" not in result:
            result["emotion"] = "neutral"
        if "need_help" not in result:
            result["need_help"] = False
        
        return result
        
    except json.JSONDecodeError as e:
        print(f"[Listener] ⚠️ JSON 解析失败: {e}")
        return {
            "action": "none",
            "reply": "我在听",
            "emotion": "neutral",
            "need_help": False
        }
    except Exception as e:
        print(f"[Listener] ❌ API 调用失败: {e}")
        return {
            "action": "none",
            "reply": "我的大脑有点晕",
            "emotion": "sad",
            "need_help": False
        }


def process_input(user_text):
    """
    处理用户输入
    """
    print(f"[Listener] 🧠 处理: '{user_text}'")
    
    # 检查是否需要外部帮助
    if needs_external_help(user_text):
        print(f"[Listener] 🌐 需要联网查询")
        # 标记需要外部处理
        return {
            "action": "none",
            "reply": "让我查一下",
            "emotion": "thinking",
            "need_help": True,
            "original_query": user_text
        }
    
    # 调用 DeepSeek API
    response = call_deepseek(user_text)
    
    print(f"[Listener] ✅ 回复: {response}")
    return response


def main():
    print("=" * 50)
    print("🤖 机器人大脑监听器已启动")
    print("=" * 50)
    print(f"监听文件: {INPUT_FILE}")
    print(f"输出文件: {OUTPUT_FILE}")
    print(f"AI 模型: DeepSeek Chat")
    print("\n按 Ctrl+C 停止")
    print("=" * 50)
    
    # 清理旧文件
    for f in [INPUT_FILE, OUTPUT_FILE, NEED_HELP_FILE, LOCK_FILE]:
        if os.path.exists(f):
            try:
                os.remove(f)
                print(f"[Listener] 清理旧文件: {f}")
            except:
                pass
    
    print("[Listener] 开始监听...\n")
    
    try:
        while True:
            # 等待输入文件
            if wait_for_file(INPUT_FILE, timeout=None, check_interval=0.1):
                user_text = read_and_delete_file(INPUT_FILE)
                
                if user_text:
                    # 处理输入
                    response = process_input(user_text)
                    
                    # 如果需要外部帮助，写入标记文件
                    if response.get("need_help"):
                        write_file(NEED_HELP_FILE, json.dumps(response, ensure_ascii=False))
                        print(f"[Listener] 🌐 已标记需要外部帮助")
                    
                    # 写入输出文件
                    if write_file(OUTPUT_FILE, json.dumps(response, ensure_ascii=False)):
                        print(f"[Listener] ✅ 已写入回复\n")
                    else:
                        print("[Listener] ❌ 写入回复失败\n")
                
            time.sleep(0.05)
            
    except KeyboardInterrupt:
        print("\n[Listener] 👋 监听器已停止")
    except Exception as e:
        print(f"\n[Listener] ❌ 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
