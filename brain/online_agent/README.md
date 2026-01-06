# Online Agent

基于语音交互的智能助手系统。

## 📋 环境要求

* OS: Linux (Raspberry Pi)
* Python: 3.10+

## 🚀 快速开始

### 1. 创建虚拟环境

```bash
python3 -m venv venv
source venv/bin/activate
```

### 2. 安装系统依赖

```bash
sudo apt-get update
sudo apt-get install portaudio19-dev libespeak1 mpg123
```

### 3. 安装 Python 依赖

```bash
pip install -r requirements.txt
```

### 4. 下载 Vosk 模型

从 [Vosk Models](https://alphacephei.com/vosk/models) 下载中文模型，解压到项目目录。

### 5. 配置

编辑 `config.py` 设置：
- `API_KEY`: DeepSeek API 密钥
- `MIC_ID`: 麦克风设备 ID
- `SAMPLE_RATE`: 采样率

### 6. 测试麦克风

```bash
python tools/check_mic.py
```

### 7. 运行

```bash
python main.py
```

## 📦 依赖说明

| 包名 | 版本 | 用途 |
|------|------|------|
| edge-tts | >=7.0.0 | 微软 Edge 语音合成 |
| pygame | >=2.6.0 | 眼睛动画显示 |
| vosk | >=0.3.45 | 离线语音识别 |
| pyaudio | >=0.2.14 | 麦克风音频输入 |
| openai | >=2.0.0 | DeepSeek API 调用 |

## 📁 项目结构

```
online_agent/
├── main.py          # 主程序入口
├── config.py        # 配置文件
├── requirements.txt # Python 依赖
├── modules/
│   ├── brain.py     # LLM 对话模块
│   ├── mouth.py     # TTS 语音合成
│   └── eyes.py      # 眼睛动画显示
└── tools/
    └── check_mic.py # 麦克风测试工具
```
