# AIOS — AI-Native Operating Environment

## v0.6.0 — Local AI Reasoning Layer

AIOS is a separate project from JARVIS OFFLINE. JARVIS remains an independent resume/portfolio project.

### Current capabilities
- AIOS desktop shell
- Protected AI command orchestration
- Windows application discovery and launching
- Application launcher panel
- File manager panel with folders and files
- File search and modified-today search
- Structured AIOS object model
- Deterministic natural-language planner
- Optional localhost LLM planner for flexible natural-language interpretation
- Strict validation of model output before it can become an OS action
- Existing confirmation gates for medium/high/critical actions

### v0.6 local AI mode
The local model is optional. By default AIOS remains deterministic/offline without an LLM process. To enable the localhost provider, set these environment variables before launching:

```powershell
$env:AIOS_LLM_ENABLED="1"
$env:AIOS_LLM_PROVIDER="ollama"
$env:AIOS_LLM_BASE_URL="http://127.0.0.1:11434"
$env:AIOS_LLM_MODEL="qwen3:4b"
python app.py
```

If the local model is unavailable or returns invalid output, AIOS automatically falls back to the deterministic object planner.

### Safety architecture

```text
User text
   ↓
Local LLM (optional)
   ↓
Strict JSON validator
   ↓
OSIntent
   ↓
ActionRequest
   ↓
Policy Engine
   ↓
System Adapter
   ↓
Windows
```

The local model cannot directly execute Windows APIs, shell commands, or Python code.
