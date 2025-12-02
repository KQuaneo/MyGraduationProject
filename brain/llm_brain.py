import json
from openai import OpenAI

# === 配置区域 ===
# 填入你刚才提供的 Key
API_KEY = "sk-6803a2dd4c1249b98eb42599bd61b0d4" 
# DeepSeek 的官方 API 地址
BASE_URL = "https://api.deepseek.com"

# 初始化客户端
client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

# === 系统提示词 (System Prompt) ===
# 这里的定义决定了小车够不够“聪明”，能不能稳定输出 JSON
SYSTEM_PROMPT = """
你是一个具身智能小车。你拥有电机控制权限。
用户会用自然语言给你指令，你需要理解意图并输出 JSON 格式的控制代码。

【重要规则】
1. 你必须严格只返回 JSON 格式，不要包含 ```json 或其他 Markdown 标记。
2. JSON 格式必须包含以下字段：
   - "action": 字符串，可选值: "move_forward", "move_backward", "turn_left", "turn_right", "stop", "dance" (跳舞/高兴)
   - "speed": 整数，范围 0-100
   - "reply": 字符串，你用简短、可爱的语气回复用户的语音内容 (20字以内)

【示例】
用户："有点黑，往前走一点看看"
返回：{"action": "move_forward", "speed": 40, "reply": "好的，小心翼翼往前走"}

用户："停下来！"
返回：{"action": "stop", "speed": 0, "reply": "急刹车！"}
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