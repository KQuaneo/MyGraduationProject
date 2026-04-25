# Raspberry Pi Deployment / 树莓派部署

本文档描述当前树莓派原型机的部署结构、服务命令和运行边界。

This document describes the deployed Raspberry Pi prototype layout, service commands and runtime boundaries.

## Runtime Paths / 运行路径

```text
/home/raspberrypi/Desktop/MyGraduationProject
├── Open-LLM-VTuber
└── scripts/openclaw_robot_bridge.py
```

中文说明：`Open-LLM-VTuber` 是主运行时，根目录脚本只承担集成桥接职责。

English: `Open-LLM-VTuber` is the main runtime. Root-level scripts only provide integration bridge behavior.

## User Services / 用户级服务

查看服务状态：

Check service status:

```bash
systemctl --user status open-llm-vtuber.service --no-pager
systemctl --user status openclaw-robot-bridge.service --no-pager
systemctl --user status 'app-open\x2dllm\x2dvtuber\x2dkiosk@autostart.service' --no-pager
```

代码或配置变更后重启：

Restart after code or config changes:

```bash
systemctl --user restart open-llm-vtuber.service
systemctl --user restart openclaw-robot-bridge.service
systemctl --user restart 'app-open\x2dllm\x2dvtuber\x2dkiosk@autostart.service'
```

## Backend / 后端

后端入口：

Backend entrypoint:

```text
Open-LLM-VTuber/run_server.py
```

当前运行配置：

Active runtime config:

```text
Open-LLM-VTuber/conf.yaml
```

中文说明：API key、模型缓存、运行日志和本地认证文件属于机器私有内容，不能提交到 Git。

English: API keys, model caches, runtime logs and local auth files are machine-specific and must not be committed.

## OpenClaw Bridge / OpenClaw 桥接

桥接服务使用文件协议：

The bridge service uses a file protocol:

```text
input:  /tmp/robot_input.txt
output: /tmp/robot_output.json
lock:   /tmp/robot_brain.lock
```

期望输出只包含 `p` 字段：

Expected output contains only the `p` field:

```json
{"p": "广州: +29°C, 湿度43%"}
```

中文说明：OpenClaw 只负责联网信息，不负责摄像头、表情、耳朵、底盘或其他硬件动作。

English: OpenClaw only provides live information. It does not control camera context, expressions, ears, chassis or other hardware actions.

## Kiosk / 前端自启动

kiosk 服务启动 Chromium 并访问：

The kiosk service launches Chromium at:

```text
http://127.0.0.1:12393
```

前端运行补丁位于 `Open-LLM-VTuber/frontend` 子模块中。

Frontend runtime patches live inside the `Open-LLM-VTuber/frontend` submodule.

## Hardware / 硬件

当前硬件集成通过 I2C 上的 PCA9685 控制：

Current hardware integration uses PCA9685 over I2C for:

- 面部追踪舵机 / face tracking servo
- 左右耳朵舵机 / left and right ear servos

硬件行为由后端拥有，OpenClaw 输出不会直接驱动舵机。

The backend owns hardware behavior. OpenClaw output does not drive servos directly.
