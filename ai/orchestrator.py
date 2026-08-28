from __future__ import annotations

from core.actions import ActionRequest, ActionResult, RiskLevel
from core.runtime import AIOSRuntime
from ai.task_planner import TaskPlan, TaskPlanner


class Orchestrator:
    """Unified AIOS control plane over the shared runtime/service container."""

    def __init__(self, runtime: AIOSRuntime | None = None) -> None:
        self.runtime = runtime or AIOSRuntime()
        services = self.runtime.services
        self.policy = services.policy
        self.system = services.system
        self.planner = services.object_planner
        self.context_planner = services.context_planner
        self.llm_planner = services.llm_planner
        self.context = services.context
        self.memory = services.memory
        self.task_planner = TaskPlanner()

    def interpret(self, text: str) -> ActionRequest | None:
        command = " ".join(text.lower().split())
        if command in {"inspect screen ui", "show screen controls", "what buttons are on screen", "show ui controls", "inspect current window"}:
            return ActionRequest("inspect_ui", {}, source="ai")
        for prefix in ("click ", "press button "):
            if command.startswith(prefix):
                target = text[len(prefix):].strip()
                target = target.removesuffix(" button").strip()
                if target:
                    return ActionRequest("click_control", {"target": target}, risk=RiskLevel.MEDIUM, source="ai")

        direct_apps = {
            "open vscode": "vscode",
            "open vs code": "vscode",
            "open visual studio code": "vscode",
            "open code": "vscode",
        }
        if command in direct_apps:
            return ActionRequest("launch_app", {"app": direct_apps[command]}, source="ai")
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
        if intent.action == "launch_app" and not parameters.get("app") and intent.target:
            parameters["app"] = intent.target
        elif intent.action == "open_path" and not parameters.get("path") and intent.target:
            parameters["path"] = intent.target
        elif intent.action == "search_files" and not parameters.get("query") and intent.target:
            parameters["query"] = intent.target

        return ActionRequest(intent.action, parameters, intent.risk, "ai")

    def handle(self, text: str, confirmed: bool = False) -> ActionResult:
        self.runtime.record_command(text)
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

    def make_task_plan(self, text: str) -> TaskPlan | None:
        return self.task_planner.plan(text)

    def execute_task_plan(self, plan: TaskPlan, confirmed: bool = False) -> list[ActionResult]:
        results: list[ActionResult] = []
        for step in plan.steps:
            request = step.request
            if self.policy.requires_confirmation(request) and not confirmed:
                results.append(ActionResult(
                    False,
                    f"Confirmation required for step {step.number}: {request.name}",
                    {"requires_confirmation": True, "action": request.name, "step": step.number},
                ))
                break
            if not self.policy.authorize(request, confirmed=confirmed):
                results.append(ActionResult(False, f"Step {step.number} blocked by the policy engine."))
                break
            result = self.system.execute(request)
            results.append(result)
            if not result.ok:
                break
        return results

    def health(self) -> dict[str, object]:
        return self.runtime.health()
