from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from apps.launcher import AppLauncher
from files.manager import FileManager
from security.policy import PolicyEngine
from system.adapter import SystemAdapter
from ai.context import ContextEngine
from ai.llm_planner import LLMPlanner
from ai.memory import MemoryStore
from ai.object_planner import ObjectPlanner
from ai.context_intents import ContextIntentPlanner
from ai.workspaces import WorkspaceEngine, WorkspaceStore
from ai.voice import VoiceEngine
from ai.vision import VisionEngine


class Service(Protocol):
    """Marker protocol for AIOS services."""


@dataclass
class AIOSServices:
    """Single dependency container shared by the shell and AI control plane."""

    policy: PolicyEngine
    system: SystemAdapter
    context: ContextEngine
    memory: MemoryStore
    object_planner: ObjectPlanner
    context_planner: ContextIntentPlanner
    llm_planner: LLMPlanner
    file_manager: FileManager
    app_launcher: AppLauncher
    workspace_store: WorkspaceStore
    workspace_engine: WorkspaceEngine
    voice: VoiceEngine
    vision: VisionEngine

    @classmethod
    def build(cls) -> "AIOSServices":
        policy = PolicyEngine()
        system = SystemAdapter()
        context = ContextEngine()
        memory = MemoryStore()
        object_planner = ObjectPlanner()
        context_planner = ContextIntentPlanner()
        llm_planner = LLMPlanner()
        file_manager = FileManager()
        app_launcher = AppLauncher(system)
        workspace_store = WorkspaceStore()
        workspace_engine = WorkspaceEngine(workspace_store, app_launcher)
        voice = VoiceEngine()
        vision = VisionEngine(context)

        system.context_provider = context
        system.memory_provider = memory

        return cls(
            policy=policy,
            system=system,
            context=context,
            memory=memory,
            object_planner=object_planner,
            context_planner=context_planner,
            llm_planner=llm_planner,
            file_manager=file_manager,
            app_launcher=app_launcher,
            workspace_store=workspace_store,
            workspace_engine=workspace_engine,
            voice=voice,
            vision=vision,
        )

    def health(self) -> dict[str, Any]:
        """Return a non-invasive service health snapshot."""
        return {
            "policy": True,
            "system": True,
            "context": True,
            "memory": self.memory.path.exists(),
            "object_planner": True,
            "llm_planner": bool(getattr(self.llm_planner.client.config, "enabled", False)),
            "file_manager": True,
            "app_launcher": True,
            "workspace_engine": True,
            "voice": self.voice.status(),
            "vision": True,
        }
