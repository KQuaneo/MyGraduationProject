# OpenClaw 与 Open-LLM-VTuber 桥接说明 / OpenClaw and Open-LLM-VTuber Bridge

当前桥接目标是让稳定的 Open-LLM-VTuber kiosk 主链路选择性使用 OpenClaw 做外部联网查询。OpenClaw 只返回可播报的信息字段，不负责动作、表情、视觉或硬件控制。

The bridge lets the stable Open-LLM-VTuber kiosk runtime selectively use OpenClaw for live web queries. OpenClaw returns only speakable information and does not control actions, expressions, vision or hardware.

## 已实现链路 / Implemented Flow

1. 用户通过语音或文本进入 Open-LLM-VTuber 对话流程。
2. The user enters the Open-LLM-VTuber conversation flow through voice or text.
3. 后端在普通 LLM 对话前，可选地把用户文本写入 `/tmp/robot_input.txt`。
4. Before normal LLM conversation, the backend may write the user text to `/tmp/robot_input.txt`.
5. OpenClaw 侧 Agent 读取输入并写回 `/tmp/robot_output.json`。
6. The OpenClaw-side agent reads the input and writes `/tmp/robot_output.json`.
7. 返回 JSON 只包含 `p` 字段。
8. The returned JSON contains only the `p` field.

```json
{
  "p": "广州今天多云，气温约 18 度，湿度较高。"
}
```

Open-LLM-VTuber 后端读取结果后：

After reading the result, the Open-LLM-VTuber backend:

- 通过 WebSocket 发出 `openclaw-agent-result` 状态消息。
- Sends an `openclaw-agent-result` status message over WebSocket.
- 将 `p` 作为外部联网查询信息注入给主 LLM。
- Injects `p` into the main LLM as external live-query information.
- 不因为 OpenClaw 结果附加摄像头快照。
- Does not attach a camera snapshot because of OpenClaw output.
- 不通过 OpenClaw 执行底盘、耳朵或其他实体动作。
- Does not execute chassis, ear or other physical actions through OpenClaw.

## 配置位置 / Configuration

文件 / File: `Open-LLM-VTuber/conf.yaml`

```yaml
system_config:
  openclaw_agent:
    enabled: false
    input_file: '/tmp/robot_input.txt'
    output_file: '/tmp/robot_output.json'
    lock_file: '/tmp/robot_brain.lock'
    timeout_sec: 90.0
    lock_timeout_sec: 0.5
    inject_result_into_prompt: true
    safe_mode: true
```

当前实际运行可设置 `enabled: true`。启动 Open-LLM-VTuber 服务前，应同时启动桥接监听器，否则联网查询会等待超时。

The deployed runtime may set `enabled: true`. Start the bridge listener before starting Open-LLM-VTuber; otherwise live-query calls will wait until timeout.

## 启动桥接监听器 / Start the Bridge Listener

在项目根目录运行：

Run from the project root:

```bash
scripts/openclaw_robot_bridge.py
```

后台运行示例：

Background example:

```bash
mkdir -p logs
setsid scripts/openclaw_robot_bridge.py > logs/openclaw_robot_bridge.log 2>&1 &
```

当前正式部署使用用户级 systemd 服务：

The deployed prototype uses a user-level systemd service:

```text
~/.config/systemd/user/openclaw-robot-bridge.service
```

该服务跟随 VTuber 主服务停止，并读取 `Open-LLM-VTuber/conf.yaml` 中的 `character_config.persona_prompt` 和 `character_name` 作为查询上下文。

The service stops with the VTuber main service and reads `character_config.persona_prompt` plus `character_name` from `Open-LLM-VTuber/conf.yaml` as query context.

检查状态：

Check status:

```bash
systemctl --user status openclaw-robot-bridge.service --no-pager
```

一次性测试天气：

One-shot weather test:

```bash
rm -f /tmp/robot_input.txt /tmp/robot_output.json /tmp/robot_brain.lock
setsid scripts/openclaw_robot_bridge.py --once --once-wait 10 --timeout 120 &
printf '%s' '广州今天的天气怎么样？' > /tmp/robot_input.txt
cat /tmp/robot_output.json
```

## OpenClaw 侧约定 / OpenClaw Contract

OpenClaw 侧只需要完成文件协议：

The OpenClaw side only needs to implement the file protocol:

1. 等待 `/tmp/robot_input.txt` 出现。
2. Wait for `/tmp/robot_input.txt`.
3. 读取用户文本。
4. Read the user text.
5. 输出 `/tmp/robot_output.json`。
6. Write `/tmp/robot_output.json`.
7. JSON 只包含 `p` 字段，内容为简短中文信息，适合直接语音播报。
8. The JSON contains only `p`, a short Chinese message suitable for direct speech output.

