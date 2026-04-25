# Codex Handoff

## Repo Layout

- Parent repo: `/home/raspberrypi/Desktop/MyGraduationProject`
- VTuber backend repo: `/home/raspberrypi/Desktop/MyGraduationProject/Open-LLM-VTuber`
- Frontend repo/submodule: `/home/raspberrypi/Desktop/MyGraduationProject/Open-LLM-VTuber/frontend`

## Git State

Latest local commits at handoff:

- Parent repo: this handoff file is being committed in the parent repo after the nested repo commits below; run `git log -1 --oneline` in `/home/raspberrypi/Desktop/MyGraduationProject` for the exact parent hash.
- `Open-LLM-VTuber`: `5dcf828` `fix: stabilize kiosk agent and tts flow`
- `frontend`: `34eba72` `fix: stabilize static expression playback`

Recent `Open-LLM-VTuber` commits from this continuation:

- `5dcf828` `fix: stabilize kiosk agent and tts flow`
- `70eb6b2` `chore: update frontend expression styles`
- `81c5009` `fix: tune ear motion and vision triggers`
- `73483cc` `feat: add ear servo emotion hooks`
- `e57a5b7` `feat: switch chassis tracking to dnn mil`
- `704511e` `feat: add chassis target tracking service`
- `f418c9c` `chore: update frontend hotfix snapshot`
- `6283ac7` `feat: add spoken wake word acknowledgement`
- `22408cf` `fix: shorten mic mute after local playback`
- `8365168` `feat: add wake word gated voice chat`

Recent `frontend` commits from this continuation:

- `34eba72` `fix: stabilize static expression playback`
- `1a1dcbf` `fix: hide vad misfire notice`
- `3a3d62a` `feat: boost live2d talk motion intensity`

Git cleanliness should be re-checked at the next session rather than assumed.

Git object repair note from 2026-04-25:

- A failed/interrupted commit left 0-byte loose Git objects in the `frontend` and `Open-LLM-VTuber` object stores.
- `frontend` was repaired by moving HEAD back to `a77b679`, removing/recreating bad objects, then recommitting as `34eba72`.
- `Open-LLM-VTuber` was repaired by moving HEAD back to `70eb6b2`, moving 12 bad 0-byte objects to `/tmp/git-corrupt-objects-open-llm-vtuber-20260425180054`, then recommitting as `5dcf828`.
- Disk was very full during this work (`/dev/mmcblk0p2` around 98% used). If Git writes fail again, free disk space before committing.

Configured remotes/forks:

- Parent repo remote is user-owned and pushable.
- `Open-LLM-VTuber` remote points to user fork: `https://github.com/KQuaneo/Open-LLM-VTuber.git`
- `frontend` remote points to user fork: `https://github.com/KQuaneo/Open-LLM-VTuber-Web.git`
- In `Open-LLM-VTuber/.gitmodules`, frontend submodule URL was changed to the user fork and branch set to `codex-kiosk-audio-camera`.

## Main Goal Of Prior Work

This project was stabilized on a Raspberry Pi kiosk deployment. Main work focused on:

- making camera/VLM input usable without browser camera permission issues
- avoiding kiosk black-screen / display-drop behavior during thinking
- making speech work reliably with local playback
- preserving Live2D expressions and motions while audio is played locally on the host

## Current Runtime Model

### Service / Kiosk

- The app is typically run by a user systemd service:
  - `open-llm-vtuber.service`
- OpenClaw bridge is now also run by a user systemd service:
  - `openclaw-robot-bridge.service`
- Kiosk launcher script:
  - `/home/raspberrypi/Desktop/MyGraduationProject/Open-LLM-VTuber/scripts/open_llm_vtuber_kiosk.sh`
- Current kiosk launcher uses `/usr/lib/chromium/chromium` directly, not `/usr/bin/chromium`, because the wrapper injected a bad `--js-flags=--no-decommit-pooled-pages` flag.
- Current kiosk Chromium flags intentionally use `--disable-gpu --enable-unsafe-swiftshader --enable-webgl` for this Pi display setup.

Typical commands that were used:

```bash
systemctl --user restart open-llm-vtuber.service
systemctl --user restart openclaw-robot-bridge.service
systemctl --user restart 'app-open\x2dllm\x2dvtuber\x2dkiosk@autostart.service'
```

Server listens on:

- `http://0.0.0.0:12393`

Current observed runtime status on 2026-04-24 after fixes:

- `open-llm-vtuber.service`: active/running
- `openclaw-robot-bridge.service`: active/running
- `app-open\x2dllm\x2dvtuber\x2dkiosk@autostart.service`: active/running
- HDMI mode was corrected to `1024x600` using `xrandr`
- logs confirmed `PCA9685 shared instance initialized at 50Hz`
- logs confirmed `Ear motion service started | left_channel=2 right_channel=3`
- logs confirmed `Face tracking servo service started | channel=0 camera_index=0`

## OpenClaw / External Agent Bridge

