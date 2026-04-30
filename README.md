# Xiaohui Anime-Pet Embodied AI / 小灰二次元萌宠具身智能

小灰是一个基于 Raspberry Pi 的二次元萌宠具身交互系统，整合了语音唤醒、ASR、Qwen-VL 视觉理解、Open-LLM-VTuber 对话编排、本地 TTS 播放、kiosk 表情前端、OpenClaw 联网查询、PCA9685 舵机控制以及本地小模型实验。

Xiaohui is a Raspberry Pi based anime-pet embodied interaction system. It combines wake-word gated speech input, ASR, Qwen-VL visual reasoning, Open-LLM-VTuber conversation orchestration, local TTS playback, a kiosk expression UI, OpenClaw live web queries, PCA9685 servo control and a local small-model experiment.

本仓库已从毕业设计开发目录整理为可展示的作品集项目。当前生产主链路是 `Open-LLM-VTuber` 子模块，根目录保留桥接脚本、部署文档、硬件资料和实验性本地模型内容。

This repository has been curated from the graduation-project workspace into a portfolio-ready project. The production runtime is the `Open-LLM-VTuber` submodule, while the root keeps bridge scripts, deployment docs, hardware assets and the optional local-model experiment.

## Highlights / 项目亮点

- 中文语音唤醒交互：机器人只在唤醒后响应，降低环境噪声误触发。
- Wake-word gated Chinese voice interaction reduces accidental responses from ambient speech.
- 后端摄像头快照：在 Raspberry Pi 后端采集图像，避免浏览器摄像头权限不稳定。
- Backend camera snapshots avoid unstable browser-side camera permission issues on Raspberry Pi.
- Qwen-VL 多模态理解：仅在用户明确询问画面、摄像头或可见物体时注入视觉上下文。
- Qwen-VL multimodal reasoning is used only when the user explicitly asks visual questions.
- OpenClaw 边界收敛：只负责天气、新闻、联网搜索等实时信息查询。
- OpenClaw is intentionally narrow: weather, news, web search and other realtime information queries only.
- 最终 OpenClaw 协议为 `{"p": "short information"}`，不再让外部工具控制动作或表情。
- The final OpenClaw protocol is `{"p": "short information"}` only; no action or emotion control is delegated to OpenClaw.
- 本地 TTS 与 kiosk 表情兜底：保证语音播放和前端表情状态在树莓派上稳定运行。
- Local TTS playback and frontend expression fallback improve kiosk stability on Raspberry Pi.
- PCA9685 硬件接口：保留面部追踪与耳朵舵机控制钩子，并通过后端服务隔离硬件安全边界。
- PCA9685 hardware hooks support face tracking and ear motion while keeping hardware control behind backend safety boundaries.
- 本地小模型实验：保留离线机器人意图解析研究路径，但不影响当前主流程。
- The local small-model experiment is kept as a future offline intent-parsing path, separate from production.

## Runtime Architecture / 运行架构

```text
User voice/text
  -> Chromium kiosk frontend
  -> Open-LLM-VTuber FastAPI/WebSocket backend
  -> wake-word gate + ASR/VAD
  -> visual-trigger detector
  -> optional backend camera snapshot
  -> optional OpenClaw live-query bridge
  -> Qwen-VL / main VTuber Agent
  -> TTS + local audio playback
  -> expression UI + ear/servo services
```

中文说明：OpenClaw 不再作为机器人主脑，它只是联网信息侧车。普通对话、人设表达、视觉判断、表情状态和硬件控制都留在 Open-LLM-VTuber 主后端中，避免外部查询工具污染主流程或直接驱动硬件。

English: OpenClaw is no longer the main robot brain. It is a live-information sidecar only. Ordinary conversation, persona, visual reasoning, expression state and hardware behavior stay in the Open-LLM-VTuber backend to avoid context pollution and unsafe external hardware control.

### Agent Abstraction / Agent 抽象

中文说明：最终系统将 `BasicMemoryAgent` 作为唯一主 Agent。系统提示词、人设记忆、可选视觉帧和可选 OpenClaw 实时信息会被统一整理成 Agent 输入；摄像头和 OpenClaw 都只是上下文提供器，不直接生成最终回复，也不直接控制表情或硬件。

