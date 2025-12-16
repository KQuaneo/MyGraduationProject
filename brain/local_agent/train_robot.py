from unsloth import FastLanguageModel
import torch
from trl import SFTTrainer
from transformers import TrainingArguments
from datasets import Dataset

# ================= 1. 配置区域 =================
max_seq_length = 2048 # 上下文长度
dtype = None # None 表示自动检测 (通常是 Float16 或 Bfloat16)
load_in_4bit = True # 【关键】强制使用4bit量化，你的8G显存全靠它

# ================= 2. 加载模型 =================
print("正在加载 Qwen2.5-1.5B 模型...")
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name = "unsloth/Qwen2.5-1.5B-Instruct", 
    max_seq_length = max_seq_length,
    dtype = dtype,
    load_in_4bit = load_in_4bit,
)

# ================= 3. 给模型加上 LoRA 适配器 =================
# 这就像给大脑装了一个外挂芯片，我们只训练这个芯片，不改动原始大脑
model = FastLanguageModel.get_peft_model(
    model,
    r = 16, # 秩，数值越大越聪明但显存消耗越大，16对于简单指令足够
    target_modules = ["q_proj", "k_proj", "v_proj", "o_proj",
                      "gate_proj", "up_proj", "down_proj",],
    lora_alpha = 16,
    lora_dropout = 0, 
    bias = "none", 
    use_gradient_checkpointing = "unsloth", 
    random_state = 3407,
)

# ================= 4. 准备机器人训练数据 =================
# 这里为了演示，我们直接在代码里写数据。
# 实际项目中，你可以加载一个 json 文件。
print("正在构建数据集...")

alpaca_prompt = """Below is an instruction that describes a task, paired with an input that provides further context. Write a response that appropriately completes the request.

### Instruction:
{}

### Input:
{}

### Response:
{}"""

# 模拟一些机器人控制指令
# 这里的 Output 是严谨的 JSON 格式，方便树莓派解析
robot_data = [
    {
        "instruction": "把红色的方块拿到左边", 
        "input": "", 
        "output": "{\"action\": \"pick_and_place\", \"target\": \"red_block\", \"destination\": \"left_zone\"}"
    },
    {
        "instruction": "前方有障碍物吗？", 
        "input": "传感器数据: 前方距离 15cm", 
        "output": "{\"warning\": true, \"message\": \"Too close\", \"action\": \"stop\"}"
    },
    {
        "instruction": "向右旋转", 
        "input": "", 
        "output": "{\"action\": \"rotate\", \"direction\": \"right\", \"degree\": 90}"
    },
    {
        "instruction": "寻找苹果", 
        "input": "", 
        "output": "{\"action\": \"detect\", \"object\": \"apple\", \"mode\": \"scan\"}"
    },
    # 你可以复制这几行，多造一点数据，或者让它重复学习这几条
] * 10 # 乘以10，假装我们有很多数据（演示用）

def formatting_prompts_func(examples):
    instructions = examples["instruction"]
    inputs       = examples["input"]
    outputs      = examples["output"]
    texts = []
    for instruction, input, output in zip(instructions, inputs, outputs):
        text = alpaca_prompt.format(instruction, input, output) + tokenizer.eos_token
        texts.append(text)
    return { "text" : texts, }

dataset = Dataset.from_list(robot_data)
dataset = dataset.map(formatting_prompts_func, batched = True,)

# ================= 5. 开始训练 (炼丹) =================
print("开始训练...")
trainer = SFTTrainer(
    model = model,
    tokenizer = tokenizer,
    train_dataset = dataset,
    dataset_text_field = "text",
    max_seq_length = max_seq_length,
    dataset_num_proc = 2,
    packing = False, 
    args = TrainingArguments(
        per_device_train_batch_size = 2, # 批次大小，显存不够就改小
        gradient_accumulation_steps = 4,
        warmup_steps = 5,
        max_steps = 60, # 训练步数，演示只跑60步。实际要想变聪明，建议跑 300+
        learning_rate = 2e-4,
        fp16 = not torch.cuda.is_bf16_supported(),
        bf16 = torch.cuda.is_bf16_supported(),
        logging_steps = 10,
        optim = "adamw_8bit",
        weight_decay = 0.01,
        lr_scheduler_type = "linear",
        seed = 3407,
        output_dir = "outputs",
        report_to = "none", # 不上传wandb，只在本地看
    ),
)

trainer.train()

# ================= 6. 测试一下效果 =================
print("\n训练完成！测试推理效果...")
FastLanguageModel.for_inference(model) 

# 测试输入
test_instruction = "把红色的方块拿到左边"
inputs = tokenizer(
[
    alpaca_prompt.format(
        test_instruction, # instruction
        "", # input
        "", # output - leave this blank for generation!
    )
], return_tensors = "pt").to("cuda")

outputs = model.generate(**inputs, max_new_tokens = 64, use_cache = True)
result = tokenizer.batch_decode(outputs)
print(f"指令: {test_instruction}")
print(f"模型回答: {result[0].split('### Response:')[-1]}")

# ================= 7. 导出给树莓派 (GGUF) =================
print("\n正在导出为 GGUF 格式 (Int4 量化)...")
# q4_k_m 是最平衡的量化方法，体积小速度快，精度损失少
model.save_pretrained_gguf("model_pi_v1", tokenizer, quantization_method = "q4_k_m")
print("导出完成！请查看 model_pi_v1 文件夹。")