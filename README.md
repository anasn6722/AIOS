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
