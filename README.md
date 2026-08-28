# AIOS v0.9.0 — AI Workspace Engine

AIOS remains a Windows-hosted AI-native desktop environment. v0.9 adds persistent workspace profiles on top of the working v0.8.1 shell.

## Features
- Persistent Coding, Study, and Business workspace profiles
- Workspace selector in the desktop UI
- `show workspaces`
- `switch to <workspace>` / `open workspace <workspace>`
- `create workspace <name>` with guided app/folder capture
- Save Current Workspace button
- Workspace restore launches configured apps and opens the first available folder
- Existing v0.8.1 command routing, context, memory, policy, and app/file functions are preserved

Workspace data is stored locally at:
`%USERPROFILE%\.aios\workspaces.json`

## Install
Close AIOS and extract this package directly into:
`C:\Users\انس\Desktop\AIOS\AIOS`

Then run:

```powershell
cd C:\Users\انس\Desktop\AIOS\AIOS
.\.venv\Scripts\Activate.ps1
python app.py
```

## Test
```text
show workspaces
switch to Coding
switch to Study
open workspace Business
```

Workspace switching only launches configured applications and opens folders; it does not perform destructive actions.

## Validation
- v0.9 workspace tests: 3 passed
- Python compile: passed


## v1.0.0 Core Integration

AIOS now uses a shared runtime/service container for the policy engine, system adapter, context, memory, object planner, LLM planner, file manager, app launcher, and workspace engine. This establishes stable internal boundaries for future AI agents and native OS services.

## v1.2 Voice + Vision

AIOS v1.2 adds a local-first media layer to the Unified AI Command Center.

### Vision
- Captures the current desktop to `%USERPROFILE%\\.aios\\captures`.
- Combines the image metadata with the read-only context snapshot.
- No system action is granted to the vision layer.

### Voice
- Uses `sounddevice` for microphone capture and Vosk for local transcription.
- Configure a local Vosk model with `AIOS_VOSK_MODEL`.
- The voice button records a short command, places the transcription in the AI command bar, and sends it through the existing orchestrator/policy boundary.

Voice is optional at installation time. Without the microphone backend or a Vosk model, AIOS remains fully usable through text.


### v1.2.1 UI fix
Voice Input and Capture Screen are now prominent controls at the top of the AI Command Center.


## v1.2.9 voice architecture
Voice uses faster-whisper `base.en` on CPU/int8 as the primary offline recognizer, with Vosk as a fallback. The first Whisper model load may download model files; afterward the model is cached locally under `C:\AIOS\models\whisper`.


## v1.3.0 Screen Understanding
The screen action now captures the desktop and produces a local semantic analysis: active window/process, visible windows, and optional OCR text. Vision remains read-only. Direct commands include "what is on my screen", "analyze my screen", and "read my screen".

## v1.5 — Autonomous Task Planning

AIOS can now convert supported natural-language goals into multi-step plans and execute them sequentially behind the existing policy engine.
