from __future__ import annotations

import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

from typing import Protocol


class LaunchSystem(Protocol):
    APP_ALIASES: dict[str, list[str]]
    COMMON_WINDOWS_APPS: dict[str, list[Path]]
    def _resolve_executable(self, app: str) -> str | None: ...
    def launch_app(self, request): ...


@dataclass(frozen=True)
class AppEntry:
    name: str
    executable: str
    source: str


class AppLauncher:
    """Discover common Windows applications without granting raw shell access."""

    def __init__(self, system: LaunchSystem) -> None:
        self.system = system or SystemAdapter()

    def discover(self) -> list[AppEntry]:
        entries: list[AppEntry] = []
        seen: set[str] = set()
        for name in sorted(self.system.APP_ALIASES):
            executable = self.system._resolve_executable(name)
            if not executable:
                continue
            key = executable.lower()
            if key in seen:
                continue
            seen.add(key)
            entries.append(AppEntry(self._pretty(name), executable, "AIOS alias"))
        for name, candidates in self.system.COMMON_WINDOWS_APPS.items():
            for candidate in candidates:
                if candidate.is_file() and str(candidate).lower() not in seen:
                    seen.add(str(candidate).lower())
                    entries.append(AppEntry(self._pretty(name), str(candidate), "Windows install"))
        return sorted(entries, key=lambda item: item.name.lower())

    @staticmethod
    def _pretty(value: str) -> str:
        return re.sub(r"\s+", " ", value.replace("microsoft ", "").replace("google ", "")).title()

    def launch(self, app_name: str) -> tuple[bool, str]:
        from core.actions import ActionRequest
        result = self.system.launch_app(ActionRequest("launch_app", {"app": app_name}, source="manual"))
        return result.ok, result.message
