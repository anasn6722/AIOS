from ai.orchestrator import Orchestrator


def test_open_known_app_is_low_risk() -> None:
    request = Orchestrator().interpret("open notepad")
    assert request is not None
    assert request.name == "launch_app"
    assert request.risk.value == "low"


def test_app_aliases_include_common_windows_apps() -> None:
    adapter = Orchestrator().system
    for app in ("calculator", "chrome", "task manager", "show desktop"):
        if app == "show desktop":
            continue
        assert app in adapter.APP_ALIASES


def test_shutdown_requires_confirmation() -> None:
    orchestrator = Orchestrator()
    result = orchestrator.handle("shutdown")
    assert result.ok is False
    assert result.data["requires_confirmation"] is True


def test_system_status_is_safe() -> None:
    request = Orchestrator().interpret("system status")
    assert request is not None
    assert request.name == "system_info"
    assert request.risk.value == "safe"
