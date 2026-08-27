from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from apps.launcher import AppEntry, AppLauncher
from files.manager import FileEntry, FileManager


class ObjectType(str, Enum):
    APPLICATION = "application"
    FILE = "file"
    FOLDER = "folder"
    WORKSPACE = "workspace"
    PROCESS = "process"
    TASK = "task"
    SETTING = "setting"


@dataclass(frozen=True)
class OSObject:
    object_type: ObjectType
    name: str
    identifier: str
    metadata: dict[str, object] = field(default_factory=dict)


class ObjectResolver:
    """Resolves natural-language OS references into typed AIOS objects."""

    def __init__(self, file_manager: FileManager | None = None, app_launcher: AppLauncher | None = None) -> None:
        self.files = file_manager or FileManager()
        self.apps = app_launcher

    def app_object(self, app: AppEntry) -> OSObject:
        return OSObject(ObjectType.APPLICATION, app.name, app.executable, {"source": app.source})

    def file_object(self, entry: FileEntry) -> OSObject:
        kind = ObjectType.FOLDER if entry.is_dir else ObjectType.FILE
        return OSObject(kind, entry.name, str(entry.path), {"size": entry.size})

    def resolve_path(self, value: str) -> OSObject | None:
        path = Path(value).expanduser()
        if not path.exists():
            return None
        return OSObject(
            ObjectType.FOLDER if path.is_dir() else ObjectType.FILE,
            path.name or str(path),
            str(path),
            {"parent": str(path.parent)},
        )

    def resolve_special_folder(self, target: str) -> OSObject | None:
        normalized = " ".join(target.lower().split())
        folders = {
            "home": Path.home(),
            "my home": Path.home(),
            "downloads": Path.home() / "Downloads",
            "my downloads": Path.home() / "Downloads",
            "desktop": Path.home() / "Desktop",
            "documents": Path.home() / "Documents",
            "my documents": Path.home() / "Documents",
            "pictures": Path.home() / "Pictures",
            "videos": Path.home() / "Videos",
            "music": Path.home() / "Music",
        }
        path = folders.get(normalized)
        if path is None:
            return None
        path.mkdir(parents=True, exist_ok=True)
        return OSObject(ObjectType.FOLDER, path.name or normalized.title(), str(path), {"special": normalized})
