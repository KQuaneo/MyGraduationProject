"""Fine-tune a small local model for robot action-intent JSON output.

This experiment is not part of the production VTuber runtime. It documents the
edge-model path explored for future offline intent parsing on Raspberry Pi.
Generated adapters, checkpoints and GGUF files are intentionally ignored.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import torch
from datasets import Dataset
from transformers import TrainingArguments
from trl import SFTTrainer
from unsloth import FastLanguageModel


ALPACA_PROMPT = """Below is an instruction that describes a robot-control task, paired with optional sensor context. Return only one compact JSON object.

### Instruction:
{}

### Input:
{}

### Response:
{}"""


def load_examples(path: Path, repeat: int) -> Dataset:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rows.append(json.loads(line))
    if not rows:
        raise ValueError(f"No training rows found in {path}")
    return Dataset.from_list(rows * repeat)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, default=Path("data/robot_intent_examples.jsonl"))
    parser.add_argument("--base-model", default="unsloth/Qwen2.5-1.5B-Instruct")
    parser.add_argument("--output-dir", default="outputs/robot-intent-lora")
    parser.add_argument("--gguf-dir", default="outputs/robot-intent-gguf")
    parser.add_argument("--max-steps", type=int, default=60)
    parser.add_argument("--repeat", type=int, default=10)
    args = parser.parse_args()

    max_seq_length = 2048
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=args.base_model,
        max_seq_length=max_seq_length,
        dtype=None,
        load_in_4bit=True,
    )

    model = FastLanguageModel.get_peft_model(
        model,
        r=16,
        target_modules=[
            "q_proj",
            "k_proj",
            "v_proj",
            "o_proj",
            "gate_proj",
            "up_proj",
            "down_proj",
        ],
        lora_alpha=16,
        lora_dropout=0,
        bias="none",
        use_gradient_checkpointing="unsloth",
        random_state=3407,
    )

    dataset = load_examples(args.data, args.repeat)

    def format_rows(examples):
        texts = []
        for instruction, input_text, output in zip(
            examples["instruction"], examples["input"], examples["output"]
        ):
            texts.append(
                ALPACA_PROMPT.format(instruction, input_text, output)
                + tokenizer.eos_token
            )
        return {"text": texts}

    dataset = dataset.map(format_rows, batched=True)

    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=dataset,
        dataset_text_field="text",
        max_seq_length=max_seq_length,
        dataset_num_proc=2,
        packing=False,
        args=TrainingArguments(
            per_device_train_batch_size=2,
            gradient_accumulation_steps=4,
            warmup_steps=5,
            max_steps=args.max_steps,
            learning_rate=2e-4,
            fp16=not torch.cuda.is_bf16_supported(),
            bf16=torch.cuda.is_bf16_supported(),
            logging_steps=10,
            optim="adamw_8bit",
            weight_decay=0.01,
            lr_scheduler_type="linear",
            seed=3407,
            output_dir=args.output_dir,
            report_to="none",
        ),
    )
    trainer.train()

    FastLanguageModel.for_inference(model)
    model.save_pretrained_gguf(args.gguf_dir, tokenizer, quantization_method="q4_k_m")
    print(f"Exported GGUF artifacts to {args.gguf_dir}")


if __name__ == "__main__":
    main()
