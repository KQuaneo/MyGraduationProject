"""Run a GGUF robot intent model locally with llama-cpp-python."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from llama_cpp import Llama


PROMPT = """Below is an instruction that describes a robot-control task, paired with optional sensor context. Return only one compact JSON object.

### Instruction:
{}

### Input:
{}

### Response:
"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--threads", type=int, default=4)
    parser.add_argument("commands", nargs="*", default=["寻找苹果", "向右旋转"])
    args = parser.parse_args()

    llm = Llama(
        model_path=str(args.model),
        n_ctx=2048,
        n_threads=args.threads,
        verbose=False,
    )

    for command in args.commands:
        output = llm(
            PROMPT.format(command, "", ""),
            max_tokens=128,
            stop=["<|im_end|>", "<|endoftext|>"],
            echo=False,
        )
        text = output["choices"][0]["text"].strip()
        print(f"\ncommand: {command}")
        print(f"raw: {text}")
        try:
            print(f"json: {json.loads(text)}")
        except json.JSONDecodeError:
            print("json: parse failed")


if __name__ == "__main__":
    main()
