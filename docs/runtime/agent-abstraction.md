# Dialogue Module and Context Abstraction / 对话模块与上下文抽象设计

本文档补充毕业论文中“主脑”和多模态输入输出链路的说明。最终系统不把“主脑”泛化描述为自主规划、调用工具并直接控制硬件的通用 Agent。更准确的表述是：系统包含一个主对话生成与编排模块，代码中由 Open-LLM-VTuber 的 `BasicMemoryAgent` 类实现；视觉输入和 OpenClaw 联网输入都被抽象为“上下文提供器”，只向主对话模块提供信息。

This document clarifies the dialogue module and multimodal context flow used by the final prototype. The "brain" is not described as a generalized autonomous Agent that plans, calls tools and directly controls hardware. A more accurate description is: the system has a main dialogue generation and orchestration module, implemented by Open-LLM-VTuber's `BasicMemoryAgent` class. Vision input and OpenClaw web input are treated as context providers.

## Core Abstraction / 核心抽象

```text
User voice/text
  -> wake-word gate + ASR
  -> context router
       -> optional camera snapshot context
       -> optional OpenClaw realtime information context
  -> main dialogue module (BasicMemoryAgent class)
       -> system prompt + memory + normalized user input
       -> LLM free-text stream
  -> output post-processing pipeline
       -> SentenceOutput(display_text, tts_text, actions)
       -> TTS + expression UI + backend hardware hooks
```

中文说明：主对话模块负责“怎么回答”和“以什么角色回答”。摄像头和 OpenClaw 不直接输出最终回复，也不直接控制表情、耳朵舵机或其他硬件。

English: The main dialogue module decides what to say and how to say it. The camera and OpenClaw do not produce the final answer directly, and they do not directly control expressions, ear servos or other hardware.

## System Prompt / 系统提示词

生产配置位于 `Open-LLM-VTuber/conf.yaml` 的 `character_config.persona_prompt`。该提示词定义了“小灰”的角色、人设、回答长度和视觉使用边界。公开版本见 [Public system prompt / 公开系统提示词](system-prompt.md)。

The production prompt is stored in `character_config.persona_prompt` inside `Open-LLM-VTuber/conf.yaml`. It defines Xiaohui's persona, response style, answer length and visual-context boundary. The public version is documented in [Public system prompt](system-prompt.md).

```text
你是“小灰”，一个二次元萌宠机器人助手，性格机灵、亲近、好奇，有一点点撒娇感。
你不是冷冰冰的工具，也不是严肃客服；你像一只会认真帮忙的小电子宠物，回答时自然、轻快、带一点可爱气质。
可以偶尔使用“嗯嗯”“欸嘿”“交给小灰吧”“我看看喔”这类短语，但不要每句话都卖萌，不要大量使用口癖，不要影响信息清晰度。
用户问正事时先把事情说清楚，再保留一点温和活泼的语气。
只有当用户明确提到摄像头、画面、图片、截图、屏幕，或问题明显是在询问当前所见内容时，才根据视觉内容回答。
如果用户的问题与画面无关，优先直接回答用户的问题，不要强行描述画面。
当用户提供摄像头、截图或其他图像，并且问题确实与视觉相关时，再根据画面内容直接回答；可以可爱一点，但不要阴阳怪气，不要刻薄，不要角色扮演过头。
如果画面里看不清，就明确说看不清，不要编造。
回答要短、自然、可直接朗读。
默认用 1 到 3 句简短中文回答。
尽量使用口语化短句，避免书面腔、长段落和复杂列表，方便语音播报。
优先描述可见的人、物体、动作、位置、颜色和场景。
除非用户明确要求，否则不要长篇发挥，不要乱开玩笑，不要脱离问题。
```

在代码层，`BasicMemoryAgent` 会把该人设提示词设置为 LLM 的 system prompt，并在用户打断模式下追加一条中断处理规则。历史对话则从 `chat_history/<conf_uid>/<history_uid>.json` 恢复为对话记忆。

