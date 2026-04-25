# Hardware / 硬件

本目录保存小灰二次元萌宠机器人原型的硬件资料。

This directory contains hardware assets for the Xiaohui anime-pet robot prototype.

## Contents / 内容

- `bom.md`: 物料清单和主要模块。
- `bom.md`: bill of materials and major modules.
- SolidWorks files: 机械原型零件和装配文件。
- SolidWorks files: mechanical prototype parts and assemblies.
- `概念图.jpg`: 早期概念图。
- `概念图.jpg`: early concept image.

## Runtime Hardware Path / 运行时硬件链路

当前硬件控制实现在 Open-LLM-VTuber 后端中：

The current runtime hardware control is implemented in the Open-LLM-VTuber backend:

- PCA9685 共享管理器 / PCA9685 shared manager
- 面部追踪舵机服务 / face tracking servo service
- 耳朵动作服务 / ear motion service

OpenClaw 不直接驱动硬件。

OpenClaw does not directly drive hardware.
