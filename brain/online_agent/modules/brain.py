import sys
import os
import json
from openai import OpenAI

# === 关键步骤：把根目录加入到 Python 的搜索路径中 ===
# 1. 获取当前文件 (brain.py) 的绝对路径
current_dir = os.path.dirname(os.path.abspath(__file__))
# 2. 获取上一级目录 (即 online_agent 根目录)
root_dir = os.path.dirname(current_dir)
# 3. 把根目录加入系统路径
sys.path.append(root_dir)

# === 现在可以安全地导入 config 了 ===
try:
    import config
except ImportError:
    print("错误：找不到 config.py，请确保它在项目根目录下。")
    sys.exit(1)

# 初始化客户端
client = OpenAI(
    api_key=config.API_KEY, 
    base_url=config.BASE_URL
)

# === 系统提示词 (System Prompt) ===
# 这里的定义决定了小车够不够“聪明”，能不能稳定输出 JSON
SYSTEM_PROMPT = """
你是一个具身智能陪伴机器人。你拥有电机控制权限和视觉能力,你的底盘可以左右旋转 270 度。
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

def chat_with_brain(user_text):
    print(f"   [LLM] 正在思考: {user_text} ...")
    
    try:
        response = client.chat.completions.create(
            model="deepseek-chat", # DeepSeek V3/V2.5
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_text},
            ],
            temperature=0.1, # 低温度保证指令格式稳定
            stream=False
        )
        
        content = response.choices[0].message.content
        
        # 清理一下可能的 Markdown 标记 (DeepSeek 有时会比较啰嗦加上 ```json)
        content = content.replace("```json", "").replace("```", "").strip()
        
        return json.loads(content) # 解析为字典
        
    except json.JSONDecodeError:
        print("   [Error] LLM 返回的不是标准 JSON")
        return None
    except Exception as e:
        print(f"   [Error] 调用出错: {e}")
        return None

# 单独运行这个文件测试一下 Key 是否好用
if __name__ == "__main__":
    test_cmd = "向右转，速度快点"
    print(f"发送测试指令: {test_cmd}")
    res = chat_with_brain(test_cmd)
    print("API 返回结果:", res)