OpenClaw is now integrated as an optional live web-query layer for Open-LLM-VTuber.

Current relationship:

- Open-LLM-VTuber remains the main conversation, persona, TTS, frontend, and camera orchestration layer.
- OpenClaw is called only for live web-query style requests before the main LLM response.
- The bridge communicates through a simple file protocol:
  - input: `/tmp/robot_input.txt`
  - output: `/tmp/robot_output.json`
- The expected OpenClaw output shape is:

```json
{
  "p": "简短中文联网信息"
}
```

Main files:

- `scripts/openclaw_robot_bridge.py`
- `docs/openclaw_vtuber_bridge.md`
- `Open-LLM-VTuber/src/open_llm_vtuber/conversations/openclaw_bridge.py`
- `Open-LLM-VTuber/src/open_llm_vtuber/conversations/conversation_handler.py`
- `Open-LLM-VTuber/src/open_llm_vtuber/conversations/single_conversation.py`
- `Open-LLM-VTuber/src/open_llm_vtuber/config_manager/system.py`
- `Open-LLM-VTuber/conf.yaml`

Current config block is under `system_config.openclaw_agent` in `Open-LLM-VTuber/conf.yaml`.

Current behavior:

- `enabled: true`
- `safe_mode: true`
- OpenClaw is now intentionally limited to live web-query style requests only.
- The current OpenClaw bridge should be used for weather/news/latest/search/web/online queries.
- Ordinary chat, vision, persona, camera reasoning, and hardware behavior should stay in the main VTuber agent.
- The current bridge prompt and normalizer only emit `p`; OpenClaw should not request robot actions, emotion changes, or camera context in the current demo.
- Non-live-query inputs are skipped by `should_query_openclaw()` in `Open-LLM-VTuber/src/open_llm_vtuber/conversations/openclaw_bridge.py`.

The formal user service is installed at:

- `/home/raspberrypi/.config/systemd/user/openclaw-robot-bridge.service`

It has been enabled and attached to the VTuber service:

- `systemctl --user enable openclaw-robot-bridge.service`
- `systemctl --user add-wants open-llm-vtuber.service openclaw-robot-bridge.service`
- the unit contains `PartOf=open-llm-vtuber.service`

Useful commands:

```bash
systemctl --user status openclaw-robot-bridge.service --no-pager
systemctl --user restart openclaw-robot-bridge.service
journalctl --user -u openclaw-robot-bridge.service -n 50 --no-pager
```

OpenClaw binary path:

- `/home/raspberrypi/.npm-global/bin/openclaw`

The OpenClaw default model was changed from an unavailable `zai/glm-5` setup to:

- `longcat/LongCat-Flash-Chat`

That was needed because the local OpenClaw config had a usable LongCat auth profile, while the ZAI profile lacked an API key.

### OpenClaw Memory / Prompt Sync

There are two separate memory systems:

- VTuber side: `BasicMemoryAgent` stores active conversation memory and can restore histories from `Open-LLM-VTuber/chat_history/<conf_uid>/<history_uid>.json`.
- OpenClaw side: local sessions are stored under `~/.openclaw/agents/main/sessions/`, and workspace memory lives under `~/.openclaw/workspace/memory/`.

Current design decision:

- sync VTuber persona/system prompt context into OpenClaw
- do **not** sync full VTuber chat history into OpenClaw

Reason:

- VTuber-LLM should remain the final voice/persona/conversation continuity layer.
- OpenClaw should act only as an external realtime information layer.
- Full chat-history sync would increase privacy leakage, duplicate memory, and context pollution risk.

`scripts/openclaw_robot_bridge.py` now reads `Open-LLM-VTuber/conf.yaml` on startup and injects:

- `character_config.character_name`
- `character_config.persona_prompt`

The bridge defaults to:

- `--session-mode isolated`

This gives each OpenClaw call a short isolated session id and avoids bloating a fixed `robot-vtuber-bridge.jsonl` session with repeated bridge prompts. Use `--session-mode persistent` only if explicitly experimenting with OpenClaw's own long-term behavior.

### OpenClaw Realtime Tests

End-to-end file protocol tests through the formal service worked.

Weather example:

```json
{"p": "广州: 🌩 +18°C (体感+18°C), 风↓19km/h, 湿度94%"}
```

News example also returned a short `最新新闻：...` style `p` value through the fallback Google News RSS path.

Important limitation:

- OpenClaw's built-in `web_search` tool reported missing Brave API key.
- The bridge script therefore includes direct fallback live-query logic for weather (`wttr.in`) and news (Google News RSS).
- If proper OpenClaw web search is desired later, configure Brave Search for OpenClaw instead of relying only on fallback logic.

## Current Local Runtime Config Notes

`Open-LLM-VTuber/conf.yaml` is intentionally git-ignored and was not committed because it is local runtime configuration and may contain local secrets/API keys.

Observed local values after the 2026-04-24 hardware test:

