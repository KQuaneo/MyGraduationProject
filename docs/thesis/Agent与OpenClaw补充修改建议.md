# Agent 与 OpenClaw 补充修改建议

本文档针对 `/home/raspberrypi/Desktop/MyGraduationProject/初稿.docx` 的当前内容，给出 Agent 和 OpenClaw 相关补充方案。核心原则是：主线论文仍以当前稳定运行的 Open-LLM-VTuber kiosk 系统为准；Agent 写成系统的认知决策抽象层；OpenClaw 写成外部智能体主脑接入原型和后续扩展接口，不要写成当前稳定主链路已经依赖 OpenClaw。

## 一、当前初稿的主要缺口

初稿已经覆盖了语音唤醒、视觉快照、Qwen-VL、多模态交互、TTS、本地播放、表情状态机、PCA9685 和人脸追踪，但 Agent 部分偏弱：

1. 摘要和关键词没有突出“智能体”或“Agent 决策层”。
2. 第二章缺少“智能体、工具调用、MCP 或动作决策”的技术基础。
3. 第三章只在总体架构里一句话提到 Agent 抽象，没有展开“感知输入如何进入 Agent，Agent 如何输出文本、情绪、动作”的链路。
4. OpenClaw 当前没有进入主运行链路，但项目中存在 `brain/online_agent/main_agent.py`、`brain/online_agent/modules/brain_agent.py` 和 `openclaw_agent` 工作区，可作为“外部智能体主脑接入原型”写入论文。
5. 第四章测试部分没有体现 Agent 或 OpenClaw 接口验证。

## 二、建议改论文题目和关键词

当前题目“二次元萌宠具身智能系统研发”可以保留。如果想更明确体现 Agent，可改为：

> 二次元萌宠具身智能体系统研发

或：

> 基于树莓派的二次元萌宠具身智能体系统设计与实现

关键词建议改为：

> 具身智能体；二次元萌宠；多模态交互；树莓派；Agent；人脸追踪

如果老师更偏机器人方向，关键词也可以写：

> 具身智能；智能体；多模态交互；树莓派；舵机控制

## 三、摘要建议补一句 Agent

在中文摘要中，建议把原来的：

> 结合二次元萌宠外观、语音唤醒、视觉上下文采集、多模态大模型推理、语音合成、本地音频播放、前端表情状态机以及PCA9685舵机控制等环节

改成：

> 结合二次元萌宠外观、语音唤醒、视觉上下文采集、Agent认知决策、多模态大模型推理、语音合成、本地音频播放、前端表情状态机以及PCA9685舵机控制等环节

再补一两句：

> 系统在后端引入 Agent 抽象层，将语音转写文本、视觉图像上下文和会话历史封装为统一输入，由 Agent 负责组织模型调用、维护短期对话记忆，并将模型输出转换为可播报文本、表情标签和可选动作指令。针对后续扩展，本文还设计了 OpenClaw 外部智能体主脑接入原型，通过文件通信方式将机器人语音输入发送给 OpenClaw Agent，并约定以 action、reply、emotion 三元 JSON 结果返回，从而为工具调用、主动规划和动作执行提供接口基础。

注意：如果答辩时没有跑通 OpenClaw，不要在摘要里写“实现并验证完整 OpenClaw 闭环”，写“设计原型”更稳。

## 四、目录结构建议

建议把第二章增加一节，第三章增加一节，第四章增加一小节。修改后目录可以这样：

```text
第二章 系统相关技术基础
2.1 大语言模型与视觉语言模型
2.2 智能体架构与工具调用机制
2.3 语音识别、语音活动检测与语音合成
2.4 WebSocket实时通信与前端交互
2.5 树莓派、摄像头与PCA9685舵机控制
2.6 本章小结

第三章 二次元萌宠具身智能系统设计
3.1 系统需求分析
3.2 系统总体架构设计
3.3 Agent认知决策层设计
3.4 语音唤醒与对话流程设计
3.5 视觉上下文采集与触发策略设计
3.6 表情生成机制与本地音频播放设计
3.7 硬件系统与电气连接设计
3.8 人脸追踪算法设计
3.9 PCA9685舵机控制与安全策略
3.10 OpenClaw外部智能体接入原型设计
3.11 本章小结

第四章 系统实现与测试
4.1 开发与运行环境
4.2 后端服务实现
4.3 Agent与动作决策接口实现
4.4 前端kiosk界面实现
4.5 语音与视觉功能测试
4.6 系统性能指标测试
4.7 舵机控制与硬件安全测试
4.8 OpenClaw接口原型验证
4.9 系统运行问题与优化
4.10 本章小结
```

如果担心章节变太多，也可以不单独开 `3.10` 和 `4.8`，而是把 OpenClaw 放到 `3.3` 和 `4.3` 里面。

