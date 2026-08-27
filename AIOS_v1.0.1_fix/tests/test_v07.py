from pathlib import Path
import tempfile

from ai.context import ContextEngine
from ai.context_intents import ContextIntentPlanner
from ai.memory import MemoryStore


def test_context_snapshot_has_safe_fields():
    engine = ContextEngine()
    snap = engine.snapshot()
    assert "active_window" in snap
    assert "cpu_percent" in snap
    assert "ram_percent" in snap
    assert isinstance(snap["recent_commands"], list)


def test_context_records_recent_commands():
    engine = ContextEngine(recent_limit=2)
    engine.record_command("one")
    engine.record_command("two")
    engine.record_command("three")
    assert engine.recent_commands == ["two", "three"]


def test_context_intents():
    planner = ContextIntentPlanner()
    assert planner.plan("show my context").action == "context_snapshot"
    assert planner.plan("what app am i using").action == "active_window"


def test_memory_persists_preferences_and_recent_commands():
    with tempfile.TemporaryDirectory() as tmp:
        store = MemoryStore(Path(tmp) / "memory.json")
        store.remember("preferred_workspace", "AIOS")
        store.record_command("open my project")
        reloaded = MemoryStore(Path(tmp) / "memory.json")
        assert reloaded.get("preferred_workspace") == "AIOS"
        assert reloaded.data["recent_commands"] == ["open my project"]
