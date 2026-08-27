from ai.orchestrator import Orchestrator
from core.actions import RiskLevel


def test_direct_application_aliases_are_canonicalized():
    orch = Orchestrator()
    for command, expected in (("open notepad", "notepad"), ("open vscode", "vscode"), ("open vs code", "vscode"), ("open chrome", "chrome")):
        request = orch.interpret(command)
        assert request is not None
        assert request.name == "launch_app"
        assert request.parameters["app"] == expected
        assert request.risk == RiskLevel.LOW


def test_health_is_direct_runtime_action():
    orch = Orchestrator()
    request = orch.interpret("aios health")
    assert request is not None
    assert request.name == "runtime_health"