## 五、第二章可新增内容：智能体架构与工具调用机制

建议插入到“大语言模型与视觉语言模型”之后。

```text
2.X 智能体架构与工具调用机制

智能体（Agent）是在大语言模型基础上进一步封装感知输入、会话记忆、工具调用和动作输出的系统结构。与单次问答模型不同，Agent 不仅负责生成自然语言回复，还需要根据输入上下文判断是否调用外部工具、是否读取视觉信息、是否触发执行机构，以及如何将模型结果转换为系统可执行的控制信号。对于具身智能系统而言，Agent 层是连接“认知推理”和“实体动作”的关键中间层。

本系统中，Open-LLM-VTuber 提供了基础的 Agent 抽象。后端将用户语音转写文本、可选摄像头图像和会话历史封装为 BatchInput，再交给 BasicMemoryAgent 处理。BasicMemoryAgent 内部维护短期对话记忆，并通过统一的 LLM 接口调用视觉语言模型。模型输出经过分句、特殊标签过滤、动作标签提取和显示文本处理后，进一步进入 TTS、表情显示和硬件动作模块。该结构使系统不需要在 WebSocket 层直接处理模型细节，而是通过 Agent 层统一管理多模态输入与自然语言输出。

工具调用是 Agent 扩展能力的重要方式。当大模型仅依靠内部参数无法完成任务时，可以通过 Function Calling 或 MCP 等机制调用外部工具，例如时间查询、网络搜索、设备控制或机器人动作接口。Open-LLM-VTuber 中的 mcpp 模块包含 ToolManager、ToolAdapter 和 ToolExecutor 等组件，可将 MCP Server 暴露的工具转换为 OpenAI 或 Claude 兼容的函数调用格式，并在模型产生工具调用请求后执行对应工具。当前稳定部署中该功能默认关闭，但其结构为后续接入设备控制、日程查询和主动任务规划提供了扩展基础。

在本文的具身萌宠场景下，Agent 输出不应只被理解为一句回答，而应被拆分为三个层面：第一是 reply，即需要播报给用户的自然语言内容；第二是 emotion，即驱动前端表情或耳朵动作的情绪状态；第三是 action，即面向底盘、头部或其他执行机构的动作意图。通过将大模型输出约束为结构化结果，系统可以从普通语音问答扩展为“感知—认知—表达—执行”的具身智能体闭环。
```

## 六、第三章可新增内容：Agent认知决策层设计

建议放在总体架构后面，作为 `3.3`。

```text
3.X Agent认知决策层设计

Agent认知决策层位于语音识别、视觉快照和模型接口之间，是系统从多模态输入到表情、语音和动作输出的核心组织模块。该层的输入包括三类信息：一是由ASR模块得到的用户文本；二是视觉触发策略附加的摄像头快照；三是短期会话历史和角色提示词。输出则包括可朗读文本、情绪标签和可选动作意图。

本文将Agent层划分为输入构造、模型推理、输出解析和执行分发四个步骤。输入构造阶段，系统将用户文本封装为TextSource.INPUT；当视觉意图判断函数命中时，将后端摄像头快照编码为data:image/jpeg;base64格式，并作为ImageData加入BatchInput。模型推理阶段，BasicMemoryAgent将BatchInput转换为OpenAI兼容的消息格式，并调用Qwen-VL模型。输出解析阶段，系统通过sentence_divider将流式文本切分为适合TTS播放的短句，通过actions_extractor保留模型输出中的情绪或动作标签，通过display_processor得到前端显示文本。执行分发阶段，文本送入TTS管理器生成语音，情绪标签送入前端表情状态机，动作标签可进一步映射到底盘或耳朵舵机服务。

这种设计的优点是降低模块耦合度。WebSocketHandler只负责连接、音频缓存和唤醒状态，不直接关心模型类型；conversation_handler只负责组织对话链路，不直接控制前端表情或舵机；Agent层则集中承担会话记忆、模型调用和输出语义解析。后续如果需要替换模型、开启MCP工具调用、加入长期记忆或接入OpenClaw外部主脑，可以优先在Agent层扩展，而不必重写语音、视觉和前端模块。
```

可配一个表：

```text
表3-X Agent层输入输出关系

输入/输出项        来源或去向                 作用
用户文本           ASR或文本输入               表达用户意图
图像上下文         后端摄像头快照              支持视觉问答
会话历史           BasicMemoryAgent.memory     保持短期上下文
角色提示词         conf.yaml persona_prompt    约束回复风格
reply              TTS管理器                   生成语音回复
emotion            表情状态机/耳朵动作服务     驱动情绪反馈
action             底盘/外部动作执行模块       执行具身动作
```

