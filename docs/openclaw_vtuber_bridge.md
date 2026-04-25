# OpenClaw 与 Open-LLM-VTuber 桥接说明

当前桥接目标是让稳定的 Open-LLM-VTuber kiosk 主链路可以选择性使用 OpenClaw 做外部联网查询。OpenClaw 只返回可播报的信息字段，不负责动作、表情、视觉或硬件控制。

## 已实现的链路

1. 用户通过语音或文本进入 Open-LLM-VTuber 对话流程。
2. 后端在进入普通 LLM 对话前，可选地把用户文本写入 `/tmp/robot_input.txt`。
3. OpenClaw 侧 Agent 读取输入并写回 `/tmp/robot_output.json`。
4. 返回 JSON 格式：

```json
{
  "p": "广州今天多云，气温约 18 度，湿度较高。"
}
```

5. Open-LLM-VTuber 后端读取结果后：
   - 通过 WebSocket 发出 `openclaw-agent-result` 状态消息；
   - 将 `p` 作为外部联网查询信息注入给主 LLM；
   - 不因为 OpenClaw 结果附加摄像头快照；
   - 不通过 OpenClaw 执行底盘、耳朵或其他实体动作。

## 配置位置

文件：`Open-LLM-VTuber/conf.yaml`

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

当前已打开 `enabled: true`。因此启动 Open-LLM-VTuber 服务前，需要同时启动桥接监听器，否则每次对话会等待 OpenClaw 超时。

## 启动桥接监听器

在项目根目录运行：

```bash
scripts/openclaw_robot_bridge.py
```

后台运行示例：

```bash
mkdir -p logs
setsid scripts/openclaw_robot_bridge.py > logs/openclaw_robot_bridge.log 2>&1 &
```

当前已配置为正式用户级 systemd 服务：

```text
~/.config/systemd/user/openclaw-robot-bridge.service
```

该服务已启用开机自启，并通过 `PartOf=open-llm-vtuber.service` 跟随 VTuber 主服务停止。服务启动后会默认读取 `Open-LLM-VTuber/conf.yaml` 中的 `character_config.persona_prompt` 和 `character_name`，作为 OpenClaw 的决策上下文。

检查状态：

```bash
systemctl --user status openclaw-robot-bridge.service --no-pager
```

一次性测试天气：

```bash
rm -f /tmp/robot_input.txt /tmp/robot_output.json /tmp/robot_brain.lock
setsid scripts/openclaw_robot_bridge.py --once --once-wait 10 --timeout 120 &
printf '%s' '广州今天的天气怎么样？' > /tmp/robot_input.txt
cat /tmp/robot_output.json
```

## OpenClaw 侧约定

OpenClaw 侧只需要完成文件协议；当前仓库中的 `scripts/openclaw_robot_bridge.py` 已实现该协议，并调用 OpenClaw 本地 agent：

1. 等待 `/tmp/robot_input.txt` 出现；
2. 读取用户文本；
3. 输出 `/tmp/robot_output.json`；
4. JSON 只需要包含 `p` 字段，内容为简短中文信息，适合直接语音播报。

脚本优先调用：

```bash
/home/raspberrypi/.npm-global/bin/openclaw agent --local --json --session-id robot-vtuber-bridge
```

若 OpenClaw 输出为空，脚本会对天气和新闻类问题进行直接联网兜底：

- 天气：`wttr.in`
- 新闻：Google News RSS

## 记忆与提示词同步

当前系统有两层记忆：

1. Open-LLM-VTuber 的 `BasicMemoryAgent` 维护对话记忆。它把当前会话中的用户/AI消息保存在内存中，并可从 `Open-LLM-VTuber/chat_history/<conf_uid>/<history_uid>.json` 恢复历史对话。
2. OpenClaw 维护自己的本地 Agent session，例如 `~/.openclaw/agents/main/sessions/robot-vtuber-bridge.jsonl`，以及 `~/.openclaw/workspace/memory/` 下的工作区记忆文件。

两套记忆不直接合并。原因是 VTuber 主模型负责最终人设、语音输出和对话连续性；OpenClaw 只负责外部联网查询。直接同步完整聊天历史会增加隐私泄漏、上下文污染和重复记忆风险。

当前采用的同步策略是“同步系统提示词，不同步聊天记忆”：

- 桥接脚本启动时读取 VTuber 的角色名和 `persona_prompt`；
- OpenClaw 按同一人设边界生成 `p` 信息；
- OpenClaw 的结果再被注入 VTuber 主模型，由主模型决定最终说法；
- OpenClaw 不直接替代 VTuber 的角色表达。
- 桥接脚本默认使用 `--session-mode isolated`，每次 OpenClaw 调用使用隔离短会话，避免固定 session 反复累积桥接 prompt 导致上下文膨胀。若需要研究 OpenClaw 自身长期记忆，可手动改为 `--session-mode persistent`。

建议的系统提示词约束：

```text
你是二次元萌宠机器人的外部联网查询工具。请把查询结果解析为 JSON。
只输出 JSON，不要输出 Markdown。
字段：
- p: 查询到的信息，简短中文，适合直接朗读，最多 80 个汉字
不要输出动作、表情或摄像头意图。
```

## 论文口径

可以写：

> 本文在稳定的 Open-LLM-VTuber 主链路外，增加了 OpenClaw 外部联网查询桥接接口。该接口通过文件通信获取 OpenClaw 返回的 `p` 信息字段，并将其作为主 LLM 的实时信息提示。主 LLM 仍负责最终人设表达、视觉判断、语音输出和硬件调度，因此 OpenClaw 接入主要用于联网信息获取能力验证。

当前实测：

- 天气问题：`广州今天的天气怎么样？`
- 返回示例：`{"p":"广州: ..."}`
- 新闻问题：`讲讲今天的人工智能新闻`
- 返回示例：`{"p":"最新新闻：..."}`

不要写：

> OpenClaw 已经控制机械爪完成抓取。

当前项目没有完整机械爪抓取闭环，硬件动作也应优先保持安全关闭。
