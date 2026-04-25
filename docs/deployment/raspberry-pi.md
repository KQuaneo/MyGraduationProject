# Raspberry Pi Deployment

This document describes the deployed prototype layout used on the Raspberry Pi.

## Runtime Paths

```text
/home/raspberrypi/Desktop/MyGraduationProject
├── Open-LLM-VTuber
└── scripts/openclaw_robot_bridge.py
```

## User Services

```bash
systemctl --user status open-llm-vtuber.service --no-pager
systemctl --user status openclaw-robot-bridge.service --no-pager
systemctl --user status 'app-open\x2dllm\x2dvtuber\x2dkiosk@autostart.service' --no-pager
```

Restart after code/config changes:

```bash
systemctl --user restart open-llm-vtuber.service
systemctl --user restart openclaw-robot-bridge.service
systemctl --user restart 'app-open\x2dllm\x2dvtuber\x2dkiosk@autostart.service'
```

## Backend

The backend runs from:

```text
Open-LLM-VTuber/run_server.py
```

The active runtime config is:

```text
Open-LLM-VTuber/conf.yaml
```

Important local-only values such as API keys and generated model caches must not be committed.

## OpenClaw Bridge

The bridge is a file protocol sidecar:

```text
input:  /tmp/robot_input.txt
output: /tmp/robot_output.json
lock:   /tmp/robot_brain.lock
```

Expected output:

```json
{"p": "广州: +29°C, 湿度43%"}
```

## Kiosk

The kiosk service launches Chromium at:

```text
http://127.0.0.1:12393
```

Frontend runtime patches live inside the `Open-LLM-VTuber/frontend` submodule.

## Hardware

Current hardware integration uses PCA9685 over I2C for:

- face tracking servo
- left/right ear servos

The backend owns hardware behavior. OpenClaw output does not drive servos directly.