In code, `BasicMemoryAgent` uses this persona prompt as the LLM system prompt and appends an interruption-handling rule when interruption mode is enabled. Conversation history is restored from `chat_history/<conf_uid>/<history_uid>.json` as dialogue memory.

## Normalized Dialogue Input / 对话模块统一输入

进入主对话模块前，所有输入会被归一化为 `BatchInput`：

Before reaching the main dialogue module, all inputs are normalized into `BatchInput`:

```text
BatchInput
  texts: user text or ASR transcription
  images: optional camera/screenshot image data
  metadata: optional runtime flags and OpenClaw result
```

`BasicMemoryAgent` 再把 `BatchInput` 转换为 LLM messages：文本进入 user message，图片以 `image_url` 形式进入同一个 user message，历史记忆位于当前轮之前。

`BasicMemoryAgent` converts `BatchInput` into LLM messages: text becomes user content, images are attached as `image_url` blocks in the same user message, and memory messages are placed before the current turn.

## Visual Input Flow / 视觉输入流程

视觉输入不是每轮都进入模型，而是由后端判断是否需要附加。核心规则是：只有用户明确询问当前画面、摄像头、图片、截图、屏幕或可见物体时，才附加视觉上下文。

Visual input is not sent to the model on every turn. The backend attaches it only when the user explicitly asks about the current scene, camera, image, screenshot, screen or visible objects.

```text
1. User asks a question
2. ASR/text input becomes input_text
3. should_attach_visual_context(input_text) checks visual keywords
4. If visual context is needed:
     build_backend_camera_image() captures a Raspberry Pi camera frame
     frame is encoded as data:image/jpeg;base64,...
5. BatchInput contains both text and image
6. Qwen-VL / OpenAI-compatible VL model answers with visual context
```

中文论文口径：本文将视觉模块抽象为主对话模块的可选感知上下文。当用户问题触发视觉语义时，后端摄像头服务采集当前帧并编码为图像输入，与文本问题共同组成多模态 `BatchInput`。若问题不涉及当前画面，则不附加图像，从而避免天气、百科或闲聊问题被无关摄像头信息污染。

English thesis wording: The vision module is abstracted as optional perceptual context for the main dialogue module. When the user question triggers visual semantics, the backend camera service captures the current frame, encodes it as image input, and combines it with the text question into a multimodal `BatchInput`. If the question is unrelated to the current scene, no image is attached, preventing weather, factual QA or casual chat from being polluted by irrelevant camera context.

## External Web Input Flow / 外部联网输入流程

OpenClaw 被限制为实时信息查询侧车，只处理天气、新闻、最新信息、搜索和联网查询类问题。它的输出协议只保留 `p` 字段。

OpenClaw is restricted to a live-information sidecar for weather, news, latest information, search and web-query questions. Its output protocol keeps only the `p` field.

```text
1. User asks a live-query question
2. should_query_openclaw(input_text) matches live-query keywords
3. Backend writes input_text to /tmp/robot_input.txt
4. openclaw_robot_bridge.py invokes OpenClaw or fallback web query
5. Bridge writes /tmp/robot_output.json
6. Backend normalizes result to {"p": "..."}
7. Backend injects p as an OpenClaw note before the user's original input
8. The main dialogue module produces the final spoken answer
```

示例注入文本：

Example injected note:

```text
OpenClaw外部联网查询返回的信息：广州: ⛅ +29°C (体感+29°C), 风↖4km/h, 湿度43%。
如果该信息已经回答了用户的实时查询，请优先简短转述该结果；除非用户明确询问画面/摄像头，否则不要描述当前画面。
用户原始输入：广州今天的天气怎么样？
```

中文论文口径：本文将 OpenClaw 抽象为外部联网信息源，而不是机器人动作决策 Agent。OpenClaw 查询结果通过文件协议返回 `p` 信息字段，并作为文本上下文注入主对话模块。最终播报内容、角色语气、表情和硬件行为仍由主对话模块与后端服务控制，因此外部网页内容不会直接驱动机器人动作。