脚本优先调用：

The script first calls:

```bash
/home/raspberrypi/.npm-global/bin/openclaw agent --local --json --session-id robot-vtuber-bridge
```

若 OpenClaw 输出为空，脚本会对天气和新闻类问题进行直接联网兜底：

If OpenClaw returns empty output, the script falls back to direct web queries for weather and news:

- 天气 / Weather: `wttr.in`
- 新闻 / News: Google News RSS

## 记忆与提示词同步 / Memory and Prompt Synchronization

当前系统有两层记忆：

The system has two memory layers:

1. Open-LLM-VTuber 的 `BasicMemoryAgent` 维护主对话记忆，可从 `Open-LLM-VTuber/chat_history/<conf_uid>/<history_uid>.json` 恢复历史对话。
2. Open-LLM-VTuber `BasicMemoryAgent` maintains main conversation memory and can restore history from `Open-LLM-VTuber/chat_history/<conf_uid>/<history_uid>.json`.
3. OpenClaw 维护自己的本地 Agent session，例如 `~/.openclaw/agents/main/sessions/robot-vtuber-bridge.jsonl`。
4. OpenClaw maintains its own local agent session, for example `~/.openclaw/agents/main/sessions/robot-vtuber-bridge.jsonl`.

两套记忆不直接合并。主 VTuber 模型负责最终人设、语音输出和对话连续性；OpenClaw 只负责外部联网查询。直接同步完整聊天历史会增加隐私泄漏、上下文污染和重复记忆风险。

The two memory layers are not merged. The main VTuber model owns persona, speech output and conversation continuity, while OpenClaw only performs external web queries. Synchronizing full chat history would increase privacy leakage, context pollution and duplicate-memory risks.

当前策略是“同步系统提示词，不同步聊天记忆”：

The current strategy is "sync the system prompt, not chat memory":

- 桥接脚本启动时读取 VTuber 的角色名和 `persona_prompt`。
- The bridge reads the VTuber character name and `persona_prompt` at startup.
- OpenClaw 按同一人设边界生成 `p` 信息。
- OpenClaw generates `p` under the same persona boundary.
- OpenClaw 结果再注入 VTuber 主模型，由主模型决定最终说法。
- The result is injected into the main VTuber model, which decides the final wording.
- OpenClaw 不直接替代 VTuber 的角色表达。
- OpenClaw does not replace VTuber persona expression.
- 默认使用隔离短会话，避免固定 session 累积桥接 prompt 导致上下文膨胀。
- Isolated short sessions are used by default to avoid context growth from repeated bridge prompts.

建议系统提示词约束：

Recommended system-prompt constraint:

```text
你是二次元萌宠机器人的外部联网查询工具。请把查询结果解析为 JSON。
只输出 JSON，不要输出 Markdown。
字段：
- p: 查询到的信息，简短中文，适合直接朗读，最多 80 个汉字
不要输出动作、表情或摄像头意图。
```

## 论文口径 / Thesis Wording

可以写：

Recommended wording:

> 本文在稳定的 Open-LLM-VTuber 主链路外，增加了 OpenClaw 外部联网查询桥接接口。该接口通过文件通信获取 OpenClaw 返回的 `p` 信息字段，并将其作为主 LLM 的实时信息提示。主 LLM 仍负责最终人设表达、视觉判断、语音输出和硬件调度，因此 OpenClaw 接入主要用于联网信息获取能力验证。

English version:

> This project adds an OpenClaw external web-query bridge outside the stable Open-LLM-VTuber main runtime. The bridge receives the `p` information field from OpenClaw through file-based communication and injects it into the main LLM as realtime context. The main LLM still owns persona expression, visual reasoning, speech output and hardware scheduling, so the OpenClaw integration mainly validates live information retrieval.

当前实测：

Current tested examples:

- 天气问题 / Weather question: `广州今天的天气怎么样？`
- 返回示例 / Example output: `{"p":"广州: ..."}`
- 新闻问题 / News question: `讲讲今天的人工智能新闻`
- 返回示例 / Example output: `{"p":"最新新闻：..."}`

不要写：

Do not claim:

> OpenClaw 已经控制机械爪完成抓取。

当前项目没有完整机械爪抓取闭环，硬件动作也应优先保持安全关闭。

The current project does not implement a complete robotic-claw grasping loop, and hardware actions should remain safety-gated.