## 七、第三章可新增内容：OpenClaw外部智能体接入原型

建议写成“原型设计”，不要写成“当前主系统已采用”。依据来自：

- `brain/online_agent/main_agent.py`
- `brain/online_agent/modules/brain_agent.py`
- `openclaw_agent/AGENTS.md`
- `openclaw_config.json`

可直接粘贴：

```text
3.X OpenClaw外部智能体接入原型设计

除Open-LLM-VTuber内部的BasicMemoryAgent外，本文还设计了OpenClaw外部智能体主脑接入原型，用于探索更强的工具调用、长期记忆和主动任务处理能力。OpenClaw本身作为独立Agent运行环境，具备工作区、记忆文件、工具说明和本地Gateway配置。为了避免直接将机器人主程序与外部Agent进程强耦合，本文采用轻量文件通信方式设计中间层。

在原型方案中，机器人主程序通过brain_agent模块与OpenClaw Agent通信。用户语音经过本地ASR识别后，主程序将文本写入/tmp/robot_input.txt；外部Agent读取该文件并完成意图理解、工具调用或任务规划；随后Agent将结构化结果写入/tmp/robot_output.json；机器人主程序读取结果并根据字段执行动作、表情和语音反馈。通信过程中使用/tmp/robot_brain.lock作为简单互斥锁，避免多轮输入同时写入造成冲突。

OpenClaw原型约定输出JSON包含action、reply和emotion三个字段。其中action表示动作意图，例如look、scan、shake、turn_away或none；reply表示需要播报的简短回复；emotion表示表情状态，例如happy、sad、angry、surprise、thinking或neutral。当action为look时，机器人可进一步调用视觉模块分析当前画面；当action为运动类动作时，可映射到底盘或耳朵舵机控制模块。该设计使自然语言指令不再只产生聊天文本，而是可以被转换为具身动作计划。

需要说明的是，当前稳定kiosk系统仍以Open-LLM-VTuber内部Agent和后端视觉快照链路为主，OpenClaw模块主要作为外部智能体主脑的接口预研。由于硬件安全和系统稳定性优先，本文未将OpenClaw作为最终稳定运行链路的强依赖，而是保留其作为后续扩展方向。
```

可配一个流程图：

```text
用户语音
  ↓
ASR转写
  ↓
brain_agent写入 /tmp/robot_input.txt
  ↓
OpenClaw Agent读取并规划
  ↓
写入 /tmp/robot_output.json
  ↓
机器人主程序解析 action/reply/emotion
  ↓
TTS播报 + 表情更新 + 可选动作执行
```

## 八、第四章可新增内容：Agent与动作决策接口实现

建议放到后端服务实现之后。

```text
4.X Agent与动作决策接口实现

在Open-LLM-VTuber后端中，Agent由AgentFactory根据配置创建。当前配置中conversation_agent_choice为basic_memory_agent，LLM provider为openai_compatible_llm。BasicMemoryAgent接收BatchInput后，将文本和可选图像转换为OpenAI兼容的messages结构，并调用DashScope兼容接口中的Qwen-VL模型。由于系统需要语音播报，Agent输出会经过分句处理，使较长回答被拆分为更适合TTS播放的短句。

BasicMemoryAgent内部维护_memory列表保存短期会话上下文，支持从历史记录加载对话，并在用户打断时向会话中加入中断提示。该机制使系统在连续对话中可以保留上下文，同时又能在用户打断AI回复时及时调整后续输出。对于具身交互终端而言，中断处理十分重要，因为用户往往会在AI尚未说完时发出新指令。

系统还保留了MCP工具调用扩展结构。ToolAdapter负责从启用的MCP服务器获取工具定义并转换为模型可识别的函数调用格式，ToolExecutor负责解析模型产生的工具调用并执行对应工具。当前conf.yaml中use_mcpp为false，因此稳定部署未启用外部工具调用；但代码结构已经支持在后续开启time、ddg-search或自定义机器人动作工具。本文将该部分作为Agent扩展能力的实现基础。
```

## 九、第四章可新增内容：OpenClaw接口原型验证

如果你还没有正式跑通 OpenClaw 控制机器人，建议用“接口原型验证”这个标题，而不是“功能测试通过”。

