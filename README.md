# AIOS

AI-native desktop environment prototype — **v0.3.0**.

AIOS is a separate project from JARVIS OFFLINE. JARVIS remains an independent portfolio project.

## v0.3

The desktop shell can now perform controlled Windows actions through:

`Command -> Orchestrator -> PolicyEngine -> SystemAdapter -> Windows`

Supported examples:

- `system status`
- `open chrome`
- `open notepad`
- `open calculator`
- `open terminal`
- `open task manager`
- `open .`
- `open C:\Users`
- `show desktop`
- `lock computer` (confirmation)
- `restart` (confirmation)
- `shutdown` (confirmation)

## Run

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

## Safety

High-risk and critical actions are blocked until explicitly confirmed. The AI layer is not allowed to call Windows APIs directly.


## v0.3.2
Application command parsing now prioritizes known Windows app aliases before filesystem path checks.