- `face_tracking.enabled: true`
- `ear_motion.enabled: true`
- `ear_motion.left_channel: 2`
- `ear_motion.right_channel: 3`
- `ear_motion.max_angle: 20`
- `openclaw_agent.enabled: true`
- `voice_wakeup.enabled: true`
- wake word variants include `小灰小灰`, `小辉小辉`, `小慧小慧`, `小惠小惠`, `小回小回`, and ASR misrecognitions `小许小开`, `小去小开`
- wake acknowledgement text is `我在`
- `tts_config.tts_model: piper_tts`
- `piper_tts.model_path: models/piper/zh_CN-huayan-medium.onnx`
- `piper_tts.length_scale: 1.18`
- `piper_tts.noise_scale: 0.55`
- `piper_tts.noise_w: 0.55`
- `basic_memory_agent.faster_first_response: false`
- `letta_agent.faster_first_response: false`

Reason for the TTS values:

- the previous `zh_CN-huayan-x_low` Piper model had a noticeably strange accent
- `zh_CN-huayan-medium` generated successfully and is more stable
- slowing speech and reducing noise/style variation reduced words blending together
- `TTSTaskManager._play_audio_locally()` now waits `0.18s` after each host-local audio playback segment to reduce glued-together phrase boundaries

## Vision / Camera Pipeline

The browser camera path was intentionally de-emphasized because it had been unreliable.

Current intended behavior:

- user does not need to use the frontend camera button
- backend grabs Raspberry Pi camera snapshots
- conversation requests attach a backend camera snapshot when the input is judged to be vision-related

Important detail:

- The system is not continuous video understanding.
- It uses snapshot-based vision at conversation time.

Related backend areas modified during earlier work:

- `src/open_llm_vtuber/conversations/conversation_handler.py`
- camera/backend helper and route files under `src/open_llm_vtuber/...`
- frontend hotfix disables browser video capture attempts

### Vision Intent Heuristic

There is heuristic logic so the model only receives camera images for vision-like prompts.

Examples that should trigger vision:

- `现在画面里有什么`
- `你看得见我吗`
- `你能看到什么`
- `我现在在干嘛`
- `我长什么样`
- `我手上拿了什么`
- `我手里拿着什么`
- `这个是什么`

Current heuristic note:

- earlier versions missed hand/object queries such as `我手上拿了什么`, so the visual-trigger keyword list was expanded
- if a vision-like question still fails to invoke VLM, inspect `should_attach_visual_context()` in `conversation_utils.py` first

Speech flow was also adjusted so for voice input, the system should first transcribe, then decide whether to attach camera input.

## LLM / API

Backend uses an OpenAI-compatible DashScope endpoint with Qwen-VL.

Important config direction:

- API key was moved out of hardcoded config and into environment-variable usage
- `conf.yaml` uses `${DASHSCOPE_API_KEY}`

The user previously exposed an old key in chat. Treat that key as compromised and rotate if needed.

## Persona / Prompt Style

The default assistant persona in `Open-LLM-VTuber/conf.yaml` is no longer the earlier cold / minimal style.

Current direction:

- the assistant should sound lively, warm, and slightly playful
- responses should still be short and readable aloud
- vision-related guardrails remain in place
- the model should not invent unseen visual details

If future behavior feels too flat or too chatty, check `character_config.persona_prompt` first before touching model or temperature settings.

## Voice Wakeup / Conversation Gating

Voice input is no longer always-open.

Current intended behavior:

- user must first say the wake word `小灰小灰`
- similar ASR spellings are accepted, e.g. `小辉小辉`, `小慧小慧`, `小惠小惠`, `晓辉晓辉`
- when the wake word is spoken by itself, the assistant should answer `我在`
- after wakeup, the system stays in an active conversational state for `20` seconds
- any additional speech during that active window extends the window again
- if there is `20` seconds of silence, voice gating resets and wakeup is required again

Important implementation detail:

- this gating happens on the backend after ASR transcription but before the normal conversation pipeline is entered
- ignored non-wakeup voice segments now explicitly send a reset signal so the frontend does not stay stuck in `Thinking...`
- the wake-word-only acknowledgement now uses the normal TTS / audio payload path instead of only showing text, so host-local audio and Live2D motion should still work

Main files involved:

- `Open-LLM-VTuber/src/open_llm_vtuber/websocket_handler.py`
- `Open-LLM-VTuber/src/open_llm_vtuber/conversations/conversation_utils.py`
- `Open-LLM-VTuber/src/open_llm_vtuber/config_manager/system.py`
- `Open-LLM-VTuber/conf.yaml`

## TTS / Audio

### Current Direction

The browser audio path had reliability issues, so host-local playback was introduced.

Current intended setup:

- TTS generates audio on backend
- Raspberry Pi host plays the reply audio locally via `pw-play`
- frontend still receives audio payload so Live2D can animate
- frontend-side AI audio is muted so it does not double-play or cause echo
- frontend muted playback timing is still operationally important because mic auto-stop / auto-reopen behavior follows that lifecycle

### Important Files

