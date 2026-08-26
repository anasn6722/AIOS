# AIOS — AI-Native Operating Environment

## v0.4.0 — Application Launcher + File Manager

AIOS is a separate project from JARVIS OFFLINE. JARVIS remains an independent resume/portfolio project.

### Current capabilities
- AIOS desktop shell
- Protected AI command orchestration
- Windows application discovery and launching
- Application launcher panel
- File manager panel with folders and files
- Browse into directories and move up
- File search from the home directory
- Open files with the native OS handler
- Live CPU / RAM / clock status
- Confirmation gates for lock, shutdown, and restart

### Architecture

```text
Manual UI / AI command
        ↓
Orchestrator
        ↓
Policy Engine
        ↓
System Adapter
   ┌────┴───────────┐
   │                │
App Launcher    File Manager
   │                │
Windows Apps     Local Files
```

### Run on Windows

```powershell
cd C:\Users\<your-user>\Desktop\AIOS\AIOS
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

### Example AI commands

- `system status`
- `open notepad`
- `open chrome`
- `open downloads`
- `open file manager`
- `open apps`
- `find pdf`
- `show desktop`

### Safety

The AI layer does not directly call Windows APIs. System actions go through the orchestrator and policy engine. High-risk operations require confirmation.
