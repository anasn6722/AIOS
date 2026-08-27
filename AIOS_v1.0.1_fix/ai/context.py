from __future__ import annotations

import ctypes
import os
import platform
from datetime import datetime
from pathlib import Path
from typing import Any

import psutil


class ContextEngine:
    """Read-only snapshot of the user's current AIOS/Windows context."""

    def __init__(self, recent_limit: int = 20) -> None:
        self.recent_limit = recent_limit
        self.recent_commands: list[str] = []

    def record_command(self, text: str) -> None:
        value = " ".join(text.split()).strip()
        if not value:
            return
        self.recent_commands.append(value)
        del self.recent_commands[:-self.recent_limit]

    def _active_window(self) -> dict[str, Any]:
        if os.name != "nt":
            return {"title": None, "pid": None}
        try:
            user32 = ctypes.windll.user32
            hwnd = user32.GetForegroundWindow()
            if not hwnd:
                return {"title": None, "pid": None}
            length = user32.GetWindowTextLengthW(hwnd)
            buffer = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buffer, length + 1)
            pid = ctypes.c_ulong()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            return {"title": buffer.value or None, "pid": int(pid.value)}
        except (AttributeError, OSError):
            return {"title": None, "pid": None}

    def snapshot(self) -> dict[str, Any]:
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage(Path.home().anchor or os.sep)
        active = self._active_window()
        active_name = None
        if active.get("pid"):
            try:
                active_name = psutil.Process(active["pid"]).name()
            except (psutil.Error, OSError):
                active_name = None
        return {
            "timestamp": datetime.now().astimezone().isoformat(timespec="seconds"),
            "user": os.environ.get("USERNAME") or os.environ.get("USER") or "user",
            "home": str(Path.home()),
            "current_directory": os.getcwd(),
            "platform": platform.platform(),
            "cpu_percent": round(psutil.cpu_percent(interval=None), 1),
            "ram_percent": round(memory.percent, 1),
            "disk_percent": round(disk.percent, 1),
            "active_window": {
                "title": active.get("title"),
                "pid": active.get("pid"),
                "process": active_name,
            },
            "recent_commands": list(self.recent_commands),
        }
