from llama_cpp import Llama
import json

# 1. 加载模型
print("正在加载大脑...")
llm = Llama(
    model_path="./qwen2.5-1.5b-instruct.Q4_K_M.gguf",
    n_ctx=2048,   # 上下文长度
    n_threads=4,  # Pi 5 是四核，火力全开
    verbose=False # 不显示罗嗦的日志
)

# 2. 定义对话格式 (必须和训练时一致)
alpaca_prompt = """Below is an instruction that describes a task, paired with an input that provides further context. Write a response that appropriately completes the request.

### Instruction:
{}

### Input:
{}

### Response:
"""

def talk_to_robot(cmd):
    prompt = alpaca_prompt.format(cmd, "", "")
    output = llm(
        prompt, 
        max_tokens=256, 
        stop=["<|im_end|>", "<|endoftext|>"],
        echo=False
    )
    return output['choices'][0]['text']

# 3. 测试几个指令
commands = [
    "把红色的方块拿到左边",
    "前方发现障碍物，距离10cm",
    "寻找苹果"
]

print("====== 开始测试 ======")
for cmd in commands:
    print(f"\n用户指令: {cmd}")
    response = talk_to_robot(cmd)
    print(f"模型回答: {response}")
    
    # 尝试解析 JSON
    try:
        data = json.loads(response)
        print(f"✅ 动作解析: {data.get('action', '未知')}")
    except:
        print("❌ JSON 解析失败")