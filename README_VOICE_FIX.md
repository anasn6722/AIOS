# AIOS v1.2.3 Voice Fix

This patch improves Windows microphone reliability by adding a PyAudio fallback,
local Vosk model discovery, cached Vosk model loading, and explicit diagnostics.

Install/update dependencies:

```powershell
pip install -r requirements.txt
```

Optional explicit model path:

```powershell
$env:AIOS_VOSK_MODEL="C:\path\to\vosk-model-small-en-us-0.15"
```
