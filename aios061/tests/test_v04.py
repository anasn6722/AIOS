from ai.orchestrator import Orchestrator


def test_app_launcher_command() -> None:
    req = Orchestrator().interpret("open apps")
    assert req is not None and req.name == "list_apps"


def test_downloads_command() -> None:
    req = Orchestrator().interpret("open downloads")
    assert req is not None and req.name == "open_path"


def test_file_search_command() -> None:
    req = Orchestrator().interpret("find pdf")
    assert req is not None and req.name == "search_files"
    assert req.parameters["query"] == "pdf"


def test_high_risk_behavior_remains() -> None:
    result = Orchestrator().handle("shutdown")
    assert not result.ok
    assert result.data["requires_confirmation"] is True
