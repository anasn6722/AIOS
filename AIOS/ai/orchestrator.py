from __future__ import annotations

from core.actions import ActionRequest, ActionResult, RiskLevel
from security.policy import PolicyEngine
from system.adapter import SystemAdapter


class Orchestrator:
    """Initial AI command boundary. A real LLM planner will plug in later."""

    def __init__(self) -> None:
        self.policy = PolicyEngine()
        self.system = SystemAdapter()

    def interpret(self, text: str) -> ActionRequest | None:
        command = text.strip().lower()
        if not command:
            return None

        if command in {"system info", "system status", "how is my system"}:
            return ActionRequest("system_info", risk=RiskLevel.SAFE, source="ai")

        if command.startswith("open "):
            path = text.strip()[5:].strip().strip('"')
            return ActionRequest(
                "open_path",
                parameters={"path": path},
                risk=RiskLevel.LOW,
                source="ai",
            )

        return None

    def handle(self, text: str, confirmed: bool = False) -> ActionResult:
        request = self.interpret(text)
        if request is None:
            return ActionResult(False, "I don't know that command yet.")

        if not self.policy.authorize(request, confirmed=confirmed):
            return ActionResult(False, "This action requires confirmation.")

        return self.system.execute(request)
