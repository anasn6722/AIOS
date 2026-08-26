# AIOS

AIOS is a separate experimental AI-native operating environment project.

## Goals
- Manual desktop control remains first-class.
- Natural-language AI control uses the same protected action layer.
- Local/offline-first architecture with optional online AI later.
- Explicit permissions for destructive or privileged actions.
- Gradual path from Windows-hosted shell to a deeper OS platform.

## Current milestone: Foundation
This starter establishes:
- project boundaries
- an action model
- a permission policy layer
- a basic orchestrator
- a Windows system adapter
- a minimal Qt desktop shell

JARVIS OFFLINE is intentionally not part of this repository.


## v0.2.0 — Desktop Shell

The first AIOS desktop shell adds:

- AIOS workspace desktop layout
- Navigation panel and taskbar
- Live CPU/RAM/time status
- AI command bar
- Protected orchestrator → policy → system execution path
- Workspace cards for system monitoring, files, AI command center, and app launcher

This remains a normal Windows application while AIOS evolves toward a full operating environment.
