# AIOS v1.5 — Multi-Step Planning

AIOS v1.5 adds a deterministic multi-step task planner. A task goal is converted into a list of `ActionRequest` objects, then executed sequentially through the existing `PolicyEngine` and `SystemAdapter`.

Examples:

- `open chrome and vscode`
- `prepare my coding workspace`
- `prepare my study workspace`
- `launch my coding apps`
- `close development apps` (confirmation required)

The planner never calls Windows APIs directly. A plan that contains medium/high/critical actions is held for explicit confirmation.
