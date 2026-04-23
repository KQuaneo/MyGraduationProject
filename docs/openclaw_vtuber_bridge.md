# OpenClaw 与 Open-LLM-VTuber 桥接说明

当前桥接目标是让稳定的 Open-LLM-VTuber kiosk 主链路可以选择性使用 OpenClaw 做外部智能体意图解析，同时不直接执行高风险硬件动作。

## 已实现的链路

1. 用户通过语音或文本进入 Open-LLM-VTuber 对话流程。
2. 后端在进入普通 LLM 对话前，可选地把用户文本写入 `/tmp/robot_input.txt`。
3. OpenClaw 侧 Agent 读取输入并写回 `/tmp/robot_output.json`。
4. 返回 JSON 格式：

```json
{
  "action": "look",
  "reply": "让我看看",
  "emotion": "thinking"
}
```

5. Open-LLM-VTuber 后端读取结果后：
   - 通过 WebSocket 发出 `openclaw-agent-result` 状态消息；
   - 将 `action/reply/emotion` 作为结构化提示注入给主 LLM；
   - 当 `action` 为 `look` 或 `scan` 时，强制附加后端摄像头快照；
   - 在 `safe_mode: true` 下不直接执行底盘、耳朵或其他实体动作。

## 配置位置

文件：`Open-LLM-VTuber/conf.yaml`

```yaml
system_config:
  openclaw_agent:
    enabled: false
    input_file: '/tmp/robot_input.txt'
    output_file: '/tmp/robot_output.json'
    lock_file: '/tmp/robot_brain.lock'
    timeout_sec: 1.5
    lock_timeout_sec: 0.5
    inject_result_into_prompt: true
    safe_mode: true
```

默认关闭是为了不影响当前稳定 kiosk。如果要测试 OpenClaw 接口，把 `enabled` 改为 `true`，并确保 OpenClaw 侧有会话或脚本监听 `/tmp/robot_input.txt`。

## OpenClaw 侧约定

OpenClaw 侧只需要完成文件协议：

1. 等待 `/tmp/robot_input.txt` 出现；
2. 读取用户文本；
3. 输出 `/tmp/robot_output.json`；
4. JSON 至少包含 `action`、`reply`、`emotion` 三个字段。

建议的系统提示词约束：

```text
你是二次元萌宠机器人的外部智能体主脑。请把用户意图解析为 JSON。
只输出 JSON，不要输出 Markdown。
字段：
- action: none/look/scan/shake/wiggle/turn_left/turn_right/turn_away/look_away
- reply: 简短中文回复，适合直接朗读
- emotion: neutral/happy/sad/angry/surprise/fear/thinking/curious
当前实体动作处于安全模式，运动类 action 只表示意图，不代表已经执行。
```

## 论文口径

可以写：

> 本文在稳定的 Open-LLM-VTuber 主链路外，增加了 OpenClaw 外部智能体桥接接口。该接口通过文件通信获取 OpenClaw 返回的 action、reply、emotion 结构化结果，并将其作为主 LLM 的意图提示和视觉触发依据。当前系统默认开启 safe_mode，不直接执行实体动作，因此 OpenClaw 接入主要用于智能体决策接口验证和后续动作规划扩展。

不要写：

> OpenClaw 已经控制机械爪完成抓取。

当前项目没有完整机械爪抓取闭环，硬件动作也应优先保持安全关闭。
