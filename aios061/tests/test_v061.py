from pathlib import Path

from ai.orchestrator import Orchestrator


def test_deterministic_known_apps_win_over_llm(monkeypatch):
    orch = Orchestrator()
    monkeypatch.setattr(orch.llm_planner, "plan", lambda text: (_ for _ in ()).throw(AssertionError("LLM should not run")))

    for command, expected in [
        ("open notepad", "launch_app"),
        ("open calculator", "launch_app"),
        ("open chrome", "launch_app"),
        ("open task manager", "launch_app"),
    ]:
        request = orch.interpret(command)
        assert request is not None
        assert request.name == expected
        assert request.parameters.get("app") in {"notepad", "calculator", "chrome", "task manager"}


def test_paths_still_resolve_deterministically():
    orch = Orchestrator()
    request = orch.interpret("open .")
    assert request is not None
    assert request.name == "open_path"
    assert request.parameters["path"] == "."
