# Local Small-Model Experiment / 本地小模型实验

本目录保留边缘端小模型实验，用于未来离线机器人意图解析。它不参与当前生产版 VTuber 主流程。

This folder keeps the optional edge-model experiment for offline robot intent parsing. It is not used by the current production VTuber runtime.

## Goal / 目标

中文目标：训练一个小型 Qwen 风格模型，将受限机器人命令映射为紧凑 JSON，并导出 GGUF 文件用于 Raspberry Pi 推理。

English goal: train a small Qwen-style model to map constrained robot commands to compact JSON, then export a GGUF file for Raspberry Pi inference.

当前生产边界：

Production scope today:

- 主对话、人设、视觉、TTS 和硬件调度都留在 `Open-LLM-VTuber`。
- Main conversation, persona, vision, TTS and hardware orchestration stay in `Open-LLM-VTuber`.
- OpenClaw 只是联网查询层，返回 `{"p": "..."}`。
- OpenClaw is only a live web-query layer and returns `{"p": "..."}`.
- 本地小模型是未来扩展，用于低风险离线动作意图解析。
- This local model is a future extension for low-risk offline action-intent parsing.

## Files / 文件

- `train_robot.py`: Unsloth LoRA 微调和 GGUF 导出脚本。
- `train_robot.py`: Unsloth LoRA fine-tuning and GGUF export script.
- `run_inference.py`: 基于 `llama-cpp-python` 的本地 GGUF 推理冒烟测试。
- `run_inference.py`: local GGUF inference smoke test with `llama-cpp-python`.
- `data/robot_intent_examples.jsonl`: 小型演示数据集。
- `data/robot_intent_examples.jsonl`: small demonstration dataset.
- `Modelfile`: 导出 GGUF 后可选的 Ollama 导入模板。
- `Modelfile`: optional Ollama import template for the exported GGUF.

## What Is Not Committed / 不提交内容

以下内容体积较大或依赖本机环境，因此被忽略：

The following are intentionally ignored because they are large or machine-specific:

- `.venv/`
- `outputs/`
- `*.gguf`
- downloaded base models
- llama.cpp build directories

## Training / 训练

```bash
cd experiments/local_model
uv venv --python 3.10
source .venv/bin/activate
uv pip install --upgrade pip
uv pip install "unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git"
uv pip install --no-deps "trl<0.9.0" peft accelerate bitsandbytes torchvision datasets
python train_robot.py --data data/robot_intent_examples.jsonl --max-steps 60
```

国内镜像示例：

China mirror example:

```bash
HF_HUB_ENABLE_HF_TRANSFER=0 HF_ENDPOINT=https://hf-mirror.com python train_robot.py
```

## Raspberry Pi Inference / 树莓派推理

```bash
cd experiments/local_model
uv pip install llama-cpp-python
python run_inference.py --model outputs/robot-intent-gguf/robot-intent.Q4_K_M.gguf "寻找苹果"
```

导出的具体文件名取决于 GGUF 导出工具，生成文件应保留在 Git 之外。

The exact exported filename depends on the GGUF export tool. Keep generated files outside git.
