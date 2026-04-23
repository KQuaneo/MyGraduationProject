# 基于树莓派的多模态语音视觉交互AI伴侣系统设计与实现

## 摘要
随着大语言模型、多模态视觉理解和嵌入式计算平台的发展，本文设计并实现一套运行于树莓派kiosk环境的多模态语音视觉交互AI伴侣系统。系统整合语音唤醒、ASR、VAD、摄像头快照、Qwen-VL视觉语言模型、TTS、本地音频播放、前端表情显示和可选舵机控制，形成完整交互闭环。

关键词：多模态交互；树莓派；视觉语言模型；语音唤醒；AI伴侣系统

## 目录
第一章 绪论
第二章 系统相关技术基础
第三章 多模态AI伴侣系统设计
第四章 系统实现与测试
结论
参考文献
致谢

## 第一章 绪论
### 1.1 引言
### 1.2 研究背景与意义
### 1.3 国内外研究现状
### 1.4 本文主要工作
### 1.5 论文结构

## 第二章 系统相关技术基础
### 2.1 大语言模型与视觉语言模型
### 2.2 语音识别、语音活动检测与语音合成
### 2.3 WebSocket实时通信与前端交互
### 2.4 树莓派、摄像头与PCA9685舵机控制
### 2.5 本章小结

## 第三章 多模态AI伴侣系统设计
### 3.1 系统需求分析
### 3.2 系统总体架构设计
### 3.3 语音唤醒与对话流程设计
### 3.4 视觉上下文采集与触发策略设计
### 3.5 前端表情与本地音频播放设计
### 3.6 硬件执行机构安全设计
### 3.7 本章小结

## 第四章 系统实现与测试
### 4.1 开发与运行环境
### 4.2 后端服务实现
### 4.3 前端kiosk界面实现
### 4.4 语音与视觉功能测试
### 4.5 舵机控制与硬件安全测试
### 4.6 系统运行问题与优化
### 4.7 本章小结

## 结论
### 1. 论文工作总结
### 2. 工作展望

## 参考文献
[1] Open-LLM-VTuber Project. Open-LLM-VTuber: Talk to LLM with voice interaction and Live2D frontend[EB/OL]. https://github.com/Open-LLM-VTuber/Open-LLM-VTuber.
[2] Vaswani A, Shazeer N, Parmar N, et al. Attention Is All You Need[C]. Advances in Neural Information Processing Systems, 2017.
[3] OpenAI. GPT-4 Technical Report[R]. 2023.
[4] Radford A, Kim J W, Hallacy C, et al. Learning Transferable Visual Models From Natural Language Supervision[C]. ICML, 2021.
[5] Raspberry Pi Ltd. Raspberry Pi Documentation[EB/OL]. https://www.raspberrypi.com/documentation/.
[6] NXP Semiconductors. PCA9685 16-channel, 12-bit PWM Fm+ I2C-bus LED controller Datasheet[Z].
[7] FastAPI Documentation[EB/OL]. https://fastapi.tiangolo.com/.
[8] Python Software Foundation. Python 3 Documentation[EB/OL]. https://docs.python.org/3/.

## 致谢