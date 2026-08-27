from core.runtime import AIOSRuntime
from core.services import AIOSServices
from ai.orchestrator import Orchestrator


def test_service_container_builds() -> None:
    services = AIOSServices.build()
    assert services.policy is not None
    assert services.system is not None
    assert services.context is not None
    assert services.workspace_engine is not None


def test_runtime_health_is_noninvasive() -> None:
    runtime = AIOSRuntime()
    health = runtime.health()
    assert health["runtime"] == "online"
    assert health["services"]["policy"] is True
    assert health["services"]["context"] is True


def test_orchestrator_uses_shared_runtime() -> None:
    runtime = AIOSRuntime()
    orchestrator = Orchestrator(runtime)
    assert orchestrator.system is runtime.services.system
    result = orchestrator.handle("aios health")
    assert result.ok is True
    assert result.data["runtime"] == "online"


def test_health_aliases_are_executable() -> None:
    runtime = AIOSRuntime()
    orchestrator = Orchestrator(runtime)
    for text in ("aios health", "system health", "show aios health"):
        result = orchestrator.handle(text)
        assert result.ok is True
        assert result.data["runtime"] == "online"


def test_vscode_alias_is_configured() -> None:
    from system.adapter import SystemAdapter
    aliases = SystemAdapter.APP_ALIASES
    assert "vscode" in aliases
    assert "code.exe" in aliases["vscode"]
