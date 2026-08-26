from __future__ import annotations

import os
import platform
import subprocess
from pathlib import Path

import psutil

from core.actions import ActionRequest, ActionResult, RiskLevel


class SystemAdapter:
    """Small, explicit OS adapter. Extend this instead of letting the AI call OS APIs directly."""

    def execute(self, request: ActionRequest) -> ActionResult:
        handlers = {
            "system_info": self.system_info,
            "open_path": self.open_path,
        }
        handler = handlers.get(request.name)
        if handler is None:
            return ActionResult(False, f"Unknown action: {request.name}")
        return handler(request)

    def system_info(self, request: ActionRequest) -> ActionResult:
        return ActionResult(
            True,
            "System information collected.",
            {
                "platform": platform.platform(),
                "cpu_percent": psutil.cpu_percent(interval=0.1),
                "ram_percent": psutil.virtual_memory().percent,
                "hostname": platform.node(),
            },
        )

    def open_path(self, request: ActionRequest) -> ActionResult:
        raw_path = str(request.parameters.get("path", "")).strip()
        if not raw_path:
            return ActionResult(False, "No path was supplied.")

        path = Path(raw_path).expanduser()
        if not path.exists():
            return ActionResult(False, f"Path does not exist: {path}")

        try:
            if os.name == "nt":
                os.startfile(path)  # type: ignore[attr-defined]
            elif platform.system() == "Darwin":
                subprocess.Popen(["open", str(path)])
            else:
                subprocess.Popen(["xdg-open", str(path)])
            return ActionResult(True, f"Opened {path}")
        except OSError as exc:
            return ActionResult(False, f"Could not open path: {exc}")
