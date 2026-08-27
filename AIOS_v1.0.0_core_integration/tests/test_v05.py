from ai.object_planner import ObjectPlanner
from ai.orchestrator import Orchestrator
from core.actions import RiskLevel


def test_open_coding_project_object() -> None:
    intent = ObjectPlanner().plan("open my coding project")
    assert intent is not None
    assert intent.action == "open_path"
    assert intent.target_type == "workspace"
    assert intent.confidence < 1.0


def test_running_processes_object() -> None:
    intent = ObjectPlanner().plan("what apps are running")
    assert intent is not None and intent.action == "list_processes"
    assert intent.target_type == "process"


def test_modified_today_object() -> None:
    intent = ObjectPlanner().plan("show files modified today")
    assert intent is not None and intent.action == "search_files_modified"
    assert intent.target_type == "file"


def test_file_search_object() -> None:
    req = Orchestrator().interpret("find university pdf")
    assert req is not None and req.name == "search_files"
    assert req.parameters["query"] == "university pdf"
    assert req.parameters["target"] == "university pdf"


def test_close_process_is_confirmation_gated() -> None:
    req = Orchestrator().interpret("close chrome")
    assert req is not None and req.name == "close_process"
    assert req.risk == RiskLevel.MEDIUM
    result = Orchestrator().handle("close chrome")
    assert not result.ok
    assert result.data["requires_confirmation"] is True
