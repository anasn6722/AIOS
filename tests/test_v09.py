from pathlib import Path
from tempfile import TemporaryDirectory

from ai.workspaces import Workspace, WorkspaceStore


def test_workspace_store_defaults_and_case_insensitive_lookup():
    with TemporaryDirectory() as tmp:
        store = WorkspaceStore(Path(tmp) / "workspaces.json")
        store.ensure_defaults()
        assert {w.name for w in store.list()} == {"Business", "Coding", "Study"}
        assert store.get("coding").name == "Coding"


def test_workspace_persistence_and_capture():
    with TemporaryDirectory() as tmp:
        path = Path(tmp) / "workspaces.json"
        store = WorkspaceStore(path)
        ws = store.capture("My Dev", "test", ["chrome", "chrome", "vscode"], [" C:\\Projects ", "C:\\Projects"])
        assert ws.apps == ["chrome", "vscode"]
        assert ws.folders == ["C:\\Projects"]
        assert store.get("my dev").description == "test"


def test_workspace_delete():
    with TemporaryDirectory() as tmp:
        store = WorkspaceStore(Path(tmp) / "workspaces.json")
        store.capture("Temp", "", [], [])
        assert store.delete("temp") is True
        assert store.get("Temp") is None
