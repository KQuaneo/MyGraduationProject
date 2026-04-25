# Local Small-Model Experiment

This folder keeps the optional edge-model experiment for offline robot intent parsing. It is not used by the current production VTuber runtime.

## Goal

Train a small Qwen-style model to map constrained robot commands to compact JSON, then export a GGUF file for Raspberry Pi inference.

Production scope today:

- Main conversation, persona, vision, TTS and hardware orchestration stay in `Open-LLM-VTuber`.
- OpenClaw is only a live web-query layer and returns `{"p": "..."}`.
- This local model is a future extension for low-risk offline action-intent parsing.

## Files

- `train_robot.py`: Unsloth LoRA fine-tuning and GGUF export script.
- `run_inference.py`: local GGUF inference smoke test with `llama-cpp-python`.
- `data/robot_intent_examples.jsonl`: small demonstration dataset.
- `Modelfile`: optional Ollama import template for the exported GGUF.

## What Is Not Committed

The following are intentionally ignored because they are large or machine-specific:

- `.venv/`
- `outputs/`
- `*.gguf`
- downloaded base models
- llama.cpp build directories

## Training

```bash
cd experiments/local_model
uv venv --python 3.10
source .venv/bin/activate
uv pip install --upgrade pip
uv pip install "unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git"
uv pip install --no-deps "trl<0.9.0" peft accelerate bitsandbytes torchvision datasets
python train_robot.py --data data/robot_intent_examples.jsonl --max-steps 60
```

For a China mirror:

```bash
HF_HUB_ENABLE_HF_TRANSFER=0 HF_ENDPOINT=https://hf-mirror.com python train_robot.py
```

## Raspberry Pi Inference

```bash
cd experiments/local_model
uv pip install llama-cpp-python
python run_inference.py --model outputs/robot-intent-gguf/robot-intent.Q4_K_M.gguf "寻找苹果"
```

The exact exported filename depends on the GGUF export tool. Keep generated files outside git.
