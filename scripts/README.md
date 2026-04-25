# Scripts

Production integration scripts that live outside the Open-LLM-VTuber submodule.

## `openclaw_robot_bridge.py`

File-protocol bridge used by `openclaw-robot-bridge.service`.

Responsibilities:

- listen for `/tmp/robot_input.txt`
- call the local OpenClaw agent for live-query requests
- fall back to direct weather/news queries when needed
- normalize output to `{"p": "..."}` only
- write `/tmp/robot_output.json`

It does not execute hardware actions and does not emit emotion/action fields.
