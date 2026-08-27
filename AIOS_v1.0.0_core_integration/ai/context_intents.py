from __future__ import annotations

from ai.intent import OSIntent


class ContextIntentPlanner:
    """Plans read-only context queries before the normal object planner."""

    COMMANDS = {
        "what's my current context": "context_snapshot",
        "what is my current context": "context_snapshot",
        "show my context": "context_snapshot",
        "show current context": "context_snapshot",
        "what window am i using": "active_window",
        "what window is active": "active_window",
        "what app am i using": "active_window",
        "what apps are open": "open_windows",
        "show recent commands": "recent_commands",
        "what did i just do": "recent_commands",
    }

    def plan(self, text: str) -> OSIntent | None:
        command = " ".join(text.lower().split())
        action = self.COMMANDS.get(command)
        if not action:
            return None
        return OSIntent(action, target_type="context", confidence=1.0, explanation="Read current AIOS context.")
