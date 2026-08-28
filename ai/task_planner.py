from __future__ import annotations

import re
from pathlib import Path
from dataclasses import dataclass
from typing import Iterable

from ai.intent import OSIntent
from core.actions import ActionRequest, RiskLevel


@dataclass(frozen=True)
class TaskStep:
    number: int
    request: ActionRequest
    explanation: str


@dataclass(frozen=True)
class TaskPlan:
    goal: str
    steps: tuple[TaskStep, ...]
    requires_confirmation: bool

    @property
    def summary(self) -> str:
        lines = [f"Goal: {self.goal}"]
        for step in self.steps:
            risk = step.request.risk.value.upper()
            lines.append(f"{step.number}. {step.explanation} [{risk}]")
        if self.requires_confirmation:
            lines.append("Confirmation required before the plan executes risky steps.")
        else:
            lines.append("All steps are safe/low-risk and can execute automatically.")
        return "\n".join(lines)


class TaskPlanner:
    """Build deterministic multi-step AIOS plans from common user goals.

    The planner emits only ActionRequest objects. Execution stays behind the
    Orchestrator policy gate, so this layer never calls Windows APIs directly.
    """

    APP_ALIASES = {
        "notepad": "notepad",
        "chrome": "chrome",
        "google chrome": "chrome",
        "vscode": "vscode",
        "vs code": "vscode",
        "visual studio code": "vscode",
        "calculator": "calculator",
        "calc": "calculator",
        "task manager": "task manager",
        "terminal": "terminal",
    }

    def plan(self, goal: str) -> TaskPlan | None:
        original = goal.strip()
        command = " ".join(original.lower().split())
        if not command:
            return None

        # Common explicit multi-app request: "open chrome and vscode"
        if command.startswith(("open ", "launch ", "start ")) and " and " in command:
            payload = re.sub(r"^(open|launch|start)\s+", "", command).strip()
            parts = [p.strip() for p in re.split(r"\s+and\s+", payload) if p.strip()]
            requests: list[ActionRequest] = []
            explanations: list[str] = []
            for part in parts:
                alias = self.APP_ALIASES.get(part)
                if alias is None:
                    return None
                requests.append(ActionRequest("launch_app", {"app": alias}, RiskLevel.LOW, "ai-plan"))
                explanations.append(f"Launch {alias}")
            if len(requests) >= 2:
                return self._make_plan(original, requests, explanations)

        if command in {
            "prepare my coding workspace",
            "prepare coding workspace",
            "set up my coding environment",
            "setup my coding environment",
        }:
            project_candidates = [
                str(Path.home() / "Desktop" / "Projects"),
                str(Path.home() / "Documents" / "Projects"),
            ]
            requests = [
                ActionRequest("open_path", {"path": project_candidates[0]}, RiskLevel.LOW, "ai-plan"),
                ActionRequest("launch_app", {"app": "vscode"}, RiskLevel.LOW, "ai-plan"),
                ActionRequest("launch_app", {"app": "chrome"}, RiskLevel.LOW, "ai-plan"),
                ActionRequest("launch_app", {"app": "terminal"}, RiskLevel.LOW, "ai-plan"),
            ]
            explanations = [
                "Open the primary Projects folder",
                "Launch VS Code",
                "Launch Chrome",
                "Launch Terminal",
            ]
            return self._make_plan(original, requests, explanations)

        if command in {
            "prepare my study workspace",
            "prepare study workspace",
            "set up my study environment",
        }:
            documents = str(Path.home() / "Documents")
            downloads = str(Path.home() / "Downloads")
            requests = [
                ActionRequest("open_path", {"path": documents}, RiskLevel.LOW, "ai-plan"),
                ActionRequest("open_path", {"path": downloads}, RiskLevel.LOW, "ai-plan"),
                ActionRequest("launch_app", {"app": "chrome"}, RiskLevel.LOW, "ai-plan"),
            ]
            explanations = [
                "Open Documents",
                "Open Downloads",
                "Launch Chrome",
            ]
            return self._make_plan(original, requests, explanations)

        if command in {"close development apps", "close everything related to development"}:
            requests = [
                ActionRequest("close_process", {"target": target}, RiskLevel.MEDIUM, "ai-plan")
                for target in ("code", "chrome", "terminal")
            ]
            explanations = [f"Request termination of {target}" for target in ("code", "chrome", "terminal")]
            return self._make_plan(original, requests, explanations)

        # A broad "launch my work apps" goal can be handled safely with a
        # predictable set of apps, but only if the user asked explicitly.
        if command in {"launch my coding apps", "open my coding apps", "launch development apps"}:
            requests = [
                ActionRequest("launch_app", {"app": "vscode"}, RiskLevel.LOW, "ai-plan"),
                ActionRequest("launch_app", {"app": "chrome"}, RiskLevel.LOW, "ai-plan"),
                ActionRequest("launch_app", {"app": "terminal"}, RiskLevel.LOW, "ai-plan"),
            ]
            explanations = ["Launch VS Code", "Launch Chrome", "Launch Terminal"]
            return self._make_plan(original, requests, explanations)

        return None

    @staticmethod
    def _make_plan(goal: str, requests: Iterable[ActionRequest], explanations: Iterable[str]) -> TaskPlan:
        steps = tuple(
            TaskStep(index, request, explanation)
            for index, (request, explanation) in enumerate(zip(requests, explanations), 1)
        )
        requires = any(step.request.risk in {RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL} for step in steps)
        return TaskPlan(goal, steps, requires)
