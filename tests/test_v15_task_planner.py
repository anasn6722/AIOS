from ai.task_planner import TaskPlanner
from core.actions import RiskLevel


def test_multi_app_plan():
    plan = TaskPlanner().plan("open chrome and vscode")
    assert plan is not None
    assert len(plan.steps) == 2
    assert [step.request.parameters["app"] for step in plan.steps] == ["chrome", "vscode"]
    assert plan.requires_confirmation is False


def test_coding_workspace_plan():
    plan = TaskPlanner().plan("prepare my coding workspace")
    assert plan is not None
    assert len(plan.steps) == 4
    assert all(step.request.risk == RiskLevel.LOW for step in plan.steps)


def test_risky_plan_requires_confirmation():
    plan = TaskPlanner().plan("close development apps")
    assert plan is not None
    assert plan.requires_confirmation is True
    assert all(step.request.risk == RiskLevel.MEDIUM for step in plan.steps)
