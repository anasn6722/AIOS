from ai.context import ContextEngine
from ai.context_intents import ContextIntentPlanner

def test_context_intents_exact_commands():
    planner = ContextIntentPlanner()
    assert planner.plan("what app am i using").action == "active_window"
    assert planner.plan("show my context").action == "context_snapshot"
    assert planner.plan("show recent commands").action == "recent_commands"

def test_recent_command_recording():
    context = ContextEngine()
    context.record_command("open notepad")
    context.record_command("show my context")
    assert context.snapshot()["recent_commands"] == ["open notepad", "show my context"]
