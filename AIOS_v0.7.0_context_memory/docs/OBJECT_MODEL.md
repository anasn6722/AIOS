# AIOS v0.5 — AI Object Model

AIOS v0.5 introduces a structured representation for common operating-system objects.

## Object types

- `application` — launchable desktop applications
- `file` — individual files
- `folder` — directories and special folders
- `workspace` — a higher-level user work location
- `process` — running processes
- `task` — future planned/queued work
- `setting` — operating-system state or configuration

## Flow

`Natural language -> Object Planner -> ActionRequest -> Policy Engine -> System Adapter`

The planner in v0.5 is deterministic. A future LLM can replace or augment the planner, but it must still emit structured intents that pass through policy and the system adapter.

## Example

`open my coding project`

becomes an `open_path` intent with target type `workspace` and candidate project locations.

`what apps are running`

becomes a `list_processes` intent with target type `process`.

`close chrome`

becomes a medium-risk `close_process` action and therefore requires confirmation.
