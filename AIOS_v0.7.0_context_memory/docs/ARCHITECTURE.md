# AIOS Architecture

## v0.3 Native Control

```text
Manual UI / AI command
          |
          v
     Orchestrator
          |
          v
     ActionRequest
          |
          v
     PolicyEngine
          |
    +-----+-----+
    |           |
   allow     confirm
    |           |
    +-----+-----+
          |
          v
    SystemAdapter
          |
          v
   Windows / OS APIs
```

The LLM layer must never receive unrestricted OS access. Future LLM planners produce structured `ActionRequest` objects that are still checked by the policy engine.

### v0.3 supported actions

- System status
- Open files/folders
- Launch common Windows applications
- Show desktop
- Lock computer (confirmation required)
- Restart computer (confirmation required)
- Shutdown computer (confirmation required)
