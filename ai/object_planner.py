from __future__ import annotations

import re
from pathlib import Path

from ai.intent import OSIntent
from core.actions import RiskLevel


class ObjectPlanner:
    """Deterministic v0.5 natural-language planner over the AIOS object model."""

    def plan(self, text: str) -> OSIntent | None:
        original = text.strip()
        command = " ".join(original.lower().split())
        if not command:
            return None

        if command in {"system status", "show system status", "how is my system", "how's my system"}:
            return OSIntent("system_info", parameters={"include_processes": False}, explanation="Inspect current system state.")

        if command in {"what apps are running", "which apps are running", "show running apps", "show running applications", "what is running"}:
            return OSIntent("list_processes", target_type="process", explanation="List user-visible running processes.")

        if command in {"open downloads", "open my downloads", "show downloads", "show my downloads"}:
            return OSIntent("open_path", "folder", str(Path.home() / "Downloads"), explanation="Open the Downloads folder.")

        if command in {"open documents", "open my documents"}:
            return OSIntent("open_path", "folder", str(Path.home() / "Documents"), explanation="Open the Documents folder.")

        if command in {"open desktop", "show desktop folder"}:
            return OSIntent("open_path", "folder", str(Path.home() / "Desktop"), explanation="Open the Desktop folder.")

        if command in {"open file manager", "open files", "open file explorer", "open explorer"}:
            return OSIntent("open_path", "folder", str(Path.home()), explanation="Open the user's home folder in the file manager.")

        if command in {"show apps", "open apps", "open app launcher", "show application launcher", "list applications"}:
            return OSIntent("list_apps", "application", explanation="Show applications discovered by AIOS.")

        for prefix in ("find ", "search for ", "search files for ", "find files for "):
            if command.startswith(prefix):
                query = original[len(prefix):].strip()
                if query:
                    return OSIntent(
                        "search_files",
                        "file",
                        query,
                        {"query": query, "root": str(Path.home())},
                        explanation=f"Search the home directory for '{query}'.",
                    )

        if command in {"show files modified today", "files modified today", "what changed today", "show today's files"}:
            return OSIntent(
                "search_files_modified",
                "file",
                "today",
                {"root": str(Path.home())},
                explanation="Find files modified since the start of today.",
            )

        if command in {"open my coding project", "open my code project", "open my programming project"}:
            candidates = [
                Path.home() / "Desktop" / "Projects",
                Path.home() / "Documents" / "Projects",
                Path.home() / "Desktop" / "AIOS",
                Path.home() / "Documents" / "AIOS",
            ]
            existing = next((p for p in candidates if p.exists()), candidates[0])
            return OSIntent("open_path", "workspace", str(existing), {"preferred": [str(p) for p in candidates]}, confidence=0.82, explanation="Open the most likely coding workspace.")

        if command.startswith("open "):
            target = original[5:].strip().strip('"')
            if target:
                path = Path(target).expanduser()
                if path.exists() or re.match(r"^[A-Za-z]:[\\/]", target) or target.startswith(("\\\\", "/")):
                    return OSIntent("open_path", "file_or_folder", target, explanation="Open the requested filesystem object.")
                return OSIntent("launch_app", "application", target, risk=RiskLevel.LOW, explanation="Launch the requested application.")

        if command.startswith("close "):
            target = original[6:].strip()
            if target:
                return OSIntent("close_process", "process", target, risk=RiskLevel.MEDIUM, confidence=0.76, explanation="Close a matching running process after confirmation.")

        if command in {"lock computer", "lock pc", "lock my computer"}:
            return OSIntent("lock_computer", "setting", risk=RiskLevel.HIGH, explanation="Lock the current Windows session.")

        if command in {"shutdown", "shut down", "shutdown computer", "shut down computer"}:
            return OSIntent("shutdown", "setting", risk=RiskLevel.CRITICAL, explanation="Power off Windows.")

        if command in {"restart", "restart computer", "reboot", "reboot computer"}:
            return OSIntent("restart", "setting", risk=RiskLevel.CRITICAL, explanation="Restart Windows.")

        return None