- `Open-LLM-VTuber/src/open_llm_vtuber/conversations/tts_manager.py`
- `Open-LLM-VTuber/frontend/frontend-hotfix.js`

### Why This Matters

At one point frontend animation broke because backend was sending `audio=None` when local playback was enabled.

That was fixed by restoring real audio payloads to the frontend while keeping browser playback muted.

Another timing issue was later found:

- backend had been waiting for local `pw-play` completion before sending audio payload to the frontend
- that caused the frontend to remain in mic-muted playback state too long, even after audible host playback had already ended

That was fixed by changing the order in `tts_manager.py`:

- send the real audio payload to frontend immediately
- then play the same audio locally on the host

If the mic again feels slow to reopen after speech, inspect `Open-LLM-VTuber/src/open_llm_vtuber/conversations/tts_manager.py` before tweaking VAD values.

### TTS Engine History

Several engines were tried:

- `edge-tts`
- local fallback / rough offline voice
- `Piper TTS`

At the time of last substantive audio work, the active direction was local/offline TTS plus host-local playback because browser playback and remote TTS had both caused problems at different times.

Check current `conf.yaml` and service logs before changing TTS again.

## Chassis Tracking

### Current Direction

Bottom chassis steering is now handled inside `Open-LLM-VTuber`, not only in the separate `brain` repo.

Current implementation direction:

- PCA9685-based servo output on channel `0`
- backend camera frames are reused from the shared camera service
- tracking now uses `DNN` face detection plus `MIL` tracker follow-up
- the older multi-source fallback approach (`person` / `face` / `motion`) was replaced because it caused unstable source hopping and visibly erratic steering

### Current Status

This feature is working but still needs tuning.

Observed state at handoff:

- `DNN + MIL` is live and loads correctly on this Raspberry Pi
- face-following is more coherent than the earlier multi-detector fallback logic
- however, the chassis can still turn a bit too far / overshoot
- recent tuning reduced overshoot by removing dynamic gain and lowering `max_step`, but it is not fully solved yet

Current active parameters in `Open-LLM-VTuber/conf.yaml` were recently tuned around:

- `kp: 4.2`
- `dead_zone: 0.06`
- `max_step: 2.2`
- `control_interval: 0.04`
- `target_x_offset: 0.0`

### Important Files

- `Open-LLM-VTuber/src/open_llm_vtuber/face_tracking_servo.py`
- `Open-LLM-VTuber/src/open_llm_vtuber/pca9685_manager.py`
- `Open-LLM-VTuber/src/open_llm_vtuber/server.py`
- `Open-LLM-VTuber/src/open_llm_vtuber/config_manager/system.py`
- `Open-LLM-VTuber/conf.yaml`

### DNN Model Files

These files are now checked into the `Open-LLM-VTuber` repo and expected at:

- `Open-LLM-VTuber/src/open_llm_vtuber/models/face_detection/deploy.prototxt`
- `Open-LLM-VTuber/src/open_llm_vtuber/models/face_detection/res10_300x300_ssd_iter_140000_fp16.caffemodel`

Important environment note:

- OpenCV on this Raspberry Pi does **not** provide `KCF`
- available tracker support was checked and `TrackerMIL_create()` works
- the current implementation therefore uses `MIL`, not `KCF`

### Runtime Notes

Hardware/runtime checks already confirmed during this continuation:

- `i2cdetect -y 1` showed PCA9685 at `0x40`
- `board`, `adafruit_pca9685`, `adafruit_motor.servo`, `cv2`, and `picamera2` all imported successfully under the real environment
- service logs showed successful startup of the chassis tracking service

One recurring operational issue:

- if `/backend-camera/stream.mjpg` is open in a browser, `systemctl --user restart open-llm-vtuber.service` can hang at `Waiting for connections to close`
- in that case, a forced restart was sometimes needed:

```bash
systemctl --user kill open-llm-vtuber.service
systemctl --user restart open-llm-vtuber.service
```

### Next Tuning Advice

If the next session continues chasing the remaining overshoot, prefer changing one thing at a time.

Recommended order:

1. slightly reduce `kp`
2. if still overshooting, slightly increase smoothing in `face_tracking_servo.py`
3. only then revisit `max_step`

Avoid going back to the old `person` / `motion` fallback chain unless there is a strong reason, because that path produced much noisier steering on-device.

## Ear Servo Motion

### Current Direction

Ear servo motion is now integrated into the currently running `Open-LLM-VTuber` process instead of only existing in the old `brain/online_agent` program.

Current implementation direction:

- a dedicated backend service drives ear servos through the shared PCA9685 instance
- dialogue start triggers a `thinking` ear motion
- wake-word acknowledgement triggers a `happy` ear motion
- LLM emotion tags extracted from text are preserved and used to drive backend ear motions

### Important Files

