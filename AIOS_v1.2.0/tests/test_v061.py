from ai.orchestrator import Orchestrator


def test_known_app_target_is_mapped_to_app_parameter(monkeypatch):
    orch = Orchestrator()
    monkeypatch.setattr(orch.llm_planner, "plan", lambda text: (_ for _ in ()).throw(AssertionError("LLM should not run")))
    request = orch.interpret("open notepad")
    assert request is not None
    assert request.name == "launch_app"
    assert request.parameters["app"] == "notepad"


def test_known_apps_are_deterministic(monkeypatch):
    orch = Orchestrator()
    monkeypatch.setattr(orch.llm_planner, "plan", lambda text: (_ for _ in ()).throw(AssertionError("LLM should not run")))
    for command, expected in [
        ("open calculator", "calculator"),
        ("open chrome", "chrome"),
        ("open task manager", "task manager"),
    ]:
        request = orch.interpret(command)
        assert request is not None
        assert request.name == "launch_app"
        assert request.parameters["app"] == expected


def test_path_target_is_mapped_to_path():
    orch = Orchestrator()
    request = orch.interpret("open .")
    assert request is not None
    assert request.name == "open_path"
    assert request.parameters["path"] == "."
