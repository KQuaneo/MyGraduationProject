# Scripts / 脚本

本目录保存位于 Open-LLM-VTuber 子模块之外的生产集成脚本。

This directory contains production integration scripts that live outside the Open-LLM-VTuber submodule.

## `openclaw_robot_bridge.py`

`openclaw_robot_bridge.py` 是 `openclaw-robot-bridge.service` 使用的文件协议桥接服务。

`openclaw_robot_bridge.py` is the file-protocol bridge used by `openclaw-robot-bridge.service`.

职责：

Responsibilities:

- 监听 `/tmp/robot_input.txt`。
- Listen for `/tmp/robot_input.txt`.
- 调用本地 OpenClaw agent 处理联网查询。
- Call the local OpenClaw agent for live-query requests.
- 必要时对天气和新闻问题执行直接联网兜底。
- Fall back to direct weather/news queries when needed.
- 将输出标准化为 `{"p": "..."}`。
- Normalize output to `{"p": "..."}` only.
- 写入 `/tmp/robot_output.json`。
- Write `/tmp/robot_output.json`.

该脚本不会执行硬件动作，也不会输出 emotion/action 字段。

It does not execute hardware actions and does not emit emotion/action fields.
