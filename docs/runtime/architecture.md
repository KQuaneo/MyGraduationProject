# Runtime Architecture / 运行架构

## Boundary / 系统边界

当前生产系统以 Open-LLM-VTuber 后端/前端 fork 为中心。根目录只提供桥接脚本、硬件资料、部署文档和实验性本地模型内容。

The production system is centered on the Open-LLM-VTuber backend/frontend fork. Root-level files provide bridge scripts, hardware notes, deployment documentation and optional local-model experiments.

OpenClaw 不再作为机器人主脑。它是一个联网查询侧车，只返回：

OpenClaw is no longer the robot brain. It is a live web-query sidecar and returns only:

```json
{"p": "short realtime information"}
```

最终运行链路不接受 OpenClaw 输出动作、表情或视觉触发字段。

The final runtime path does not accept action, emotion or visual-trigger fields from OpenClaw.

## Request Flow / 请求流程

1. Chromium kiosk 前端采集麦克风音频并维护可见表情状态。
2. The Chromium kiosk frontend captures microphone audio and maintains visible expression state.
3. 后端通过 WebSocket 接收音频或文本输入。
4. The backend receives audio or text over WebSocket.
5. 唤醒词门控避免机器人响应环境噪声。
6. Wake-word gating keeps the robot from responding to ambient speech.
7. ASR 将语音转换为文本。
8. ASR converts speech to text.
9. 视觉触发检测器判断是否需要附加后端摄像头快照。
10. The visual-trigger detector decides whether to attach a backend camera snapshot.
11. 仅天气、新闻、最新信息或联网搜索类输入会调用 OpenClaw。
12. OpenClaw is called only for live-query inputs such as weather, news, latest information or web search.
13. 主 VTuber Agent 结合人设、记忆、可选图像和可选 `p` 信息生成最终回答。
14. The main VTuber Agent builds the final response with persona, memory, optional image and optional `p` information.
15. TTS 在树莓派本地生成并播放音频。
16. TTS audio is generated and played locally on the Raspberry Pi.
17. 前端表情和后端耳朵/舵机钩子跟随主对话状态，而不是跟随 OpenClaw。
18. Frontend expressions and backend ear/servo hooks follow the main conversation state, not OpenClaw output.

## Responsibility Split / 职责划分

| Module | 中文职责 | English Responsibility |
| --- | --- | --- |
| Open-LLM-VTuber backend | 对话编排、ASR、TTS、摄像头快照、模型调用、硬件服务 | Conversation orchestration, ASR, TTS, camera snapshots, model calls and hardware services |
| Open-LLM-VTuber frontend | kiosk UI、麦克风采集、表情状态兜底 | Kiosk UI, microphone capture and visible expression fallback |
| OpenClaw bridge | 只提供天气、新闻、联网搜索等实时信息 | Live weather, news and web-query information only |
| PCA9685 services | 面部追踪和耳朵舵机 PWM 输出 | Face tracking and ear-motion PWM output |
| Local model experiment | 未来离线动作意图解析研究，不进入生产流程 | Future offline action-intent parsing research, not production |

## Visual Context Rule / 视觉上下文规则

只有当用户明确询问场景、摄像头、图片、屏幕或当前可见物体时，系统才会附加摄像头图像。天气、普通知识问答或联网搜索不应接收摄像头上下文。

Camera images are attached only when the user explicitly asks about the scene, camera, image, screen or currently visible objects. Weather questions, ordinary knowledge questions and live web queries must not receive camera context.

## Hardware Safety / 硬件安全

舵机行为始终通过后端服务和配置开关控制。外部联网工具不能直接命令硬件，这可以防止搜索结果或网页内容变成不可控动作。

Servo behavior is kept behind backend services and configuration gates. External web-query tools cannot directly command hardware, preventing search results or web content from turning into uncontrolled motion.