- `Open-LLM-VTuber/src/open_llm_vtuber/ear_motion_service.py`
- `Open-LLM-VTuber/src/open_llm_vtuber/agent/transformers.py`
- `Open-LLM-VTuber/src/open_llm_vtuber/live2d_model.py`
- `Open-LLM-VTuber/src/open_llm_vtuber/conversations/tts_manager.py`
- `Open-LLM-VTuber/src/open_llm_vtuber/websocket_handler.py`
- `Open-LLM-VTuber/conf.yaml`

### Current Status

Observed state at handoff:

- initial worker-loop jitter bug was fixed; ear motions no longer replay continuously without a new event
- wake-word ear response now works again after that fix
- ear motion amplitudes and delays were increased to make movement more visible in normal use
- direct hardware testing confirmed left ear on channel `2` is healthy
- right ear behavior was inconsistent across channels `1` and `3` in real app usage even though direct channel tests produced some movement

Current config direction in `conf.yaml` is:

- `left_channel: 2`
- `right_channel: 3`

Important nuance:

- direct servo tests are not enough by themselves; the right ear looked different in short real app motions than in standalone channel sweeps
- if right-ear motion still feels weak, compare direct channel tests against actual in-app wake/joy motions before changing software again

### Hardware Testing Notes

During this continuation, direct channel sweeps were run while the service was temporarily stopped:

- channels `2`, `1`, and `4`
- later channels `2` and `3`

That established:

- channel `2` is definitely reliable
- the right ear path is more ambiguous and may still involve mechanical or wiring limitations in addition to software

## Ear Servo Motion

Ear servo motion is now integrated into the currently running `Open-LLM-VTuber` process rather than the older standalone `brain` runtime.

Current implementation direction:

- a backend `EarMotionService` is started during server initialization
- it reuses the same shared PCA9685 manager as the chassis service
- ear motion is triggered from backend emotion/action flow, not from the frontend
- wake-word acknowledgement triggers a `happy` ear motion
- conversation start triggers a `thinking` ear motion
- LLM emotion tags such as `joy`, `smirk`, `surprise`, `sadness`, `anger` are preserved and mapped to ear motions

Main files involved:

- `Open-LLM-VTuber/src/open_llm_vtuber/ear_motion_service.py`
- `Open-LLM-VTuber/src/open_llm_vtuber/server.py`
- `Open-LLM-VTuber/src/open_llm_vtuber/conversations/tts_manager.py`
- `Open-LLM-VTuber/src/open_llm_vtuber/conversations/conversation_utils.py`
- `Open-LLM-VTuber/src/open_llm_vtuber/websocket_handler.py`
- `Open-LLM-VTuber/src/open_llm_vtuber/live2d_model.py`
- `Open-LLM-VTuber/src/open_llm_vtuber/agent/transformers.py`

Current config block is under `system_config.ear_motion` in `Open-LLM-VTuber/conf.yaml`.

Hardware notes established during this continuation:

- left ear servo channel is reliable on PCA9685 channel `2`
- channel `1` was inconsistent in practice
- channel `3` responded during direct hardware tests and the runtime config was switched to use it for the right ear

Current runtime config at handoff:

- `left_channel: 2`
- `right_channel: 3`

Important caveat:

- direct channel tests showed `2` and `3` could both move servos, but in the full runtime the right ear still sometimes looked weak or insufficiently visible
- this suggests remaining issues may be mechanical amplitude / timing rather than pure channel selection

Recent ear-motion tuning:

- fixed a worker-loop bug that caused continuous repeated replay of the same motion and visible ear jitter after wake-word acknowledgement
- increased motion amplitude and hold time so ear actions are easier to see in real use

If the right ear still looks inactive in the next session, prefer checking:

1. whether the motion amplitude is large enough for that servo/geometry
2. whether the servo horn or linkage on the right ear has less visible travel
3. whether right-ear-specific gain/offset should be added in `EarMotionService`

## Parent Repo Notes

The parent repo also contains local `brain/online_agent` code that was adjusted so the older brain runtime keeps the chassis in pure visual-follow mode and ignores scripted emotion/body actions:

- `brain/online_agent/main.py`
- `brain/online_agent/main_agent.py`
- `brain/online_agent/modules/chassis.py`

Those changes were committed in the parent repo snapshot `b177ab9`.

## Live2D Motion State

### Root Cause Found Earlier

Live2D expressions were still coming back from the LLM as tags like `[neutral]`, `[smirk]`.

Frontend bundle behavior:

- expressions and `Talk` motion are triggered when `audioBase64` is present
- lip sync depends on the model `_wavFileHandler`

Because frontend audio payload had previously been nulled out, the character stopped moving.

### Fixes Applied

1. Backend now keeps sending actual audio payload to frontend even when host-local playback is enabled.
2. Frontend hotfix mutes browser AI audio instead of removing it.
3. Frontend hotfix also boosts motion intensity.

Latest motion-boost patch:

- file: `Open-LLM-VTuber/frontend/frontend-hotfix.js`
- cache-bust version in `Open-LLM-VTuber/frontend/index.html` is `backendcam11`

What the motion boost does:

