from __future__ import annotations

from ai.llm_planner import LLMPlanner
from ai.object_planner import ObjectPlanner
from core.actions import ActionRequest, ActionResult
from security.policy import PolicyEngine
from system.adapter import SystemAdapter


class Orchestrator:
    """AIOS intent pipeline with deterministic-first routing.

    Exact, known OS commands are resolved locally before the optional LLM is
    consulted. This prevents a local model from accidentally changing the
    meaning of reliable system/app commands.
    """

    def __init__(self) -> None:
        self.policy = PolicyEngine()
        self.system = SystemAdapter()
        self.planner = ObjectPlanner()
        self.llm_planner = LLMPlanner()

    def interpret(self, text: str) -> ActionRequest | None:
        # v0.6.1: deterministic commands always win.
        intent = self.planner.plan(text)
        if intent is None:
            intent = self.llm_planner.plan(text)
        if intent is None:
            return None
        parameters = dict(intent.parameters)
        if intent.target is not None:
            # Normalize the object-model target into the parameter expected by
            # the concrete system action. Keep target as metadata for future
            # reasoning, but never rely on it for execution.
            parameters.setdefault("target", intent.target)
            if intent.action == "launch_app":
                parameters.setdefault("app", intent.target)
            elif intent.action == "open_path":
                parameters.setdefault("path", intent.target)
            elif intent.action == "close_process":
                parameters.setdefault("target", intent.target)
            elif intent.action in {"search_files", "search_files_modified"}:
                parameters.setdefault("query", intent.target)
        return ActionRequest(intent.action, parameters, intent.risk, "ai")

    def handle(self, text: str, confirmed: bool = False) -> ActionResult:
        request = self.interpret(text)
        if request is None:
            return ActionResult(
                False,
                "I don't understand that OS intent yet. Try: open notepad, open chrome, system status, find pdf, or what apps are running.",
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
