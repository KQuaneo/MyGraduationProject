# Local agent

本部分旨在构建一个基于deepseek api的agent，输出格式为json，来控制多外设联动
语音转文字模型使用开源模型Vosk[vosk-model-small-cn-0.22](https://alphacephei.com/vosk/models))

## 📋 环境要求 / Prerequisites

* **OS**: Linux / MacOS / WSL2
* **Python**: 3.10
* **工具**: [uv](https://github.com/astral-sh/uv) (极速 Python 包管理器)

## 🚀 快速开始 / Quick Start

请严格按照以下顺序执行命令，以确保虚拟环境配置正确。

### 1. 项目初始化
创建并进入工作目录：
```bash
mkdir -p ~/brain/online_agent
cd ~/brain/online_agent
```

### 2.搭建环境
```bash
uv venv --python 3.10
source .venv/bin/activate
sudo apt-get update
sudo apt-get install portaudio19-dev libespeak1
```

### 3.安装依赖
```bash
uv pip install edge-tts pygame vosk pyaudio openai 
```

### 4.测试麦克风
```bash
python check_mic.py
```

### 5.运行总文件
```bash
python main.py
```
