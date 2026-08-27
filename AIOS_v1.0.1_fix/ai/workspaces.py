from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from apps.launcher import AppLauncher


WORKSPACE_DIR = Path.home() / ".aios"
WORKSPACE_FILE = WORKSPACE_DIR / "workspaces.json"


@dataclass
class Workspace:
    name: str
    description: str = ""
    apps: list[str] = field(default_factory=list)
    folders: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class WorkspaceStore:
    """Small local persistent store for AIOS workspace profiles."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or WORKSPACE_FILE
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _load(self) -> dict[str, Workspace]:
        if not self.path.exists():
            return {}
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
            return {
                item["name"]: Workspace(**item)
                for item in payload.get("workspaces", [])
                if isinstance(item, dict) and item.get("name")
            }
        except (OSError, ValueError, TypeError):
            return {}

    def _save(self, workspaces: dict[str, Workspace]) -> None:
        data = {"version": 1, "workspaces": [asdict(ws) for ws in workspaces.values()]}
        self.path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def ensure_defaults(self) -> None:
        workspaces = self._load()
        defaults = {
            "Coding": Workspace(
                "Coding",
                "Development workspace",
                apps=["vscode", "chrome", "terminal"],
                folders=[str(Path.home() / "Desktop" / "Projects")],
            ),
            "Study": Workspace(
                "Study",
                "Focused study workspace",
                apps=["chrome", "notepad"],
                folders=[str(Path.home() / "Documents"), str(Path.home() / "Downloads")],
            ),
            "Business": Workspace(
                "Business",
                "Business workspace",
                apps=["chrome", "edge"],
                folders=[str(Path.home() / "Documents")],
            ),
        }
        changed = False
        for name, ws in defaults.items():
            if name not in workspaces:
                workspaces[name] = ws
                changed = True
        if changed:
            self._save(workspaces)

    def list(self) -> list[Workspace]:
        self.ensure_defaults()
        return sorted(self._load().values(), key=lambda ws: ws.name.lower())

    def get(self, name: str) -> Workspace | None:
        self.ensure_defaults()
        workspaces = self._load()
        return workspaces.get(name) or next(
            (ws for key, ws in workspaces.items() if key.lower() == name.lower()), None
        )

    def save(self, workspace: Workspace) -> None:
        workspaces = self._load()
        workspaces[workspace.name] = workspace
        self._save(workspaces)

    def delete(self, name: str) -> bool:
        workspaces = self._load()
        key = next((key for key in workspaces if key.lower() == name.lower()), None)
        if key is None:
            return False
        del workspaces[key]
        self._save(workspaces)
        return True

    def capture(self, name: str, description: str, apps: list[str], folders: list[str]) -> Workspace:
        workspace = Workspace(
            name=name.strip(),
            description=description.strip(),
            apps=sorted(dict.fromkeys(a.strip() for a in apps if a.strip()), key=str.lower),
            folders=sorted(dict.fromkeys(f.strip() for f in folders if f.strip()), key=str.lower),
            metadata={"platform": os.name},
        )
        self.save(workspace)
        return workspace


class WorkspaceEngine:
    """Resolve workspace profiles into safe launch/open operations."""

    def __init__(self, store: WorkspaceStore | None = None, launcher: AppLauncher | None = None) -> None:
        self.store = store or WorkspaceStore()
        self.launcher = launcher

    def resolve(self, name: str) -> Workspace | None:
        return self.store.get(name)

    def launchable_apps(self, workspace: Workspace) -> list[str]:
        if not self.launcher:
            return list(workspace.apps)
        discovered = {entry.name.lower(): entry.name for entry in self.launcher.discover()}
        selected: list[str] = []
        for app in workspace.apps:
            selected.append(discovered.get(app.lower(), app))
        return selected
