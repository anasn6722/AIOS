from __future__ import annotations

from core.actions import ActionRequest, ActionResult, RiskLevel
from security.policy import PolicyEngine
from system.adapter import SystemAdapter
from ai.object_planner import ObjectPlanner
from ai.llm_planner import LLMPlanner
from ai.context import ContextEngine
from ai.context_intents import ContextIntentPlanner
from ai.memory import MemoryStore


class Orchestrator:
    """AIOS v0.5 intent layer: structured OS objects -> policy -> system adapter."""

    def __init__(self) -> None:
        self.policy = PolicyEngine()
        self.system = SystemAdapter()
        self.planner = ObjectPlanner()
        self.context_planner = ContextIntentPlanner()
        self.llm_planner = LLMPlanner()
        self.context = ContextEngine()
        self.memory = MemoryStore()
        self.system.context_provider = self.context

    def interpret(self, text: str) -> ActionRequest | None:
        # Deterministic planner always gets first chance. This preserves stable
        # behavior for known OS commands and prevents an optional local LLM from
        # breaking commands that are already understood exactly.
        intent = self.context_planner.plan(text)
        if intent is None:
            intent = self.planner.plan(text)
        if intent is None:
            intent = self.llm_planner.plan(text)
        if intent is None:
            return None

        parameters = dict(intent.parameters)
        if intent.target is not None:
            parameters.setdefault("target", intent.target)

        # Normalize object-model targets into the parameter names expected by
        # the execution adapter. This is the critical bridge between v0.5/v0.6
        # intents and the existing v0.3 system-action API.
        if intent.action == "launch_app" and not parameters.get("app") and intent.target:
            parameters["app"] = intent.target
        elif intent.action == "open_path" and not parameters.get("path") and intent.target:
            parameters["path"] = intent.target
        elif intent.action == "search_files" and not parameters.get("query") and intent.target:
            parameters["query"] = intent.target

        return ActionRequest(intent.action, parameters, intent.risk, "ai")

    def handle(self, text: str, confirmed: bool = False) -> ActionResult:
        self.context.record_command(text)
        self.memory.record_command(text)
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
