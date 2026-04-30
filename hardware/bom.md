# Bill of Materials (BOM) / 硬件物料清单

本表公开原型机的模块级硬件组成。实际购买价格、订单来源和个人收货信息不放入公开仓库；论文成本分析可根据个人购买记录单独填写。

This table publishes the module-level hardware composition. Actual purchase prices, order links and personal shipping information are not stored in the public repository. Thesis cost analysis can be filled from private purchase records.

| Component | 中文名称 | Function | Quantity | Public Notes |
| --- | --- | --- | ---: | --- |
| Raspberry Pi | 树莓派主控 | Runs backend, kiosk page, local audio playback and hardware services | 1 | Main controller |
| Display | 显示屏 | Shows the static/anime expression UI | 1 | Connected through the local kiosk setup |
| Camera module | 摄像头 | Provides backend snapshots and face-position input | 1 | Used only when visual context is needed |
| USB microphone or USB sound card | USB 麦克风/声卡 | Captures user voice and provides audio I/O | 1 | Device choice may vary |
| Speaker | 扬声器 | Plays local TTS output | 1 | Driven by Raspberry Pi audio output |
| PCA9685 servo driver | PCA9685 舵机驱动板 | Generates PWM signals for servos over I2C | 1 | Hardware actions are backend-gated |
| Servo for face/base tracking | 面部/底座跟随舵机 | Rotates the visible body/head/base toward detected face | 1 | Public channel mapping: channel 0 |
| Left ear servo | 左耳舵机 | Provides ear motion feedback | 1 | Public channel mapping: channel 2 |
| Right ear servo | 右耳舵机 | Provides ear motion feedback | 1 | Public channel mapping: channel 3 |
| External servo power supply | 舵机外部供电 | Powers servos separately from Raspberry Pi logic power | 1 | Must share common ground with Raspberry Pi/PCA9685 |
| Jumper wires and connectors | 杜邦线/连接线 | Connects I2C, common ground and servo signal lines | several | Verify polarity before power-on |
| Mechanical shell and brackets | 机械外壳与连接件 | Mounts display, ears, servos and base structure | 1 set | See SolidWorks assets in this directory |

## Wiring Principles / 接线原则

- Raspberry Pi `3.3V` connects to PCA9685 `VCC` logic power only.
- 树莓派 `3.3V` 只连接 PCA9685 的 `VCC` 逻辑侧。
- Servo power connects to PCA9685 `V+`, not to Raspberry Pi `3.3V`.
- 舵机动力电源连接 PCA9685 的 `V+`，不要接树莓派 `3.3V`。
- Raspberry Pi, PCA9685 and external servo power must share common ground.
- 树莓派、PCA9685 和外部舵机电源必须共地。
- OpenClaw and web-query output never drive hardware directly.
- OpenClaw 和联网查询结果不能直接驱动硬件。
