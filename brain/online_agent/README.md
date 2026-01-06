# Online Agent

## 📋 环境要求
* OS: Linux / MacOS / WSL2
* Python: 3.10

## 🚀 快速开始

### 1. 搭建虚拟环境
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

### 4. 测试麦克风
```bash
python tools/check_mic.py
```

### 5. 运行
```bash
python main.py
```

## 📦 依赖包
- edge-tts: 语音合成
- pygame: 眼睛动画显示
- vosk: 语音识别
- pyaudio: 麦克风输入
- openai: DeepSeek API
