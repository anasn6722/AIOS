from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from core.services import AIOSServices


@dataclass
class RuntimeState:
    started_at: str
    command_count: int = 0
    last_command: str | None = None


class AIOSRuntime:
    """Application runtime coordinating services without exposing raw OS access to AI."""

    def __init__(self, services: AIOSServices | None = None) -> None:
        self.services = services or AIOSServices.build()
        self.state = RuntimeState(started_at=datetime.now(timezone.utc).isoformat())
        self.services.system.runtime_provider = self

    def record_command(self, command: str) -> None:
        self.state.command_count += 1
        self.state.last_command = command
        self.services.context.record_command(command)
        self.services.memory.record_command(command)

    def health(self) -> dict[str, Any]:
        return {
            "runtime": "online",
            "started_at": self.state.started_at,
            "command_count": self.state.command_count,
            "last_command": self.state.last_command,
            "services": self.services.health(),
        }
