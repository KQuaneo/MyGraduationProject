# 流式对话优化文档

## 📋 概述

针对原系统对话延迟高的问题，创建了流式优化版本，实现**边生成边说**，显著降低用户感知延迟。

## 🚀 优化效果

| 指标 | 阻塞式 | 流式 | 提升 |
|------|--------|------|------|
| 首句延迟 | ~2.6s | ~1.9s | **28%↓** |
| 用户体验 | 等待完整回复 | 边生成边听 | **显著改善** |

## 📁 文件结构

```
online_agent/
├── main.py                    # 原版 (保留)
├── main_streaming.py          # ⭐ 流式优化版 (推荐)
├── modules/
│   ├── brain.py               # 原版大脑 (保留)
│   ├── streaming_brain.py     # ⭐ 流式大脑模块
│   └── ...
```

## 🔧 核心优化点

### 1. 流式 LLM 调用
```python
# 原版 - 阻塞等待完整回复
response = client.chat.completions.create(..., stream=False)
content = response.choices[0].message.content  # 等待全部生成

# 流式版 - 增量接收
response = client.chat.completions.create(..., stream=True)
for chunk in response:
    content = chunk.choices[0].delta.content  # 逐字接收
```

### 2. 句子级 TTS 触发
- 收到完整句子立即播放，无需等待全部内容
- TTS 队列管理器后台播放，不阻塞 LLM 生成

### 3. 头部 JSON 优先解析
```
LLM 输出格式:
{"action": "wiggle", "emotion": "happy"}  ← 第一行立即解析，执行动作
你好呀！我是你的智能陪伴玩偶...          ← 第二行起逐句播放
```

## 🎮 使用方法

### 启动流式版本
```bash
cd /home/raspberrypi/Desktop/MyGraduationProject/brain/online_agent
source .venv/bin/activate
python main_streaming.py
```

### 切换回原版
```bash
python main.py  # 使用原版阻塞式
```

## 📊 流程对比

### 原版流程 (阻塞式)
```
用户说话 → [等待ASR] → [等待LLM完整生成] → [等待TTS] → 播放
     ↑___________________________________________↓
                    总延迟 = 各阶段之和
```

### 流式流程 (优化)
```
用户说话 → [ASR] → LLM开始生成 → 收到首句 → 立即播放
                              ↓
                         继续生成 → 收到次句 → 追加播放
                              ↓
                              ...
```

## ⚙️ 配置调优

### 系统提示词优化
流式版本使用特殊格式提示词，要求 LLM 先输出 JSON 头部：
```
{"action": "动作", "emotion": "情绪"}
回复内容...
```

### 温度参数
- 流式版：`temperature=0.3` (稍高，增加流畅度)
- 原版：`temperature=0.1` (更低，保证格式稳定)

## 🔄 兼容性

- `streaming_brain.py` 保留 `chat_with_brain()` 函数，兼容旧接口
- 原版 `main.py` 不受影响，可随时切换

## 📝 注意事项

1. **网络要求**：流式对网络稳定性要求稍高，弱网环境可能卡顿
2. **TTS 衔接**：句子间可能有微小停顿，可通过调整分割逻辑优化
3. **长回复**：流式优势在长回复场景更明显，短回复差异不大

## 🐛 故障排查

### 流式不生效
- 检查 API 是否支持流式 (DeepSeek 支持)
- 查看日志是否有 `[LLM] 流式思考` 字样

### TTS 播放混乱
- 检查 `TTSQueueManager` 是否正常启动
- 查看是否有 `🔊 流式:` 日志输出

## 🎯 后续优化建议

1. **预加载 TTS**：预测用户意图，提前准备常用回复
2. **本地 LLM**：部署本地小模型处理简单指令，零网络延迟
3. **WebSocket 优化**：使用 WebSocket 替代 HTTP SSE，进一步降低延迟