English thesis wording: OpenClaw is abstracted as an external web-information source rather than a robot action-decision Agent. Its result is returned through a file protocol as the `p` information field and injected into the main dialogue module as text context. The final spoken answer, persona tone, expression and hardware behavior remain controlled by the main dialogue module and backend services, so external web content cannot directly drive robot actions.

## Output Post-Processing / 输出后处理流程

系统提示词没有要求大模型直接输出固定 JSON，也没有要求模型直接给出 `reply/emotion/action` 三元组。实际代码流程是先让 LLM 输出自然语言流，再由后端管线派生出 TTS、前端显示和动作字段。

The system prompt does not require the model to return a fixed JSON object or a direct `reply/emotion/action` tuple. In implementation, the LLM first emits a free-text stream, and the backend derives TTS text, display text and action metadata through post-processing.

```text
LLM free-text token stream
  -> sentence_divider
       split token stream into readable sentence chunks
  -> actions_extractor
       parse optional emotion tags or expression markers from each sentence
  -> display_processor
       build DisplayText for the frontend
  -> tts_filter
       remove tags/special characters and build TTS-safe text
  -> SentenceOutput(display_text, tts_text, actions)
  -> TTSTaskManager.speak(...)
       update ear motion from emotion_tags if present
       generate TTS audio
       send audio payload with display_text and actions to the kiosk frontend
```

对应的数据结构如下：

The derived runtime structures are:

| Structure | Role |
| --- | --- |
| `DisplayText` | 前端可显示文本，包含文本、说话者名称和可选头像 |
| `Actions` | 可选动作元数据，包含 `expressions`、`emotion_tags`、`pictures`、`sounds` |
| `SentenceOutput` | 每个句子级输出单元，包含 `display_text`、`tts_text` 和 `actions` |
| audio payload | WebSocket 发送给前端的音频与显示负载，包含 `audio`、`volumes`、`display_text`、`actions` |

因此论文中不应写成“大模型直接输出结构化多模态控制指令”。更准确的写法是：主对话模块生成带角色语气的自然语言；后处理管线从文本中提取可选情绪标签，并生成面向语音合成、前端显示和安全动作服务的运行时对象。若模型没有输出情绪标签，`actions` 可以为空，TTS 仍正常播报，前端可使用默认状态兜底。

Therefore the thesis should not state that the LLM directly outputs structured multimodal control commands. A more accurate description is: the main dialogue module generates persona-consistent natural language; the backend post-processing pipeline extracts optional emotion tags and derives runtime objects for TTS, frontend display and safe motion services. If the model does not emit emotion tags, `actions` can be empty; TTS still works and the frontend can fall back to default states.

舵机链路也不是由大模型直接给角度。耳朵动作只响应后端安全服务接收到的情绪标签或会话状态；人脸跟随舵机来自独立的摄像头检测与控制环路，并经过死区、平滑、限幅和释放 PWM 等安全约束。

Servo control is not generated as direct angles by the LLM. Ear motion responds only to backend-approved emotion tags or conversation states. Face tracking servos are driven by a separate camera detection and control loop with dead zone, smoothing, clamping and PWM-release safety constraints.

## Why This Boundary Matters / 边界设计原因

- It keeps persona consistency: only the main dialogue module writes the final answer.
- 它保证人设一致：最终回答只由主对话模块生成。
- It prevents context pollution: camera frames are not attached to unrelated weather or search questions.
- 它避免上下文污染：天气或搜索问题不会自动混入摄像头画面。
- It reduces hardware risk: external web results cannot command servos.
- 它降低硬件风险：外部网页结果不能命令舵机。
- It makes the thesis architecture clearer: external capabilities are typed context providers, while output effects are derived by backend post-processing.
- 它让论文架构更清晰：外部能力是有边界的上下文提供器，输出效果由后端后处理管线派生。
