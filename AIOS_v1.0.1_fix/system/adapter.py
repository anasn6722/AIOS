from __future__ import annotations

import ctypes
import os
import platform
import shutil
import subprocess
from pathlib import Path

import psutil

from core.actions import ActionRequest, ActionResult
from files.manager import FileManager
from apps.launcher import AppLauncher


class SystemAdapter:
    """Explicit Windows/system adapter. AI never calls OS APIs directly."""

    def __init__(self) -> None:
        self.file_manager = FileManager()
        self.app_launcher = AppLauncher(self)
        self.context_provider = None
        self.memory_provider = None
        self.runtime_provider = None

    APP_ALIASES = {
        "notepad": ["notepad.exe"],
        "calculator": ["calc.exe"],
        "calc": ["calc.exe"],
        "paint": ["mspaint.exe"],
        "cmd": ["cmd.exe"],
        "powershell": ["powershell.exe", "pwsh.exe"],
        "terminal": ["wt.exe", "WindowsTerminal.exe"],
        "windows terminal": ["wt.exe", "WindowsTerminal.exe"],
        "explorer": ["explorer.exe"],
        "file explorer": ["explorer.exe"],
        "task manager": ["taskmgr.exe"],
        "taskmgr": ["taskmgr.exe"],
        "chrome": ["chrome.exe"],
        "google chrome": ["chrome.exe"],
        "edge": ["msedge.exe"],
        "microsoft edge": ["msedge.exe"],
        "vscode": ["code.exe", "code.cmd"],
        "vs code": ["code.exe", "code.cmd"],
        "visual studio code": ["code.exe", "code.cmd"],
        "code": ["code.exe", "code.cmd"],
    }

    COMMON_WINDOWS_APPS = {
        "chrome": [
            Path(os.environ.get("PROGRAMFILES", r"C:\Program Files"))
            / "Google/Chrome/Application/chrome.exe",
            Path(os.environ.get("PROGRAMFILES(X86)", r"C:\Program Files (x86)"))
            / "Google/Chrome/Application/chrome.exe",
            Path(os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData/Local")))
            / "Google/Chrome/Application/chrome.exe",
        ],
        "google chrome": [
            Path(os.environ.get("PROGRAMFILES", r"C:\Program Files"))
            / "Google/Chrome/Application/chrome.exe",
            Path(os.environ.get("PROGRAMFILES(X86)", r"C:\Program Files (x86)"))
            / "Google/Chrome/Application/chrome.exe",
            Path(os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData/Local")))
            / "Google/Chrome/Application/chrome.exe",
        ],
        "edge": [
            Path(os.environ.get("PROGRAMFILES(X86)", r"C:\Program Files (x86)"))
            / "Microsoft/Edge/Application/msedge.exe",
            Path(os.environ.get("PROGRAMFILES", r"C:\Program Files"))
            / "Microsoft/Edge/Application/msedge.exe",
            Path(os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData/Local")))
            / "Microsoft/Edge/Application/msedge.exe",
        ],
        "microsoft edge": [
            Path(os.environ.get("PROGRAMFILES(X86)", r"C:\Program Files (x86)"))
            / "Microsoft/Edge/Application/msedge.exe",
            Path(os.environ.get("PROGRAMFILES", r"C:\Program Files"))
            / "Microsoft/Edge/Application/msedge.exe",
            Path(os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData/Local")))
            / "Microsoft/Edge/Application/msedge.exe",
        ],
        "vscode": [
            Path(os.environ.get("PROGRAMFILES", r"C:\Program Files")) / "Microsoft VS Code/Code.exe",
            Path(os.environ.get("PROGRAMFILES(X86)", r"C:\Program Files (x86)")) / "Microsoft VS Code/Code.exe",
            Path(os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData/Local"))) / "Programs/Microsoft VS Code/Code.exe",
        ],
        "vs code": [
            Path(os.environ.get("PROGRAMFILES", r"C:\Program Files")) / "Microsoft VS Code/Code.exe",
            Path(os.environ.get("PROGRAMFILES(X86)", r"C:\Program Files (x86)")) / "Microsoft VS Code/Code.exe",
            Path(os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData/Local"))) / "Programs/Microsoft VS Code/Code.exe",
        ],
        "visual studio code": [
            Path(os.environ.get("PROGRAMFILES", r"C:\Program Files")) / "Microsoft VS Code/Code.exe",
            Path(os.environ.get("PROGRAMFILES(X86)", r"C:\Program Files (x86)")) / "Microsoft VS Code/Code.exe",
            Path(os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData/Local"))) / "Programs/Microsoft VS Code/Code.exe",
        ],
    }

    def execute(self, request: ActionRequest) -> ActionResult:
        handlers = {
            "system_info": self.system_info,
            "open_path": self.open_path,
            "launch_app": self.launch_app,
            "show_desktop": self.show_desktop,
            "lock_computer": self.lock_computer,
            "shutdown": self.shutdown,
            "restart": self.restart,
            "list_apps": self.list_apps,
            "search_files": self.search_files,
            "search_files_modified": self.search_files_modified,
            "list_processes": self.list_processes,
            "close_process": self.close_process,
            "context_snapshot": self.context_snapshot,
            "active_window": self.active_window,
            "open_windows": self.open_windows,
            "recent_commands": self.recent_commands,
            "runtime_health": self.runtime_health,
        }
        handler = handlers.get(request.name)
        if handler is None:
            return ActionResult(False, f"Unknown action: {request.name}")
        return handler(request)

    def runtime_health(self, request: ActionRequest) -> ActionResult:
        if self.runtime_provider is None:
            return ActionResult(False, "Runtime health provider unavailable.")
        return ActionResult(True, "AIOS internal services are online.", self.runtime_provider.health())

    def system_info(self, request: ActionRequest) -> ActionResult:
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage(Path.home().anchor or "/")
        return ActionResult(
            True,
            "System information collected.",
            {
                "platform": platform.platform(),
                "cpu_percent": round(psutil.cpu_percent(interval=0.1), 1),
                "ram_percent": round(memory.percent, 1),
                "ram_used_gb": round(memory.used / (1024**3), 2),
                "ram_total_gb": round(memory.total / (1024**3), 2),
                "disk_percent": round(disk.percent, 1),
                "hostname": platform.node(),
            },
        )

    def open_path(self, request: ActionRequest) -> ActionResult:
        raw_path = str(request.parameters.get("path", "")).strip()
        if raw_path in {".", "~"} or not raw_path:
            path = Path.home()
        else:
            path = Path(raw_path).expanduser()

        if not path.exists():
            return ActionResult(False, f"Path does not exist: {path}")

        try:
            if os.name == "nt":
                os.startfile(path)  # type: ignore[attr-defined]
            elif platform.system() == "Darwin":
                subprocess.Popen(["open", str(path)])
            else:
                subprocess.Popen(["xdg-open", str(path)])
            return ActionResult(True, f"Opened {path}")
        except OSError as exc:
            return ActionResult(False, f"Could not open path: {exc}")

    def _candidate_paths(self, app: str) -> list[Path]:
        paths: list[Path] = []
        for path in self.COMMON_WINDOWS_APPS.get(app, []):
            paths.append(path)

        local_appdata = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData/Local"))
        appdata = Path(os.environ.get("APPDATA", Path.home() / "AppData/Roaming"))
        paths.extend(
            [
                local_appdata / "Microsoft/WindowsApps" / alias
                for alias in self.APP_ALIASES.get(app, [])
            ]
        )
        paths.extend(
            [
                Path(os.environ.get("WINDIR", r"C:\Windows")) / "System32" / alias
                for alias in self.APP_ALIASES.get(app, [])
            ]
        )
        paths.extend(
            [
                appdata / "Microsoft/Windows/Start Menu/Programs" / alias
                for alias in self.APP_ALIASES.get(app, [])
            ]
        )
        return paths

    def _resolve_executable(self, app: str) -> str | None:
        normalized = app.strip().lower().removesuffix(".exe")
        candidates = self.APP_ALIASES.get(normalized, [normalized, normalized + ".exe"])

        # 1) PATH / Windows command resolution.
        for candidate in candidates:
            for query in (candidate, candidate.removesuffix(".exe")):
                executable = shutil.which(query)
                if executable:
                    return executable

        # 2) Known installation locations.
        for path in self._candidate_paths(normalized):
            if path.is_file():
                return str(path)

        # 3) Windows shell/App Execution Alias fallback for commands such as
        # Store apps. The caller handles actual process startup.
        return None

    def launch_app(self, request: ActionRequest) -> ActionResult:
        app = str(request.parameters.get("app", "")).strip().lower()
        if not app:
            return ActionResult(False, "No application was supplied.")

        executable = self._resolve_executable(app)
        if executable:
            try:
                subprocess.Popen([executable], close_fds=True)
                return ActionResult(True, f"Launched {app}.", {"executable": executable})
            except OSError as exc:
                return ActionResult(False, f"Could not launch {app}: {exc}")

        # Windows shell resolution handles Store apps and App Execution Aliases.
        if os.name == "nt":
            try:
                completed = subprocess.run(
                    ["cmd", "/c", "start", "", app],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if completed.returncode == 0:
                    return ActionResult(True, f"Launch request sent for {app}.")
                detail = (completed.stderr or completed.stdout or "Windows could not resolve the application.").strip()
                return ActionResult(False, f"Could not launch {app}: {detail}")
            except (OSError, subprocess.SubprocessError) as exc:
                return ActionResult(False, f"Could not launch {app}: {exc}")

        return ActionResult(False, f"Could not find application: {app}")


    def list_apps(self, request: ActionRequest) -> ActionResult:
        apps = [entry.__dict__ for entry in self.app_launcher.discover()]
        return ActionResult(True, f"Found {len(apps)} launchable apps.", {"apps": apps})

    def search_files(self, request: ActionRequest) -> ActionResult:
        query = str(request.parameters.get("query", "")).strip()
        root = str(request.parameters.get("root", str(Path.home())))
        if not query:
            return ActionResult(False, "Search query is empty.")
        results = self.file_manager.search(root, query, limit=40)
        data = [{"name": item.name, "path": str(item.path), "is_dir": item.is_dir, "size": item.size} for item in results]
        return ActionResult(True, f"Found {len(data)} matching items.", {"results": data})

    def search_files_modified(self, request: ActionRequest) -> ActionResult:
        from datetime import datetime, time

        root = Path(str(request.parameters.get("root", Path.home()))).expanduser()
        start = datetime.combine(datetime.now().date(), time.min).timestamp()
        results = []
        try:
            for item in root.rglob("*"):
                try:
                    if item.is_file() and item.stat().st_mtime >= start:
                        results.append({"name": item.name, "path": str(item.path if hasattr(item, "path") else item), "size": item.stat().st_size})
                        if len(results) >= 100:
                            break
                except (OSError, PermissionError):
                    continue
        except (OSError, PermissionError):
            pass
        return ActionResult(True, f"Found {len(results)} files modified today.", {"results": results})

    def list_processes(self, request: ActionRequest) -> ActionResult:
        import psutil

        rows = []
        for proc in psutil.process_iter(["pid", "name", "username"]):
            try:
                info = proc.info
                name = info.get("name") or "unknown"
                rows.append({"pid": info.get("pid"), "name": name, "username": info.get("username")})
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        rows.sort(key=lambda item: str(item["name"]).lower())
        return ActionResult(True, f"Found {len(rows)} running processes.", {"processes": rows[:200]})

    def context_snapshot(self, request: ActionRequest) -> ActionResult:
        if self.context_provider is None:
            return ActionResult(False, "Context provider unavailable.")
        return ActionResult(True, "Current AIOS context collected.", self.context_provider.snapshot())

    def active_window(self, request: ActionRequest) -> ActionResult:
        if self.context_provider is None:
            return ActionResult(False, "Context provider unavailable.")
        data = self.context_provider.snapshot().get("active_window", {})
        return ActionResult(True, "Active window identified.", data)

    def open_windows(self, request: ActionRequest) -> ActionResult:
        if self.context_provider is None:
            return ActionResult(False, "Context provider unavailable.")
        return ActionResult(True, "Current foreground context identified.", self.context_provider.snapshot().get("active_window", {}))

    def recent_commands(self, request: ActionRequest) -> ActionResult:
        if self.context_provider is None:
            return ActionResult(False, "Context provider unavailable.")
        return ActionResult(True, "Recent AIOS commands retrieved.", {"commands": self.context_provider.snapshot().get("recent_commands", [])})


    def close_process(self, request: ActionRequest) -> ActionResult:
        import psutil

        target = str(request.parameters.get("target", "")).strip().lower()
        if not target:
            return ActionResult(False, "No process target supplied.")
        matches = []
        for proc in psutil.process_iter(["pid", "name"]):
            try:
                name = (proc.info.get("name") or "").lower()
                if target in name:
                    matches.append(proc)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        if not matches:
            return ActionResult(False, f"No running process matched: {target}")
        stopped = 0
        for proc in matches[:5]:
            try:
                proc.terminate()
                stopped += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return ActionResult(True, f"Requested termination for {stopped} process(es) matching '{target}'.", {"matched": len(matches)})

    def show_desktop(self, request: ActionRequest) -> ActionResult:
        if os.name != "nt":
            return ActionResult(False, "Show desktop is currently implemented for Windows only.")
        try:
            # Win+D is the native Windows Show Desktop shortcut.
            user32 = ctypes.windll.user32
            vk_lwin = 0x5B
            vk_d = 0x44
            keyup = 0x0002
            user32.keybd_event(vk_lwin, 0, 0, 0)
            user32.keybd_event(vk_d, 0, 0, 0)
            user32.keybd_event(vk_d, 0, keyup, 0)
            user32.keybd_event(vk_lwin, 0, keyup, 0)
            return ActionResult(True, "Desktop shown.")
        except (AttributeError, OSError) as exc:
            return ActionResult(False, f"Could not show desktop: {exc}")

    def lock_computer(self, request: ActionRequest) -> ActionResult:
        if os.name != "nt":
            return ActionResult(False, "Lock computer is currently implemented for Windows only.")
        try:
            subprocess.run(["rundll32.exe", "user32.dll,LockWorkStation"], check=True)
            return ActionResult(True, "Computer locked.")
        except (OSError, subprocess.CalledProcessError) as exc:
            return ActionResult(False, f"Could not lock computer: {exc}")

    def shutdown(self, request: ActionRequest) -> ActionResult:
        if os.name != "nt":
            return ActionResult(False, "Shutdown is currently implemented for Windows only.")
        try:
            subprocess.Popen(["shutdown", "/s", "/t", "0"])
            return ActionResult(True, "Shutdown command sent to Windows.")
        except OSError as exc:
            return ActionResult(False, f"Could not shut down: {exc}")

    def restart(self, request: ActionRequest) -> ActionResult:
        if os.name != "nt":
            return ActionResult(False, "Restart is currently implemented for Windows only.")
        try:
            subprocess.Popen(["shutdown", "/r", "/t", "0"])
            return ActionResult(True, "Restart command sent to Windows.")
        except OSError as exc:
            return ActionResult(False, f"Could not restart: {exc}")