- patches `startRandomMotion("Talk", ...)` to prefer stronger priority if available
- patches `_wavFileHandler.update()` to increase `_lastRms`
- caps boosted lip-sync RMS at `6`

This was done as a runtime hotfix instead of editing the built minified bundle.

## Frontend Hotfix File

Main hotfix file:

- `Open-LLM-VTuber/frontend/frontend-hotfix.js`

It currently contains multiple operational patches, not just one:

- force safer VAD values
- force `autoStopMic = true`
- force mic auto-restart behavior
- mute browser AI audio
- disable browser video capture for frontend-only camera flows
- soften camera UI labels
- suppress the `Voice detected but too brief` / `检测到语音但过于简短` notice in the UI
- patch black fullscreen-like panels to transparent
- boost Live2D motion / lip sync

This file is operationally important. Be careful removing pieces blindly because several earlier kiosk problems were mitigated there.

## VAD / Echo Notes

Echo happened when the mic stayed open while AI audio was being played through speakers.

Frontend hotfix forces:

- `autoStopMic = true`
- automatic reopen after AI ends / interruption

This is important for kiosk speaker playback.

Important nuance:

- mic reopen timing depends not only on frontend settings but also on when backend emits audio payloads and end-of-conversation signals
- a delayed backend audio payload can look like a frontend VAD problem even when the actual bug is in backend TTS ordering

## Display / Black Screen History

There were repeated reports of the screen going black or appearing to power off during `thinking`.

Several mitigations were tried over time:

- disabling browser video capture
- hotfixing black overlay-like panels
- changing Chromium kiosk launch mode
- trying software WebGL / GPU-related flags
- removing unstable repeated `xrandr` mode forcing
- adjusting `/boot/firmware/config.txt` and `/boot/firmware/cmdline.txt`

The user later changed power setup, which may have improved some of the apparent display-drop behavior.

Do not assume the black-screen issue is fully solved. Re-verify on hardware before major frontend/display changes.

## Kiosk / Browser Notes

Frontend is loaded through `index.html` with cache-busted query params.

Current relevant line:

- `frontend-hotfix.js?v=backendcam11`

If the hotfix changes but kiosk appears stale, update the version suffix in `frontend/index.html` and relaunch kiosk.

## Frontend Recovery State

### What Changed In This Continuation

The original `Open-LLM-VTuber` frontend was temporarily replaced at the served `index.html` layer with a simplified expression display page.

Important current reality:

- this is **not** the normal Live2D frontend flow
- the page currently served by `/` is a recovery UI focused on stable face/eye display
- `#root` is intentionally hidden in `frontend/index.html`
- the built frontend bundle is still loaded, but visually suppressed

Current live page characteristics:

- dark full-screen background
- static expression / eye fallback rendered directly in HTML/CSS
- `frontend-hotfix.js` still loads
- cache-bust version currently observed live: `backendcam18`

### Why This Was Done

During this continuation, attempts were made to replace the frontend with animated eyes. Several instability paths appeared:

- browser sessions got out of sync with what the server was serving
- multiple Chromium profiles/processes fought each other
- temporary black-screen states appeared
- canvas-based eye rendering looked correct briefly, then could fall back to a black screen
- WebGL/Live2D init problems under the hidden original frontend produced extra UI noise

The current stable recovery decision was:

- stop trying to keep the animated canvas path active
- stop trusting the original Live2D page as the visible layer
- keep a simpler static expression page that the user reported as stable

### Current Files Involved

- `Open-LLM-VTuber/frontend/index.html`
- `Open-LLM-VTuber/frontend/frontend-hotfix.js`
- `Open-LLM-VTuber/frontend/eyes-overlay.js`

Important nuance:

- `eyes-overlay.js` still exists on disk from the earlier animated-eye attempt
- but it is **not currently loaded** by `index.html`
- the current stable recovery page is therefore static rather than animated

### Current Verified Runtime State

Observed on `2026-04-16`:

- `open-llm-vtuber.service` was running normally
- local server returned the simplified expression page at `http://127.0.0.1:12393/`
- server logs showed requests for:
  - `frontend-hotfix.js?v=backendcam18`
  - `assets/main-nu7uwxNJ.js?v=backendcam18`
  - `assets/main-QEkl09-0.css?v=backendcam18`
- WebSocket connection to `/client-ws` was established successfully
- the user reported the expression frontend had become stable again

### Browser / Chromium Notes From This Recovery

At one point, multiple Chromium sessions existed simultaneously:

- the old kiosk-launched profile
- temporary recovery profiles under `/tmp`

That caused confusion where the screen could show different frontend states than the server was actually serving.

Practical lesson:

- if the screen content does not match the HTML returned by `curl http://127.0.0.1:12393/`, suspect stale or competing Chromium sessions first

One clean recovery approach that worked during this continuation was:

1. kill all Chromium processes
2. relaunch a single Chromium session on `:0`
3. use only one profile during recovery

### Known Residual Issues

