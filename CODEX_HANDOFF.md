# Codex Handoff / 维护交接说明

本文件保留给后续维护者快速理解当前项目状态。它不是运行入口，也不包含密钥、认证文件或本地私有配置。

This file is kept for future maintainers to understand the current project state quickly. It is not a runtime entrypoint and does not contain secrets, auth files or private local configuration.

## Repository Layout / 仓库结构

- Parent repository / 父仓库: `/home/raspberrypi/Desktop/MyGraduationProject`
- Runtime submodule / 主运行时子模块: `Open-LLM-VTuber`
- Frontend submodule / 前端子模块: `Open-LLM-VTuber/frontend`
- Bridge script / 桥接脚本: `scripts/openclaw_robot_bridge.py`
- Final thesis / 最终论文: `docs/thesis/final-thesis.docx`
- Local-model experiment / 本地小模型实验: `experiments/local_model`

The parent repository records `Open-LLM-VTuber` as a git submodule. `Open-LLM-VTuber` records `frontend` as its own submodule.

父仓库通过 submodule 记录 `Open-LLM-VTuber`；`Open-LLM-VTuber` 内部再通过 submodule 记录 `frontend`。

## Current Runtime Boundary / 当前运行边界

Open-LLM-VTuber is the production runtime. It owns persona, dialogue orchestration, ASR, TTS, backend camera snapshots, expression state and hardware services.

Open-LLM-VTuber 是生产主运行时，负责人设、对话编排、ASR、TTS、后端摄像头快照、表情状态和硬件服务。

OpenClaw is intentionally limited to live information retrieval. The bridge accepts only this output shape:

OpenClaw 被严格限制为联网信息查询工具。桥接层只接受以下输出：

```json
{"p": "short realtime information"}
```

OpenClaw must not control expressions, camera triggers, ears, chassis or other hardware.

OpenClaw 不能控制表情、摄像头触发、耳朵、底盘或其他硬件。

## Raspberry Pi Services / 树莓派服务

The deployed prototype uses user-level systemd services:

当前原型使用用户级 systemd 服务：

```bash
systemctl --user status open-llm-vtuber.service --no-pager
systemctl --user status openclaw-robot-bridge.service --no-pager
systemctl --user status 'app-open\x2dllm\x2dvtuber\x2dkiosk@autostart.service' --no-pager
```

Restart after code or config changes:

代码或配置变更后重启：

```bash
systemctl --user restart open-llm-vtuber.service
systemctl --user restart openclaw-robot-bridge.service
systemctl --user restart 'app-open\x2dllm\x2dvtuber\x2dkiosk@autostart.service'
```

## Hardware Notes / 硬件说明

- PCA9685 uses I2C address `0x40`.
- PCA9685 使用 I2C 地址 `0x40`。
- Face/chassis tracking uses channel `0`.
- 面部/底盘跟踪使用通道 `0`。
- Ear motion uses channels `2` and `3`.
- 耳朵动作使用通道 `2` 和 `3`。
- Hardware actions are controlled by backend services and configuration gates.
- 硬件动作由后端服务和配置开关控制。
- External web-query output must never drive hardware directly.
- 外部联网查询结果不能直接驱动硬件。

## Public Repository Notes / 公开仓库注意事项

Do not commit local runtime state:

不要提交本地运行状态：

- `Open-LLM-VTuber/conf.yaml`
- `Open-LLM-VTuber/.env.systemd`
- virtual environments / 虚拟环境
- model weights and GGUF exports / 模型权重和 GGUF 导出
- logs, cache and chat history / 日志、缓存和聊天历史
- OpenClaw auth or local workspace files / OpenClaw 认证和本地工作区文件

The portfolio-facing entry points are:

作品集展示入口：

- `README.md`
- `docs/runtime/architecture.md`
- `docs/deployment/raspberry-pi.md`
- `docs/openclaw_vtuber_bridge.md`
- `experiments/local_model/README.md`

## Verification Checklist / 验证清单

Before pushing a public update, run:

公开推送前建议检查：

```bash
git status -sb
git submodule status --recursive
git grep -n -I -E 'sk-[A-Za-z0-9_-]{20,}|Bearer [A-Za-z0-9._-]{30,}|AKIA[0-9A-Z]{16}'
unzip -t docs/thesis/final-thesis.docx
```

For Python syntax checks:

Python 语法检查：

```bash
python3 -m py_compile scripts/openclaw_robot_bridge.py experiments/local_model/train_robot.py experiments/local_model/run_inference.py
```

The active git commit hashes should be read with `git log -1 --oneline` in each repository rather than copied manually into this handoff.

当前提交哈希应在各仓库中通过 `git log -1 --oneline` 实时查看，不再手写到本交接文档中，避免过期。
