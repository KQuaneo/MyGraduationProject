# Runtime Architecture

## Boundary

The current production system is centered on the Open-LLM-VTuber backend/frontend fork. Root-level files provide integration, hardware notes and documentation.

OpenClaw is not the main robot brain anymore. It is a live web-query sidecar:

```json
{"p": "short realtime information"}
```

No action, emotion or visual trigger fields are accepted from OpenClaw in the final runtime path.

## Request Flow

1. The Chromium kiosk frontend captures microphone audio and maintains visible expression state.
2. The backend receives audio/text over WebSocket.
3. Wake-word gating keeps the robot from responding to ambient speech.
4. ASR converts speech to text.
5. The visual-trigger detector decides whether to attach a backend camera snapshot.
6. OpenClaw is called only for live-query inputs such as weather, news, latest information or web search.
7. The main VTuber Agent builds the final response with persona, memory, optional image and optional `p` information.
8. TTS audio is generated and played locally on the Raspberry Pi.
9. Frontend expressions and backend ear/servo hooks follow the main conversation state.

## Responsibility Split

| Module | Responsibility |
| --- | --- |
| Open-LLM-VTuber backend | conversation orchestration, ASR, TTS, camera snapshots, model calls, hardware services |
| Open-LLM-VTuber frontend | kiosk UI, microphone capture, visible expression fallback |
| OpenClaw bridge | live weather/news/web-query information only |
| PCA9685 services | face tracking and ear motion PWM output |
| Local model experiment | future offline action-intent parsing research, not production |

## Visual Context Rule

Camera images are attached only when the user explicitly asks about the scene, camera, image, screen or currently visible objects. Weather or ordinary knowledge questions must not receive camera context.

## Hardware Safety

Servo behavior is kept behind backend services and configuration gates. External tools cannot directly command hardware. This prevents web-query output from turning into uncontrolled motion.