```text
4.X OpenClaw接口原型验证

OpenClaw接口原型主要验证机器人主程序与外部Agent之间的数据协议是否清晰。brain_agent模块定义了/tmp/robot_input.txt、/tmp/robot_output.json和/tmp/robot_brain.lock三个通信文件。主程序调用chat_with_brain(user_text)后，模块先尝试通过文件通信等待外部Agent返回结构化结果；若超时或返回内容不是合法JSON，则切换到备用LLM调用路径，保证机器人不会因外部Agent不可用而完全失效。

原型验证中，可使用“你好呀”“向右转”“你看到了什么”等输入检查JSON字段完整性。理想返回结果应包含action、reply和emotion字段。例如用户询问视觉问题时，action应为look，reply可为“让我看看”，emotion可为thinking或happy；用户发出动作指令时，action应映射为对应动作，reply保持简短口语化。机器人主程序读取结果后，根据action决定是否调用视觉分析或底盘动作，根据emotion更新眼睛和耳朵状态，根据reply进行TTS播报。

该原型说明OpenClaw可以作为系统的外部认知扩展层，但在最终稳定版本中仍需解决进程常驻、超时恢复、动作安全白名单、硬件互锁和日志追踪等问题。因此本文将OpenClaw接入定位为后续增强智能体能力的预研模块。
```

可加表：

```text
表4-X OpenClaw接口原型测试项

测试项             输入示例           预期结果
普通对话           你好呀             返回reply和neutral/happy情绪
动作指令           向右转             返回运动类action
视觉请求           你看到了什么       返回look动作并触发视觉模块
非法输出           非JSON内容          进入备用路径或错误处理
超时               Agent未写输出文件   返回备用LLM结果
```

## 十、结论和展望建议改法

结论中“论文工作总结”建议加一句：

```text
在系统软件结构上，本文将传统问答模型封装为Agent认知决策层，使语音、视觉、会话历史和角色提示词能够被统一组织，并将模型输出进一步映射为语音、表情和动作意图。该设计为系统从多模态问答终端扩展为具备工具调用和动作规划能力的具身智能体提供了基础。
```

展望中建议把第五点改得更具体：

```text
第五，引入长期记忆、工具调用和外部Agent主脑机制。后续可在Open-LLM-VTuber的MCP工具调用框架上注册机器人动作工具，也可进一步完善OpenClaw接入，使系统能够根据自然语言主动规划多步任务，例如先观察环境、再判断目标、最后执行转向或表情动作，从而从一次性问答系统发展为持续运行的具身智能体。
```

## 十一、答辩口径建议

如果老师问“你的 Agent 到底在哪里”，可以这样回答：

```text
我的系统里有两层Agent设计。第一层是当前稳定运行的Open-LLM-VTuber内部BasicMemoryAgent，它负责把语音转写文本、可选视觉快照和会话历史组织成模型输入，再把模型输出转成可播报文本和表情标签，这是主系统实际使用的Agent层。第二层是我预研的OpenClaw外部Agent主脑，它通过文件通信协议返回action、reply、emotion三元结构，用于探索工具调用和动作规划。但考虑到答辩前硬件稳定性和PCA9685安全问题，我没有把OpenClaw作为最终稳定链路的强依赖，而是作为扩展接口保留。
```

如果老师问“OpenClaw为什么没用上”，可以这样回答：

```text
OpenClaw更适合作为长期记忆、工具调用和多步规划的外部主脑，但当前系统首先要保证树莓派kiosk的语音、视觉、表情和硬件安全稳定。由于PCA9685硬件曾出现烧毁风险，我把最终演示链路收敛到稳定的Open-LLM-VTuber内部Agent，并把OpenClaw接入保留为原型和后续扩展方向。这样可以避免为了展示Agent而牺牲系统稳定性。
```

## 十二、不建议这样写

不要写：

> 本系统已完整接入OpenClaw并实现自主规划和机械抓取。

因为当前项目里没有看到机械爪抓取闭环，也没有看到OpenClaw成为当前稳定kiosk主链路。

也不要写：

> OpenClaw控制PCA9685完成抓取。

当前硬件记录显示PCA9685旧板烧毁，且当前配置建议关闭face_tracking和ear_motion。可以写“预留动作执行接口”或“外部智能体主脑接入原型”。

## 十三、可以强调的真实工作量

论文可以强调这些真实、有依据的工作：

1. Open-LLM-VTuber内部Agent抽象：`BasicMemoryAgent`、`BatchInput`、会话记忆、流式输出、分句、情绪/动作标签处理。
2. MCP工具调用框架：`ToolManager`、`ToolAdapter`、`ToolExecutor`、`mcp_servers.json`，但当前稳定配置 `use_mcpp: false`。
3. OpenClaw原型：`brain_agent.py` 通过 `/tmp/robot_input.txt` 和 `/tmp/robot_output.json` 通信，输出 `action/reply/emotion`。
4. `main_agent.py` 的动作决策流程：ASR唤醒后调用 `chat_with_brain()`，再根据 `action` 调用底盘或视觉，根据 `emotion` 更新表情/耳朵，根据 `reply` 播报。
5. 当前主系统的工程取舍：为了稳定展示，OpenClaw作为扩展接口，不强行并入最终稳定演示链路。