- server logs still showed:
  - `GET /undefined/undefined.model3.json HTTP/1.1` `404 Not Found`
- this likely comes from the bundled original frontend still trying to initialize a model underneath the hidden root
- because the recovery page hides `#root`, this was not treated as the immediate blocker once the user confirmed stable visible expressions

Recommended next cleanup step:

1. remove or neutralize the hidden frontend code path that still requests `undefined.model3.json`

### Guidance For The Next Session

If the user says the expression frontend is stable, prefer preserving that state first.

Recommended order:

1. do **not** re-enable animated eyes immediately
2. first clean up the hidden `undefined.model3.json` request path
3. only after that, if the user explicitly wants animation again, reintroduce animation gradually from the stable static page

If the screen becomes black again:

- first verify what `/` is serving with `curl`
- then verify Chromium process count/profile usage
- do not assume backend or service restart alone will fix it

## Audio Hardware Notes

Audio device previously detected and used:

- `CD002-AUDIO Analog Stereo`

Direct system playback test via `pw-play` was audible. That means if app speech is silent again, hardware may still be fine and the bug may be in TTS generation or playback plumbing.

## Raspberry Pi To PCA9685 Wiring Notes

Current hardware situation:

- the old PCA9685 board produced visible burn damage during a direct `channel 0` servo sweep test
- do not reuse the burned PCA9685 board, because it may short and damage the Raspberry Pi
- user plans to buy a replacement PCA9685 board
- only the chassis/base servo is currently intended to be connected
- ear servos are not currently connected
- `Open-LLM-VTuber/conf.yaml` has `ear_motion.enabled: false`
- chassis face tracking is configured for PCA9685 `channel=0`

Recommended Raspberry Pi control wiring for the new PCA9685 board:

- Raspberry Pi `3.3V` -> PCA9685 `VCC`
- Raspberry Pi `GND` -> PCA9685 `GND`
- Raspberry Pi `SDA` / GPIO2 / physical pin 3 -> PCA9685 `SDA`
- Raspberry Pi `SCL` / GPIO3 / physical pin 5 -> PCA9685 `SCL`

User-provided current wire color note:

- yellow -> `1`
- red -> `3`
- orange -> `4`
- green -> `5`

This color note was recorded exactly as provided. Before powering the replacement PCA9685, verify whether these numbers mean Raspberry Pi physical pins, PCA9685 header positions, or another connector numbering scheme. Do not assume this mapping is electrically safe until each wire is matched to `VCC`, `GND`, `SDA`, and `SCL`.

Recommended servo power wiring:

- external servo power positive -> PCA9685 `V+`
- external servo power negative -> PCA9685 `GND`
- Raspberry Pi `GND`, PCA9685 `GND`, and external servo power negative must share common ground
- do not power a chassis servo directly from the Raspberry Pi 5V pin
- do not connect Raspberry Pi `3.3V` or `5V` to PCA9685 `V+`

Servo channel mapping expected by current software:

- chassis/base servo signal -> PCA9685 `channel 0`
- left ear servo would be `channel 2`, but ear motion is currently disabled
- right ear servo would be `channel 3`, but ear motion is currently disabled

Safe bring-up order for the replacement PCA9685:

1. with no servos connected, wire only `VCC`, `GND`, `SDA`, and `SCL`
2. run `i2cdetect -y 1` and confirm address `0x40`
3. connect external servo power to `V+` and `GND`, with no servo plugged in, and verify there is no heat/smell
4. connect one chassis servo to `channel 0`, carefully checking the servo plug direction: `GND`, `V+`, `PWM`
5. run only a small angle sweep test before enabling face tracking
6. restart `open-llm-vtuber.service` only after the direct hardware test is safe

Important diagnostic note:

- the direct sweep command previously sent PWM to `channel 0` only; PWM alone should not burn a healthy PCA9685 board
- visible burn damage strongly suggests wiring, polarity, voltage, short circuit, or power-current issue rather than a frontend/software issue

## Current Stable Kiosk State On 2026-04-20

This is the latest state the user considered acceptable enough to commit:

- visible frontend is the custom static eyes/expression UI
- original Open-LLM-VTuber frontend bundle still runs underneath with `#root` nearly hidden
- original frontend handles microphone/VAD/WebSocket conversation flow
- `emotion-fallback.js` observes backend WebSocket messages and updates the visible eyes expression
- `backend-camera-patch.js` polls `/backend-camera/snapshot.jpg` and attaches images to conversation payloads
- browser audio is no longer forcibly muted in `frontend-hotfix.js`
- `frontend/index.html` currently uses cache-bust suffix `voice-image-1`
- kiosk browser was relaunched with `--use-fake-ui-for-media-stream` to avoid microphone permission blocking

Hardware safety state during this test:

- no PCA9685 board should be connected until the replacement board arrives
- `Open-LLM-VTuber/conf.yaml` was locally changed to `face_tracking.enabled: false`
- `Open-LLM-VTuber/conf.yaml` was locally changed to `ear_motion.enabled: false`
- these config values may be local runtime config rather than committed code; verify before starting any hardware test

