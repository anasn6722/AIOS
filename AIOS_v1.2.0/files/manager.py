from __future__ import annotations

import os
import shutil
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class FileEntry:
    name: str
    path: Path
    is_dir: bool
    size: int


class FileManager:
    """Safe local file operations used by the AIOS desktop UI."""

    def list_dir(self, directory: str | Path) -> list[FileEntry]:
        path = Path(directory).expanduser()
        if not path.exists() or not path.is_dir():
            raise FileNotFoundError(f"Folder does not exist: {path}")
        entries: list[FileEntry] = []
        for item in sorted(path.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower())):
            try:
                size = item.stat().st_size if item.is_file() else 0
            except OSError:
                size = 0
            entries.append(FileEntry(item.name, item, item.is_dir(), size))
        return entries

    def search(self, root: str | Path, query: str, limit: int = 100) -> list[FileEntry]:
        base = Path(root).expanduser()
        if not base.exists():
            raise FileNotFoundError(f"Folder does not exist: {base}")
        query = query.strip().lower()
        if not query:
            return []
        results: list[FileEntry] = []
        try:
            iterator = base.rglob("*")
            for item in iterator:
                if query in item.name.lower():
                    try:
                        size = item.stat().st_size if item.is_file() else 0
                    except OSError:
                        size = 0
                    results.append(FileEntry(item.name, item, item.is_dir(), size))
                    if len(results) >= limit:
                        break
        except (OSError, PermissionError):
            pass
        return results

    def create_folder(self, parent: str | Path, name: str) -> Path:
        clean = name.strip()
        if not clean or clean in {".", ".."}:
            raise ValueError("Invalid folder name")
        target = Path(parent).expanduser() / clean
        target.mkdir(parents=False, exist_ok=False)
        return target

    def copy(self, source: str | Path, destination: str | Path) -> Path:
        src = Path(source).expanduser()
        dst = Path(destination).expanduser()
        if src.is_dir():
            target = dst / src.name if dst.exists() and dst.is_dir() else dst
            shutil.copytree(src, target)
            return target
        target = dst / src.name if dst.exists() and dst.is_dir() else dst
        shutil.copy2(src, target)
        return target

    def move(self, source: str | Path, destination: str | Path) -> Path:
        src = Path(source).expanduser()
        dst = Path(destination).expanduser()
        target = dst / src.name if dst.exists() and dst.is_dir() else dst
        return Path(shutil.move(str(src), str(target)))

    def trash(self, target: str | Path) -> None:
        """Move to Recycle Bin where available; no permanent deletion here."""
        path = Path(target).expanduser()
        if os.name == "nt":
            import send2trash  # type: ignore

            send2trash.send2trash(str(path))
            return
        raise OSError("Recycle Bin integration is only implemented for Windows.")
