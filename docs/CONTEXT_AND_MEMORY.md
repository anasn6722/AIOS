# AIOS v0.7 — Context & Memory

AIOS v0.7 adds a read-only context layer and small local memory store.

## Context

The context engine can report:
- current user/home/directory
- platform and resource usage
- foreground window title, PID and process (Windows)
- recent AIOS commands in the current session

## Memory

Safe local memory is stored at `~/.aios/memory.json` and currently supports preferences and recent commands. It does not grant the AI additional OS permissions.

## New commands

```text
show my context
what is my current context
what app am i using
what window is active
show recent commands
what did i just do
```

All context actions are read-only and use the same orchestrator boundary.