Verified behavior:

- wake word and speech path worked
- backend attached camera image to the conversation
- AI generated a visual answer about the camera frame
- TTS generated audio files
- no PCA9685 / `face_tracking_servo` / `ear_motion` initialization appeared after disabling those config flags
- audio was fixed after moving the USB audio device to another port

## Static Expression UI Update On 2026-04-23

The visible frontend is still the custom static eyes/expression UI in `Open-LLM-VTuber/frontend/index.html`.

Latest committed expression state:

- `Open-LLM-VTuber` commit: `5dcf828` `fix: stabilize kiosk agent and tts flow`
- `frontend` commit: `34eba72` `fix: stabilize static expression playback`

Current `frontend/index.html` cache-bust suffix is:

- `live2d-eyes-4`

Latest expression-runtime behavior:

- user input transcription no longer forces a surprised expression
- audio payloads without real audio no longer immediately reset or change the current expression while speaking
- each response keeps a stable response emotion instead of defaulting every audio chunk to happy
- conversation end holds the current expression briefly before neutral fallback, reducing visible eye/expression jitter

Current visible expression states:

- `neutral`: normal open eyes, middle eyelash line removed
- `happy`: same base style, slightly larger pupils, brighter highlights, softer smiling upper eyelids
- `sad`: soft half-closed/downcast eyes, no middle eyelash line, pupils lower in the eye frame, outer eyebrow ends raised per user preference
- `angry`: uses the `surprised` eye-frame shape, with orange/fire-like pupils inside both eyes
- `surprised`: rounded open-eye expression
- `thinking`: side-looking pupils, middle eyelash line removed

Expression screenshots were exported for thesis/demo use at:

- `/home/raspberrypi/Desktop/MyGraduationProject/docs/thesis/expression_screenshots/`

Important files in that folder:

- `all_expressions.png`
- `neutral.png`
- `happy.png`
- `sad.png`
- `angry.png`
- `surprised.png`
- `thinking.png`
- `expression_capture.html`
- `contact_sheet.html`

Screenshot generation note:

- screenshots were generated from `expression_capture.html`, a temporary standalone page derived from `frontend/index.html`
- it intentionally removes the production frontend scripts so screenshots do not open WebSocket/camera paths
- headless Chromium needed elevated execution in this environment because the normal sandbox hit crashpad/shared-memory restrictions

Design caveat:

- do not return to the earlier aggressive black `sad` eyelid/concave shape; the user found that version scary
- if continuing expression tuning, preserve the current soft anime-eye style and regenerate both the single expression PNG and `all_expressions.png`

Git caveat:

- the expression CSS and screenshots are committed
- there are still unrelated uncommitted OpenClaw/backend and thesis-file changes in the worktree; do not assume a clean tree

## Files Worth Reading First

If a new Codex session needs to continue efficiently, read these first:

- `/home/raspberrypi/Desktop/MyGraduationProject/CODEX_HANDOFF.md`
- `/home/raspberrypi/Desktop/MyGraduationProject/Open-LLM-VTuber/conf.yaml`
- `/home/raspberrypi/Desktop/MyGraduationProject/Open-LLM-VTuber/src/open_llm_vtuber/conversations/conversation_handler.py`
- `/home/raspberrypi/Desktop/MyGraduationProject/Open-LLM-VTuber/src/open_llm_vtuber/websocket_handler.py`
- `/home/raspberrypi/Desktop/MyGraduationProject/Open-LLM-VTuber/src/open_llm_vtuber/conversations/conversation_utils.py`
- `/home/raspberrypi/Desktop/MyGraduationProject/Open-LLM-VTuber/src/open_llm_vtuber/conversations/tts_manager.py`
- `/home/raspberrypi/Desktop/MyGraduationProject/Open-LLM-VTuber/frontend/frontend-hotfix.js`
- `/home/raspberrypi/Desktop/MyGraduationProject/Open-LLM-VTuber/frontend/index.html`

If debugging current behavior, also inspect recent logs:

- `/home/raspberrypi/Desktop/MyGraduationProject/Open-LLM-VTuber/logs/`

## Practical Advice For The Next Codex

- Treat the frontend hotfix as part of the production path, not a temporary scratch file.
- Prefer small runtime patches over editing the built frontend bundle directly.
- Treat `websocket_handler.py` as part of the real product behavior now, not just plumbing; recent wake-word logic lives there.
- When changing audio, remember there are two separate concerns:
  - host-local audible playback
  - frontend audio payload needed for Live2D motion/lip sync
- When changing mic behavior, remember there are two separate concerns:
  - frontend VAD / auto-reopen settings
  - backend timing of audio payload emission and conversation-end signaling
- When changing camera behavior, remember there are also two separate concerns:
  - user-visible camera UI
  - backend-attached snapshot for VLM
- Re-verify behavior on the real kiosk after each substantial change. This project has several hardware-specific failure modes that are not obvious from code alone.
