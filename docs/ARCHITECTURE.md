# AIOS Foundation Architecture

```text
Manual UI ───────┐
                 ├──> Action Layer ──> Policy ──> OS Adapters ──> Windows
AI Intent ───────┘
```

The key rule is that AI never receives unrestricted operating-system access.
AI requests structured actions. The policy layer decides whether they can execute.

## Next layers
1. Local AI model adapter
2. Voice input
3. Vision and screen understanding
4. File intelligence
5. Application automation
6. AI workspace manager
7. Multi-agent orchestration
8. Deep Windows integration
9. Installer and background services
10. Future bootable/custom OS research
