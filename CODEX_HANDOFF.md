# Codex Handoff

## Repo Layout

- Parent repo: `/home/raspberrypi/Desktop/MyGraduationProject`
- VTuber backend repo: `/home/raspberrypi/Desktop/MyGraduationProject/Open-LLM-VTuber`
- Frontend repo/submodule: `/home/raspberrypi/Desktop/MyGraduationProject/Open-LLM-VTuber/frontend`

## Git State

Latest local commits at handoff:

- Parent repo: `b177ab9` `chore: sync vtuber and chassis updates`
- `Open-LLM-VTuber`: `81c5009` `fix: tune ear motion and vision triggers`
- `frontend`: `1a1dcbf` `fix: hide vad misfire notice`

Recent `Open-LLM-VTuber` commits from this continuation:

- `81c5009` `fix: tune ear motion and vision triggers`
- `73483cc` `feat: add ear servo emotion hooks`
- `e57a5b7` `feat: switch chassis tracking to dnn mil`
- `704511e` `feat: add chassis target tracking service`
- `f418c9c` `chore: update frontend hotfix snapshot`
- `6283ac7` `feat: add spoken wake word acknowledgement`
- `22408cf` `fix: shorten mic mute after local playback`
- `8365168` `feat: add wake word gated voice chat`

Recent `frontend` commits from this continuation:

- `1a1dcbf` `fix: hide vad misfire notice`
- `3a3d62a` `feat: boost live2d talk motion intensity`

Git cleanliness should be re-checked at the next session rather than assumed.

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
- Kiosk launcher script:
  - `/home/raspberrypi/Desktop/MyGraduationProject/Open-LLM-VTuber/scripts/open_llm_vtuber_kiosk.sh`

Typical commands that were used:

```bash
systemctl --user restart open-llm-vtuber.service
setsid /home/raspberrypi/Desktop/MyGraduationProject/Open-LLM-VTuber/scripts/open_llm_vtuber_kiosk.sh
```

Server listens on:

- `http://0.0.0.0:12393`

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

## Audio Hardware Notes

Audio device previously detected and used:

- `CD002-AUDIO Analog Stereo`

Direct system playback test via `pw-play` was audible. That means if app speech is silent again, hardware may still be fine and the bug may be in TTS generation or playback plumbing.

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
