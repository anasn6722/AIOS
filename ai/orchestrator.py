from __future__ import annotations

from core.actions import ActionRequest, ActionResult, RiskLevel
from security.policy import PolicyEngine
from system.adapter import SystemAdapter
from ai.object_planner import ObjectPlanner


class Orchestrator:
    """AIOS v0.5 intent layer: structured OS objects -> policy -> system adapter."""

    def __init__(self) -> None:
        self.policy = PolicyEngine()
        self.system = SystemAdapter()
        self.planner = ObjectPlanner()

    def interpret(self, text: str) -> ActionRequest | None:
        intent = self.planner.plan(text)
        if intent is None:
            return None
        return ActionRequest(
            intent.action,
            {**intent.parameters, **({"target": intent.target} if intent.target is not None else {})},
            intent.risk,
            "ai",
        )

    def handle(self, text: str, confirmed: bool = False) -> ActionResult:
        request = self.interpret(text)
        if request is None:
            return ActionResult(
                False,
                "I don't understand that OS intent yet. Try: open my coding project, find pdf, show files modified today, or what apps are running.",
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
