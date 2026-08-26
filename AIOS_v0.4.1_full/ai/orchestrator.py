from __future__ import annotations

import re
from pathlib import Path

from core.actions import ActionRequest, ActionResult, RiskLevel
from security.policy import PolicyEngine
from system.adapter import SystemAdapter


class Orchestrator:
    """Deterministic v0.4 intent router; future LLM plans still pass through policy."""

    def __init__(self) -> None:
        self.policy = PolicyEngine()
        self.system = SystemAdapter()

    def interpret(self, text: str) -> ActionRequest | None:
        original = text.strip()
        command = original.lower()
        if not command:
            return None

        if command in {"system info", "system status", "show system status", "how is my system"}:
            return ActionRequest("system_info", risk=RiskLevel.SAFE, source="ai")

        if command in {"show desktop", "minimize everything", "desktop"}:
            return ActionRequest("show_desktop", risk=RiskLevel.LOW, source="ai")

        if command in {"list apps", "show apps", "app launcher", "open apps", "open app launcher"}:
            return ActionRequest("list_apps", risk=RiskLevel.SAFE, source="ai")

        if command in {"open home", "open files", "open file manager", "open file explorer", "open explorer"}:
            return ActionRequest("open_path", {"path": str(Path.home())}, RiskLevel.LOW, "ai")

        if command in {"open downloads", "open my downloads"}:
            return ActionRequest("open_path", {"path": str(Path.home() / "Downloads")}, RiskLevel.LOW, "ai")

        for prefix in ("find ", "search files for ", "find files for "):
            if command.startswith(prefix):
                query = original[len(prefix):].strip()
                if query:
                    return ActionRequest("search_files", {"query": query, "root": str(Path.home())}, RiskLevel.SAFE, "ai")

        for prefix in ("open ", "launch ", "start "):
            if command.startswith(prefix):
                target = original[len(prefix):].strip().strip('"')
                if not target:
                    return None
                path = Path(target).expanduser()
                if path.exists() or target in {".", "~"}:
                    return ActionRequest("open_path", {"path": target}, RiskLevel.LOW, "ai")
                if re.match(r"^[A-Za-z]:[\\/]", target) or target.startswith(("\\\\", "/")):
                    return ActionRequest("open_path", {"path": target}, RiskLevel.LOW, "ai")
                return ActionRequest("launch_app", {"app": target}, RiskLevel.LOW, "ai")

        if command in {"lock computer", "lock pc", "lock my computer"}:
            return ActionRequest("lock_computer", risk=RiskLevel.HIGH, source="ai")
        if command in {"shutdown", "shut down", "shutdown computer", "shut down computer"}:
            return ActionRequest("shutdown", risk=RiskLevel.CRITICAL, source="ai")
        if command in {"restart", "restart computer", "reboot", "reboot computer"}:
            return ActionRequest("restart", risk=RiskLevel.CRITICAL, source="ai")

        return None

    def handle(self, text: str, confirmed: bool = False) -> ActionResult:
        request = self.interpret(text)
        if request is None:
            return ActionResult(
                False,
                "I don't know that command yet. Try: open apps, open downloads, find pdf, open chrome, system status, or show desktop.",
            )
        if self.policy.requires_confirmation(request) and not confirmed:
            return ActionResult(False, f"Confirmation required for: {request.name}", {"requires_confirmation": True, "action": request.name})
        if not self.policy.authorize(request, confirmed=confirmed):
            return ActionResult(False, "This action is blocked by the policy engine.")
        return self.system.execute(request)
