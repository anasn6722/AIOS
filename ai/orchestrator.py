from __future__ import annotations

import re
from pathlib import Path

from core.actions import ActionRequest, ActionResult, RiskLevel
from security.policy import PolicyEngine
from system.adapter import SystemAdapter


class Orchestrator:
    """Natural-language command router for AIOS v0.3.

    This is intentionally deterministic for system-control actions. A future LLM
    planner will propose ActionRequest objects, but the PolicyEngine remains the
    mandatory gate before execution.
    """

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

        if command in {"lock computer", "lock pc", "lock my computer"}:
            return ActionRequest("lock_computer", risk=RiskLevel.HIGH, source="ai")

        if command in {"shutdown", "shut down", "shutdown computer", "shut down computer"}:
            return ActionRequest("shutdown", risk=RiskLevel.CRITICAL, source="ai")

        if command in {"restart", "restart computer", "reboot", "reboot computer"}:
            return ActionRequest("restart", risk=RiskLevel.CRITICAL, source="ai")

        for prefix in ("open ", "launch ", "start "):
            if command.startswith(prefix):
                target = original[len(prefix):].strip().strip('"')
                if not target:
                    return None
                # Explicit filesystem paths are handled as paths. Known app names are always
                # routed to the application launcher before any filesystem existence check.
                known_apps = {
                    "notepad", "calculator", "calc", "chrome", "google chrome", "edge",
                    "microsoft edge", "terminal", "windows terminal", "task manager",
                    "taskmgr", "explorer", "file explorer", "paint", "powershell",
                    "cmd", "command prompt", "vscode", "visual studio code",
                }
                normalized_target = target.lower().strip()
                if normalized_target in known_apps:
                    return ActionRequest(
                        "launch_app",
                        parameters={"app": target},
                        risk=RiskLevel.LOW,
                        source="ai",
                    )

                path = Path(target).expanduser()
                if path.exists() or target in {".", "~"}:
                    return ActionRequest(
                        "open_path",
                        parameters={"path": target},
                        risk=RiskLevel.LOW,
                        source="ai",
                    )
                if re.match(r"^[A-Za-z]:[\\/]", target) or target.startswith(("\\\\", "/")):
                    return ActionRequest(
                        "open_path",
                        parameters={"path": target},
                        risk=RiskLevel.LOW,
                        source="ai",
                    )
                return ActionRequest(
                    "launch_app",
                    parameters={"app": target},
                    risk=RiskLevel.LOW,
                    source="ai",
                )

        return None

    def handle(self, text: str, confirmed: bool = False) -> ActionResult:
        request = self.interpret(text)
        if request is None:
            return ActionResult(
                False,
                "I don't know that command yet. Try: open chrome, open downloads, show desktop, system status, lock computer, restart, or shutdown.",
            )

        if self.policy.requires_confirmation(request) and not confirmed:
            return ActionResult(
                False,
                f"Confirmation required for: {request.name}",
                {"requires_confirmation": True, "action": request.name},
            )

        if not self.policy.authorize(request, confirmed=confirmed):
            return ActionResult(False, "This action is blocked by the policy engine.")

        return self.system.execute(request)