English: The final system uses `BasicMemoryAgent` as the single main Agent. The system prompt, persona memory, optional visual frame and optional OpenClaw realtime information are normalized into the Agent input. The camera and OpenClaw are context providers only; they do not directly produce the final answer or control expressions and hardware.

See [docs/runtime/agent-abstraction.md](docs/runtime/agent-abstraction.md) for the production system prompt and the visual/web context flow.

## Repository Layout / 仓库结构

```text
.
├── Open-LLM-VTuber/          # production backend/frontend fork as a git submodule
├── scripts/                  # root-level integration services
├── docs/                     # architecture, deployment, thesis and runtime notes
├── hardware/                 # BOM and mechanical design assets
├── firmware/                 # embedded firmware placeholder/config
└── experiments/local_model/  # optional local small-model research path
```

## Main Components / 核心模块

- `Open-LLM-VTuber`: 当前生产运行时，包含树莓派摄像头、kiosk 前端、表情、TTS、OpenClaw 和舵机集成。
- `Open-LLM-VTuber`: production runtime with Raspberry Pi camera, kiosk UI, expression, TTS, OpenClaw and servo integrations.
- `scripts/openclaw_robot_bridge.py`: VTuber 后端与 OpenClaw 之间的文件协议桥接服务。
- `scripts/openclaw_robot_bridge.py`: file-protocol bridge between the VTuber backend and OpenClaw.
- `docs/openclaw_vtuber_bridge.md`: OpenClaw `p`-only 协议、服务运行方式和论文口径。
- `docs/openclaw_vtuber_bridge.md`: OpenClaw `p`-only protocol, service operations and thesis wording.
- `experiments/local_model`: 离线机器人意图解析实验，不参与当前生产链路。
- `experiments/local_model`: offline robot intent parser experiment, not part of the production flow.

## Raspberry Pi Services / 树莓派服务

The deployed prototype uses user-level systemd services:

```bash
systemctl --user status open-llm-vtuber.service --no-pager
systemctl --user status openclaw-robot-bridge.service --no-pager
systemctl --user status 'app-open\x2dllm\x2dvtuber\x2dkiosk@autostart.service' --no-pager
```

中文说明：主服务负责后端对话、ASR/TTS、视觉和硬件钩子；桥接服务负责 OpenClaw 联网查询；kiosk 服务负责 Chromium 前端显示和麦克风输入。

English: The main service owns backend conversation, ASR/TTS, vision and hardware hooks. The bridge service owns OpenClaw live queries. The kiosk service owns Chromium display and microphone capture.

See [docs/deployment/raspberry-pi.md](docs/deployment/raspberry-pi.md) for setup and operations.

## Documentation / 文档

- [Architecture / 架构](docs/runtime/architecture.md)
- [Agent abstraction / Agent 抽象](docs/runtime/agent-abstraction.md)
- [Public system prompt / 公开系统提示词](docs/runtime/system-prompt.md)
- [Public thesis materials / 论文公开支撑材料](docs/thesis/public-thesis-materials.md)
- [Raspberry Pi deployment / 树莓派部署](docs/deployment/raspberry-pi.md)
- [OpenClaw bridge / OpenClaw 桥接](docs/openclaw_vtuber_bridge.md)
- [Local model experiment / 本地小模型实验](experiments/local_model/README.md)
- [Final thesis document / 最终论文](docs/thesis/final-thesis.docx)

## Development Notes / 开发说明

中文说明：虚拟环境、模型权重、GGUF 导出、运行日志、OpenClaw 认证文件和临时截图等大文件或本地敏感文件不会提交。当前生产流程依赖 `Open-LLM-VTuber/`、`scripts/openclaw_robot_bridge.py` 和树莓派用户级 systemd 服务。旧的独立 `brain/online_agent` 运行时已经移除，因为它不再参与主进程。

English: Large generated or machine-specific files are intentionally not committed, including virtual environments, model weights, GGUF exports, runtime logs, OpenClaw auth files and temporary screenshots. The current production flow depends on `Open-LLM-VTuber/`, `scripts/openclaw_robot_bridge.py` and Raspberry Pi user-level systemd services. The old standalone `brain/online_agent` runtime was removed because it is no longer used by the main process.
