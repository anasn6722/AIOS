from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class MemoryStore:
    """Small local JSON memory for safe AIOS preferences and recent context."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or (Path.home() / ".aios" / "memory.json")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.data: dict[str, Any] = self._load()

    def _load(self) -> dict[str, Any]:
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            return {"preferences": {}, "recent_commands": []}

    def save(self) -> None:
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(json.dumps(self.data, indent=2), encoding="utf-8")
        temporary.replace(self.path)

    def remember(self, key: str, value: Any) -> None:
        self.data.setdefault("preferences", {})[key] = value
        self.save()

    def get(self, key: str, default: Any = None) -> Any:
        return self.data.get("preferences", {}).get(key, default)

    def record_command(self, command: str, limit: int = 50) -> None:
        recent = self.data.setdefault("recent_commands", [])
        recent.append(command)
        del recent[:-limit]
        self.save()
