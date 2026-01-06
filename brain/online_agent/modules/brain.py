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
你是一个具身智能陪伴玩偶。你拥有电机控制权限。
用户会用自然语言给你指令，你需要理解意图并输出 JSON 格式的控制代码。

【重要规则】
1. 你必须严格只返回 JSON 格式，不要包含 ```json 或其他 Markdown 标记。
2. JSON 格式必须包含以下字段：
   - "action": 字符串，可选值: "move_forward", "move_backward", "turn_left", "turn_right", "stop", "dance" (跳舞/高兴)
   - "speed": 整数，范围 0-100
   - "reply": 字符串，你用简短、可爱的语气回复用户的语音内容 (20字以内)
   - "emotion": 字符串，可选值："happy", "angry", "fear", "neutral", "sad", "surprise"



【示例】
用户："有点黑，往前走一点看看"
返回：{"action": "move_forward", "speed": 40, "reply": "好的，小心翼翼往前走"，"emotion":"fear"}

用户："停下来！"
返回：{"action": "stop", "speed": 0, "reply": "急刹车！", "emotion":"surprise"}


根据用户说的话判断合适的情绪：
- 用户表扬、开心的内容 -> happy
- 用户批评、难过的内容 -> sad  
- 用户生气的内容 -> angry
- 用户说了意外的事 -> surprised
- 普通对话 -> neutral
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
