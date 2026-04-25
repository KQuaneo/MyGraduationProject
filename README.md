# Xiaohui Anime-Pet Embodied AI

Xiaohui is a Raspberry Pi based anime-pet embodied interaction system. It combines voice wake-up, ASR, Qwen-VL visual reasoning, Open-LLM-VTuber conversation orchestration, local TTS playback, a kiosk expression UI, OpenClaw live web queries, PCA9685 servo control and a small local-model experiment.

This repository is the graduation-project workspace cleaned into a portfolio-ready structure. The production runtime is the `Open-LLM-VTuber` submodule plus the root bridge/deployment assets.

## Highlights

- Wake-word gated Chinese voice interaction for a desktop anime-pet robot.
- Backend camera snapshots on Raspberry Pi, avoiding unstable browser camera permissions.
- Qwen-VL multimodal reasoning for explicit visual questions.
- OpenClaw bridge limited to live information queries such as weather, news and web search.
- Final OpenClaw protocol is `{"p": "short information"}` only; no action or emotion control is delegated to OpenClaw.
- Local Piper TTS playback and frontend expression-state fallback for kiosk stability.
- PCA9685-based face tracking and ear motion hooks with hardware safety boundaries.
- Optional local small-model experiment for future offline robot action-intent parsing.

## Current Runtime Architecture

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

OpenClaw is intentionally narrow: it only supplies realtime information in `p`. Ordinary chat, persona, vision, expression and hardware behavior stay in the main VTuber backend.

## Repository Layout

```text
.
├── Open-LLM-VTuber/          # production backend/frontend fork as a git submodule
├── scripts/                  # root-level integration services
├── docs/                     # architecture, deployment, thesis and runtime notes
├── hardware/                 # BOM and mechanical design assets
├── firmware/                 # embedded firmware placeholder/config
└── experiments/local_model/  # optional local small-model research path
```

## Main Components

- `Open-LLM-VTuber`: forked runtime with Raspberry Pi camera, kiosk, expression, TTS, OpenClaw and servo integrations.
- `scripts/openclaw_robot_bridge.py`: file-protocol bridge between the VTuber backend and OpenClaw.
- `docs/openclaw_vtuber_bridge.md`: OpenClaw protocol and operational notes.
- `experiments/local_model`: offline robot intent parser experiment. It is not part of the production flow.

## Raspberry Pi Services

The deployed prototype uses user-level systemd services:

```bash
systemctl --user status open-llm-vtuber.service --no-pager
systemctl --user status openclaw-robot-bridge.service --no-pager
systemctl --user status 'app-open\x2dllm\x2dvtuber\x2dkiosk@autostart.service' --no-pager
```

See [docs/deployment/raspberry-pi.md](docs/deployment/raspberry-pi.md) for setup and operations.

## Documentation

- [Architecture](docs/runtime/architecture.md)
- [Raspberry Pi deployment](docs/deployment/raspberry-pi.md)
- [OpenClaw bridge](docs/openclaw_vtuber_bridge.md)
- [Local model experiment](experiments/local_model/README.md)
- [Final thesis document](docs/thesis/final-thesis.docx)

## Development Notes

Large generated files are intentionally not committed: virtual environments, model weights, GGUF exports, runtime logs, OpenClaw auth files and temporary screenshots.

The current production flow depends on `Open-LLM-VTuber/`, `scripts/openclaw_robot_bridge.py` and Raspberry Pi service files. The old standalone `brain/online_agent` runtime was removed because it is no longer used by the main process.
