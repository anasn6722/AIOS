from __future__ import annotations

import platform
from pathlib import Path
from datetime import datetime

import psutil
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QInputDialog,
    QListWidget,
    QListWidgetItem,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QScrollArea,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from ai.orchestrator import Orchestrator
from apps.launcher import AppLauncher
from files.manager import FileManager
from ai.workspaces import WorkspaceEngine, WorkspaceStore


class AiosShell(QMainWindow):
    """AIOS desktop shell v0.2.

    This is still a normal desktop application, not a replacement Windows shell.
    The AI command layer is kept behind the existing Orchestrator/Policy boundary.
    """

    def __init__(self) -> None:
        super().__init__()
        self.orchestrator = Orchestrator()
        self.file_manager = FileManager()
        self.app_launcher = AppLauncher(self.orchestrator.system)
        self.workspace_store = WorkspaceStore()
        self.workspace_engine = WorkspaceEngine(self.workspace_store, self.app_launcher)
        self.setWindowTitle("AIOS — AI-Native Desktop")
        self.resize(1520, 940)
        self.setMinimumSize(1180, 760)
        self._build_ui()
        self._start_system_timer()

    def _build_ui(self) -> None:
        root = QWidget()
        root.setObjectName("root")
        self.setCentralWidget(root)

        outer = QVBoxLayout(root)
        outer.setContentsMargins(14, 14, 14, 10)
        outer.setSpacing(10)

        top = QHBoxLayout()
        top.setSpacing(10)
        brand = QLabel("AIOS")
        brand.setObjectName("brand")
        version = QLabel("AI-NATIVE OPERATING ENVIRONMENT  •  v0.8")
        version.setObjectName("eyebrow")
        top.addWidget(brand, 0)
        top.addWidget(version, 0)
        top.addStretch(1)
        self.clock = QLabel()
        self.clock.setObjectName("clock")
        top.addWidget(self.clock, 0)
        outer.addLayout(top)

        content = QHBoxLayout()
        content.setSpacing(10)
        content.setContentsMargins(0, 0, 0, 0)

        sidebar = self._make_sidebar()
        content.addWidget(sidebar, 0)

        main_column = QVBoxLayout()
        main_column.setSpacing(10)

        # The central workspace scrolls vertically on smaller screens so that
        # no cards or panels are clipped. The AI command bar and taskbar remain
        # anchored and always accessible.
        workspace_scroll = QScrollArea()
        workspace_scroll.setObjectName("workspaceScroll")
        workspace_scroll.setWidgetResizable(True)
        workspace_scroll.setFrameShape(QFrame.Shape.NoFrame)
        workspace_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        workspace_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        workspace_container = QWidget()
        workspace_layout = QVBoxLayout(workspace_container)
        workspace_layout.setContentsMargins(0, 0, 4, 0)
        workspace_layout.setSpacing(10)
        workspace_layout.addWidget(self._make_hero(), 0)
        workspace_layout.addWidget(self._make_workspace(), 1)
        workspace_scroll.setWidget(workspace_container)
        main_column.addWidget(workspace_scroll, 1)
        main_column.addWidget(self._make_ai_bar(), 0)

        content.addLayout(main_column, 1)
        outer.addLayout(content, 1)
        outer.addWidget(self._make_taskbar(), 0)

        root.setStyleSheet(self._stylesheet())

    def _make_sidebar(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("sidebar")
        panel.setMinimumWidth(160)
        panel.setMaximumWidth(190)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 12, 10, 12)
        layout.setSpacing(6)

        title = QLabel("WORKSPACES")
        title.setObjectName("sectionTitle")
        layout.addWidget(title)

        nav_items = (
            ("⌂  Home", self._focus_ai),
            ("◈  AI Workspace", self._focus_workspace),
            ("▣  Files", self._open_file_manager),
            ("◫  Apps", self._open_apps),
            ("⚙  Settings", self._focus_ai),
        )
        for label, callback in nav_items:
            button = QPushButton(label)
            button.setObjectName("navButton")
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.clicked.connect(callback)
            layout.addWidget(button)

        layout.addStretch(1)
        security = QLabel("●  AI CORE ONLINE\n●  POLICY ENGINE ACTIVE")
        security.setObjectName("security")
        layout.addWidget(security)
        return panel

    def _make_hero(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("hero")
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(28, 24, 24, 24)
        layout.setSpacing(24)

        left = QVBoxLayout()
        left.setSpacing(8)
        greeting = QLabel("SYSTEM ONLINE  /  AI CORE READY")
        greeting.setObjectName("heroEyebrow")
        title = QLabel("Your computer,\nwith an AI-native control layer.")
        title.setObjectName("heroTitle")
        title.setWordWrap(True)
        copy = QLabel(
            "Use the desktop normally or describe a goal in natural language. "
            "AIOS keeps execution behind its policy and action boundary."
        )
        copy.setObjectName("heroCopy")
        copy.setWordWrap(True)
        left.addWidget(greeting)
        left.addWidget(title)
        left.addWidget(copy)

        right = QFrame()
        right.setObjectName("heroStatus")
        status = QVBoxLayout(right)
        status.setContentsMargins(18, 16, 18, 16)
        status.setSpacing(10)
        status_title = QLabel("LIVE CORE")
        status_title.setObjectName("statusHeading")
        status.addWidget(status_title)
        for label, value in (("POLICY", "ACTIVE"), ("CONTEXT", "READ-ONLY"), ("CONTROL", "MANUAL + AI")):
            row = QHBoxLayout()
            name = QLabel(label)
            name.setObjectName("statusLabel")
            val = QLabel(value)
            val.setObjectName("statusValue")
            row.addWidget(name)
            row.addStretch(1)
            row.addWidget(val)
            status.addLayout(row)
        layout.addLayout(left, 1)
        layout.addWidget(right, 0)
        return frame

    def _make_workspace(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("panel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        header = QHBoxLayout()
        label = QLabel("AIOS WORKSPACE")
        label.setObjectName("sectionTitle")
        header.addWidget(label)
        header.addStretch(1)
        self.workspace_status = QLabel("READY")
        self.workspace_status.setObjectName("statusPill")
        header.addWidget(self.workspace_status)
        layout.addLayout(header)

        cards = QGridLayout()
        cards.setContentsMargins(0, 0, 0, 0)
        cards.setHorizontalSpacing(10)
        cards.setVerticalSpacing(10)
        # Workspace profiles
        workspace_panel = QFrame()
        workspace_panel.setObjectName("workspacePanel")
        workspace_layout = QVBoxLayout(workspace_panel)
        workspace_layout.setContentsMargins(12, 12, 12, 12)
        workspace_layout.setSpacing(8)
        workspace_header = QHBoxLayout()
        workspace_title = QLabel("AI WORKSPACES")
        workspace_title.setObjectName("miniHeading")
        workspace_header.addWidget(workspace_title)
        workspace_header.addStretch(1)
        save_btn = QPushButton("Save Current")
        save_btn.setObjectName("miniButton")
        save_btn.clicked.connect(self._save_current_workspace)
        workspace_header.addWidget(save_btn)
        workspace_layout.addLayout(workspace_header)
        self.workspace_buttons = QHBoxLayout()
        self.workspace_buttons.setSpacing(8)
        workspace_layout.addLayout(self.workspace_buttons)
        layout.addWidget(workspace_panel)
        self._refresh_workspace_buttons()

        card_defs = [
            ("▦", "System Monitor", "Live CPU, RAM and platform status", self._system_status),
            ("▤", "File Manager", "Browse folders and search your files", self._open_file_manager),
            ("◇", "AI Command Center", "Control AIOS using natural-language commands", self._focus_ai),
            ("◫", "Application Launcher", "Discover and launch installed apps", self._open_apps),
        ]
        for index, (icon, title, desc, slot) in enumerate(card_defs):
            card = QFrame()
            card.setObjectName("card")
            card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(13, 11, 13, 11)
            card_layout.setSpacing(5)
            icon_label = QLabel(icon)
            icon_label.setObjectName("cardIcon")
            title_label = QLabel(title)
            title_label.setObjectName("cardTitle")
            desc_label = QLabel(desc)
            desc_label.setObjectName("cardDesc")
            desc_label.setWordWrap(True)
            action = QPushButton("Open")
            action.setObjectName("cardButton")
            action.clicked.connect(slot)
            card_layout.addWidget(icon_label)
            card_layout.addWidget(title_label)
            card_layout.addWidget(desc_label, 1)
            card_layout.addWidget(action, 0, Qt.AlignmentFlag.AlignLeft)
            cards.addWidget(card, index // 2, index % 2)
        cards.setColumnStretch(0, 1)
        cards.setColumnStretch(1, 1)
        layout.addLayout(cards)

        self.file_view = QFrame()
        self.file_view.setObjectName("embeddedPanel")
        self.file_view.setMinimumHeight(210)
        file_layout = QVBoxLayout(self.file_view)
        file_layout.setContentsMargins(12, 12, 12, 12)
        file_header = QHBoxLayout()
        self.path_label = QLabel(str(self.file_manager.list_dir(Path.home())[0].path.parent if self.file_manager.list_dir(Path.home()) else Path.home()))
        self.path_label.setObjectName("pathLabel")
        up = QPushButton("Up"); up.setObjectName("miniButton"); up.clicked.connect(self._file_up)
        refresh = QPushButton("Refresh"); refresh.setObjectName("miniButton"); refresh.clicked.connect(self._refresh_files)
        search = QPushButton("Search"); search.setObjectName("miniButton"); search.clicked.connect(self._search_files)
        file_header.addWidget(self.path_label, 1); file_header.addWidget(up); file_header.addWidget(refresh); file_header.addWidget(search)
        file_layout.addLayout(file_header)
        self.file_list = QListWidget(); self.file_list.setObjectName("fileList"); self.file_list.itemDoubleClicked.connect(self._file_double_click)
        file_layout.addWidget(self.file_list, 1)
        self.current_directory = Path.home()
        self._refresh_files()
        layout.addWidget(self.file_view, 1)
        return panel

    def _make_ai_bar(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("aiBar")
        layout = QHBoxLayout(panel)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(10)

        label = QLabel("◉")
        label.setObjectName("aiGlyph")
        layout.addWidget(label)

        self.command = QLineEdit()
        self.command.setPlaceholderText('Ask AIOS…  e.g. "system status" or "open C:\\Users"')
        self.command.returnPressed.connect(self.run_command)
        layout.addWidget(self.command, 1)

        button = QPushButton("Run")
        button.setObjectName("runButton")
        button.clicked.connect(self.run_command)
        layout.addWidget(button)

        self.confirm_button = QPushButton("Confirm")
        self.confirm_button.setObjectName("confirmButton")
        self.confirm_button.clicked.connect(self.confirm_command)
        self.confirm_button.setVisible(False)
        layout.addWidget(self.confirm_button)

        self.output = QLabel("AIOS ready. Context awareness is read-only; AI actions remain gated by the policy engine.")
        self.output.setObjectName("output")
        self.output.setWordWrap(True)
        self.output.setMinimumWidth(0)
        self.output.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        layout.addWidget(self.output, 1)
        return panel

    def _make_taskbar(self) -> QFrame:
        bar = QFrame()
        bar.setObjectName("taskbar")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(8)

        home = QPushButton("◉  AIOS")
        home.setObjectName("taskButton")
        home.clicked.connect(self._focus_ai)
        layout.addWidget(home)

        for name, callback in (("Explorer", self._open_home), ("Apps", self._open_apps), ("Monitor", self._system_status)):
            button = QPushButton(name)
            button.setObjectName("taskButton")
            button.clicked.connect(callback)
            layout.addWidget(button)

        layout.addStretch(1)
        self.task_status = QLabel("Protected • Local actions")
        self.task_status.setObjectName("taskStatus")
        layout.addWidget(self.task_status)
        return bar

    def _start_system_timer(self) -> None:
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._refresh_status)
        self.timer.start(1000)
        self._refresh_status()

    def _refresh_status(self) -> None:
        now = datetime.now().strftime("%H:%M:%S")
        cpu = psutil.cpu_percent(interval=None)
        ram = psutil.virtual_memory().percent
        self.clock.setText(f"{now}   •   CPU {cpu:.0f}%   •   RAM {ram:.0f}%")

    def run_command(self) -> None:
        text = self.command.text().strip()
        if not text:
            return

        normalized = " ".join(text.lower().split())

        # v0.7.2: context queries are read-only and are handled directly by
        # the ContextEngine. This avoids coupling UI context features to the
        # general AI intent parser and guarantees these commands stay usable.
        if normalized in {
            "what app am i using",
            "what window am i using",
            "what window is active",
            "show current window",
        }:
            self.orchestrator.context.record_command(text)
            data = self.orchestrator.context.snapshot().get("active_window", {})
            title = data.get("title") or "No foreground window detected"
            process = data.get("process") or "Unknown process"
            pid = data.get("pid")
            pid_text = f"PID {pid}" if pid else "PID unknown"
            self.file_list.clear()
            self.path_label.setText("Active Application")
            self.file_list.addItem(QListWidgetItem(f"Window: {title}"))
            self.file_list.addItem(QListWidgetItem(f"Application: {process}"))
            self.file_list.addItem(QListWidgetItem(pid_text))
            self.output.setText(f"✓ You are using: {process}\nWindow: {title}\n{pid_text}")
            self.workspace_status.setText("ACTIVE APP")
            self.command.clear()
            return

        if normalized in {
            "show my context",
            "show current context",
            "what is my current context",
            "what's my current context",
        }:
            self.orchestrator.context.record_command(text)
            data = self.orchestrator.context.snapshot()
            active = data.get("active_window") or {}
            lines = [
                f"User: {data.get('user', 'Unknown')}",
                f"Home: {data.get('home', '')}",
                f"Directory: {data.get('current_directory', '')}",
                f"Platform: {data.get('platform', '')}",
                f"CPU: {data.get('cpu_percent', '?')}%",
                f"RAM: {data.get('ram_percent', '?')}%",
                f"Disk: {data.get('disk_percent', '?')}%",
                f"Active app: {active.get('process') or 'Unknown'}",
                f"Active window: {active.get('title') or 'Unknown'}",
            ]
            self.file_list.clear()
            self.path_label.setText("Current Context")
            for line in lines:
                self.file_list.addItem(QListWidgetItem(line))
            self.output.setText("✓ Current computer context collected (read-only).")
            self.workspace_status.setText("CONTEXT")
            self.command.clear()
            return

        if normalized in {
            "show recent commands",
            "recent commands",
            "what did i just do",
            "show command history",
        }:
            # Snapshot AFTER recording this request, so history reflects what
            # the user just asked AIOS to do.
            self.orchestrator.context.record_command(text)
            commands = self.orchestrator.context.snapshot().get("recent_commands", [])
            self.file_list.clear()
            self.path_label.setText("Recent AIOS Commands")
            if commands:
                for index, command in enumerate(commands[-20:], 1):
                    self.file_list.addItem(QListWidgetItem(f"{index}.  {command}"))
            else:
                self.file_list.addItem(QListWidgetItem("No recent commands yet."))
            self.output.setText(f"✓ {len(commands)} recent AIOS command(s) stored locally.")
            self.workspace_status.setText("COMMAND HISTORY")
            self.command.clear()
            return

        # v0.9 workspace intents.
        if normalized in {"show workspaces", "list workspaces", "open workspaces", "show ai workspaces"}:
            self._show_workspaces()
            self.command.clear()
            return

        for prefix in ("switch to ", "open workspace ", "load workspace "):
            if normalized.startswith(prefix):
                name = text[len(prefix):].strip()
                if name:
                    self._switch_workspace(name)
                    self.command.clear()
                    return

        if normalized.startswith("create workspace "):
            name = text[len("create workspace "):].strip()
            if name:
                self._create_workspace_from_name(name)
                self.command.clear()
                return

        # v0.6 object-model intents: show structured OS information in the shell.
        if normalized in {"what apps are running", "which apps are running", "show running apps", "show running applications", "what is running"}:
            result = self.orchestrator.handle(text)
            processes = result.data.get("processes", [])
            self.file_list.clear()
            self.path_label.setText("Running Processes")
            for proc in processes[:120]:
                item = QListWidgetItem(f"⚙  {proc.get('name')}   —   PID {proc.get('pid')}")
                item.setData(Qt.ItemDataRole.UserRole, str(proc.get('pid')))
                self.file_list.addItem(item)
            self.output.setText(f"✓ {result.message}")
            self.workspace_status.setText("PROCESS VIEW")
            self.command.clear()
            return

        if normalized in {"show files modified today", "files modified today", "what changed today", "show today's files"}:
            result = self.orchestrator.handle(text)
            self.file_list.clear()
            self.path_label.setText("Modified Today")
            for entry in result.data.get("results", [])[:120]:
                item = QListWidgetItem(f"📄  {entry.get('name')}   —   {entry.get('path')}")
                item.setData(Qt.ItemDataRole.UserRole, entry.get('path'))
                self.file_list.addItem(item)
            self.output.setText(f"✓ {result.message}")
            self.workspace_status.setText("RECENT FILES")
            self.command.clear()
            return

        if normalized in {"open apps", "show apps", "app launcher", "open app launcher"}:
            self._open_apps()
            self.output.setText("✓ Application Launcher opened.")
            self.workspace_status.setText("APP LAUNCHER")
            self.command.clear()
            return

        if normalized in {"open file manager", "open file explorer", "open explorer", "open files"}:
            self._open_file_manager()
            self.command.clear()
            return

        if normalized in {"open downloads", "open my downloads"}:
            downloads = Path.home() / "Downloads"
            downloads.mkdir(parents=True, exist_ok=True)
            self.current_directory = downloads
            self._refresh_files()
            self.output.setText(f"✓ Opened Downloads: {downloads}")
            self.workspace_status.setText("DOWNLOADS")
            self.file_list.setFocus()
            self.command.clear()
            return

        search_query = None
        for prefix in ("find ", "search files for ", "find files for "):
            if normalized.startswith(prefix):
                search_query = text[len(prefix):].strip()
                break
        if search_query:
            self._show_search_results(search_query)
            self.command.clear()
            return

        result = self.orchestrator.handle(text)
        if result.data.get("requires_confirmation"):
            action = result.data.get("action", "this action")
            self.output.setText(f"⚠ Confirmation required: {action}. Run the command again using the confirmation button.")
            self.workspace_status.setText("CONFIRMATION REQUIRED")
            self.confirm_button.setVisible(True)
            self.confirm_button.setProperty("command_text", text)
            return
        if result.ok:
            details = ""
            if result.data:
                details = "\n" + "\n".join(f"{k}: {v}" for k, v in result.data.items())
            self.output.setText(f"✓ {result.message}{details}")
            self.workspace_status.setText("ACTION COMPLETE")
        else:
            self.output.setText(f"⚠ {result.message}")
            self.workspace_status.setText("ACTION BLOCKED")
        self.command.clear()

    def confirm_command(self) -> None:
        text = self.confirm_button.property("command_text")
        if not text:
            return
        result = self.orchestrator.handle(str(text), confirmed=True)
        self.confirm_button.setVisible(False)
        self.command.clear()
        self.output.setText(("✓ " if result.ok else "⚠ ") + result.message)
        self.workspace_status.setText("ACTION COMPLETE" if result.ok else "ACTION BLOCKED")

    def _system_status(self) -> None:
        self.command.setText("system status")
        self.run_command()

    def _open_home(self) -> None:
        self._open_file_manager()

    def _open_file_manager(self) -> None:
        self.current_directory = Path.home()
        self._refresh_files()
        self.workspace_status.setText("FILE MANAGER")
        self.file_list.setFocus()

    def _refresh_files(self) -> None:
        self.file_list.clear()
        self.path_label.setText(str(self.current_directory))
        try:
            entries = self.file_manager.list_dir(self.current_directory)
        except (FileNotFoundError, PermissionError) as exc:
            self.output.setText(f"⚠ {exc}")
            return
        for entry in entries[:250]:
            prefix = "📁" if entry.is_dir else "📄"
            item = QListWidgetItem(f"{prefix}  {entry.name}")
            item.setData(Qt.ItemDataRole.UserRole, str(entry.path))
            self.file_list.addItem(item)

    def _file_double_click(self, item: QListWidgetItem) -> None:
        path = Path(item.data(Qt.ItemDataRole.UserRole))
        if path.is_dir():
            self.current_directory = path
            self._refresh_files()
            return
        self.command.setText(f'open "{path}"')
        self.run_command()

    def _file_up(self) -> None:
        parent = self.current_directory.parent
        if parent != self.current_directory:
            self.current_directory = parent
            self._refresh_files()

    def _search_files(self) -> None:
        query, accepted = QInputDialog.getText(self, "AIOS File Search", "Find files containing:")
        if not accepted or not query.strip():
            return
        self._show_search_results(query.strip())

    def _show_search_results(self, query: str) -> None:
        try:
            results = self.file_manager.search(Path.home(), query, limit=100)
        except FileNotFoundError as exc:
            self.output.setText(f"⚠ {exc}")
            return
        self.file_list.clear()
        self.path_label.setText(f"Search: {query}")
        for entry in results:
            prefix = "📁" if entry.is_dir else "📄"
            item = QListWidgetItem(f"{prefix}  {entry.name}   —   {entry.path}")
            item.setData(Qt.ItemDataRole.UserRole, str(entry.path))
            self.file_list.addItem(item)
        self.output.setText(f"✓ Found {len(results)} matching items for '{query}'.")
        self.workspace_status.setText("SEARCH RESULTS")
        self.file_list.setFocus()

    def _open_apps(self) -> None:
        apps = self.app_launcher.discover()
        self.file_list.clear()
        self.path_label.setText("Applications")
        for app in apps:
            item = QListWidgetItem(f"◫  {app.name}")
            item.setToolTip(app.executable)
            item.setData(Qt.ItemDataRole.UserRole, app.name)
            self.file_list.addItem(item)
        self.file_list.itemDoubleClicked.disconnect(self._file_double_click)
        self.file_list.itemDoubleClicked.connect(self._launch_selected_app)
        self.output.setText(f"✓ {len(apps)} applications discovered. Double-click an app to launch it.")
        self.workspace_status.setText("APP LAUNCHER")

    def _launch_selected_app(self, item: QListWidgetItem) -> None:
        name = str(item.data(Qt.ItemDataRole.UserRole))
        ok, message = self.app_launcher.launch(name)
        self.output.setText(("✓ " if ok else "⚠ ") + message)


    def _focus_workspace(self) -> None:
        self._show_workspaces()

    def _refresh_workspace_buttons(self) -> None:
        while self.workspace_buttons.count():
            item = self.workspace_buttons.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        for workspace in self.workspace_store.list():
            button = QPushButton(workspace.name)
            button.setObjectName("workspaceButton")
            button.setToolTip(workspace.description or workspace.name)
            button.clicked.connect(lambda checked=False, name=workspace.name: self._switch_workspace(name))
            self.workspace_buttons.addWidget(button)
        self.workspace_buttons.addStretch(1)

    def _show_workspaces(self) -> None:
        self.file_list.clear()
        self.path_label.setText("AI Workspaces")
        for workspace in self.workspace_store.list():
            apps = ", ".join(workspace.apps) if workspace.apps else "none"
            folders = ", ".join(workspace.folders) if workspace.folders else "none"
            item = QListWidgetItem(f"◈  {workspace.name}  —  Apps: {apps}  —  Folders: {folders}")
            item.setData(Qt.ItemDataRole.UserRole, workspace.name)
            self.file_list.addItem(item)
        self.output.setText("✓ Workspace profiles ready. Select a workspace button to switch.")
        self.workspace_status.setText("WORKSPACES")

    def _switch_workspace(self, name: str) -> None:
        workspace = self.workspace_engine.resolve(name)
        if not workspace:
            self.output.setText(f"⚠ Workspace not found: {name}")
            self.workspace_status.setText("WORKSPACE NOT FOUND")
            return
        launched: list[str] = []
        failed: list[str] = []
        for app in self.workspace_engine.launchable_apps(workspace):
            ok, message = self.app_launcher.launch(app)
            (launched if ok else failed).append(app)
        first_folder = next((Path(folder) for folder in workspace.folders if Path(folder).exists()), None)
        if first_folder:
            self.current_directory = first_folder
            self._refresh_files()
        detail = f"Launched: {', '.join(launched) or 'none'}."
        if failed:
            detail += f" Not available: {', '.join(failed)}."
        self.output.setText(f"✓ Switched to {workspace.name}. {detail}")
        self.workspace_status.setText(f"{workspace.name.upper()} WORKSPACE")

    def _create_workspace_from_name(self, name: str) -> None:
        name = name.strip()
        if not name:
            return
        apps_text, ok = QInputDialog.getText(self, "Create AIOS Workspace", "Apps (comma-separated):", text="chrome, notepad")
        if not ok:
            return
        folders_text, ok = QInputDialog.getText(self, "Create AIOS Workspace", "Folders (comma-separated):", text=str(Path.home() / "Documents"))
        if not ok:
            return
        self.workspace_store.capture(name, f"Custom AIOS workspace: {name}", apps_text.split(","), folders_text.split(","))
        self._refresh_workspace_buttons()
        self._show_workspaces()
        self.output.setText(f"✓ Workspace '{name}' saved.")
        self.workspace_status.setText("WORKSPACE SAVED")

    def _save_current_workspace(self) -> None:
        name, ok = QInputDialog.getText(self, "Save Workspace", "Workspace name:")
        if not ok or not name.strip():
            return
        apps, _ = QInputDialog.getText(self, "Save Workspace", "Apps (comma-separated):", text="chrome")
        folders, _ = QInputDialog.getText(self, "Save Workspace", "Folders (comma-separated):", text=str(self.current_directory))
        self.workspace_store.capture(name, "Saved from the current AIOS desktop", apps.split(","), folders.split(","))
        self._refresh_workspace_buttons()
        self._show_workspaces()
        self.output.setText(f"✓ Saved workspace '{name}'.")
        self.workspace_status.setText("WORKSPACE SAVED")

    def _focus_ai(self) -> None:
        self.command.setFocus()
        self.command.selectAll()

    @staticmethod
    def _stylesheet() -> str:
        return """
            * {
                font-family: "Segoe UI";
            }
            QWidget#root {
                background: #070b12;
                color: #eaf2ff;
            }
            QLabel { color: #eaf2ff; }
            #brand {
                font-size: 24px;
                font-weight: 900;
                letter-spacing: 4px;
                color: #f4f8ff;
            }
            #eyebrow, #sectionTitle {
                color: #7183a6;
                font-size: 10px;
                font-weight: 800;
                letter-spacing: 1.8px;
            }
            #clock { color: #8296bb; font-size: 12px; font-weight: 600; }
            #sidebar, #panel, #taskbar {
                background: #0b111c;
                border: 1px solid #1a2940;
                border-radius: 18px;
            }
            #sidebar {
                background: #09101a;
            }
            #hero {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #0d1a2d, stop:1 #0c1321);
                border: 1px solid #244161;
                border-radius: 20px;
            }
            #heroEyebrow { color: #63c7ff; font-size: 10px; font-weight: 900; letter-spacing: 2.2px; }
            #heroTitle { font-size: 30px; font-weight: 900; line-height: 1.08; color: #f2f7ff; }
            #heroCopy { color: #8da1c4; font-size: 13px; line-height: 1.5; }
            #heroStatus {
                background: #08111d;
                border: 1px solid #1f3550;
                border-radius: 14px;
                min-width: 220px;
            }
            #statusHeading { color: #5abfff; font-size: 10px; font-weight: 900; letter-spacing: 2px; }
            #statusLabel { color: #6e82a6; font-size: 10px; font-weight: 700; letter-spacing: 1px; }
            #statusValue { color: #73efc2; font-size: 10px; font-weight: 800; }
            #navButton, #taskButton, #cardButton {
                text-align: left;
                background: transparent;
                border: 1px solid transparent;
                color: #a9b8d0;
                border-radius: 10px;
                padding: 8px 10px;
                font-weight: 600;
            }
            #navButton:hover, #taskButton:hover {
                background: #101d30;
                border: 1px solid #203652;
                color: #ffffff;
            }
            #security {
                color: #76e5bd;
                background: #081910;
                border: 1px solid #173c2d;
                border-radius: 10px;
                padding: 10px;
                font-size: 9px;
                line-height: 1.65;
            }
            #card {
                background: #0d1624;
                border: 1px solid #1c304a;
                border-radius: 14px;
                min-height: 138px;
            }
            #card:hover {
                border: 1px solid #2e5b7e;
                background: #0e1929;
            }
            #cardIcon { font-size: 26px; color: #69cbff; }
            #cardTitle { font-size: 15px; font-weight: 800; color: #edf5ff; }
            #cardDesc { color: #7f92b4; font-size: 11px; line-height: 1.45; }
            #cardButton {
                border: 1px solid #294562;
                background: #0a1320;
                padding: 7px 12px;
                font-size: 11px;
            }
            #cardButton:hover { background: #13273d; border-color: #39719a; }
            #statusPill {
                color: #78edc3;
                background: #0b2119;
                border: 1px solid #174a35;
                border-radius: 9px;
                padding: 6px 10px;
                font-size: 9px;
                font-weight: 800;
            }
            #embeddedPanel {
                background: #09121e;
                border: 1px solid #1a2b42;
                border-radius: 12px;
            }
            #pathLabel { color: #89a0c4; font-size: 10px; font-weight: 600; }
            #miniButton {
                background: #0b1725;
                border: 1px solid #213752;
                border-radius: 8px;
                padding: 6px 10px;
                color: #aebfda;
                font-size: 10px;
            }
            #miniButton:hover { background: #12243a; color: #fff; }
            #fileList {
                background: #08111c;
                border: 1px solid #17283d;
                border-radius: 9px;
                padding: 5px;
                color: #c8d7ed;
                font-size: 11px;
                outline: none;
            }
            #fileList::item { padding: 8px 8px; border-radius: 6px; }
            #fileList::item:hover { background: #102236; }
            #fileList::item:selected { background: #16324e; color: #ffffff; }
            #aiBar {
                background: #0a1320;
                border: 1px solid #2a4e70;
                border-radius: 15px;
            }
            #aiGlyph { color: #60caff; font-size: 20px; font-weight: 900; }
            QLineEdit {
                background: #07101a;
                border: 1px solid #1e3650;
                border-radius: 10px;
                padding: 9px 12px;
                color: #eef6ff;
                selection-background-color: #164d73;
            }
            QLineEdit:focus { border: 1px solid #49bcff; background: #081522; }
            #confirmButton {
                background: #4d3b0d;
                border: 1px solid #977a24;
                border-radius: 9px;
                padding: 10px 14px;
                color: #fff8df;
                font-weight: 800;
            }
            #runButton {
                background: #1294d1;
                border: 1px solid #42bdf2;
                border-radius: 9px;
                padding: 10px 18px;
                color: white;
                font-weight: 800;
            }
            #runButton:hover { background: #1ca9e8; }
            #output { color: #8fa5c8; font-size: 10px; }
            #taskStatus { color: #6e83a9; font-size: 10px; font-weight: 600; }
            #workspaceScroll { background: transparent; border: none; }
            #workspacePanel {
                background: #0a1422;
                border: 1px solid #20364f;
                border-radius: 12px;
            }
            #miniHeading { color: #7aa2c9; font-size: 10px; font-weight: 900; letter-spacing: 1.8px; }
            #workspaceButton {
                background: #0e1d2e;
                border: 1px solid #23445f;
                border-radius: 9px;
                padding: 8px 14px;
                color: #c7dbf1;
                font-size: 10px;
                font-weight: 800;
            }
            #workspaceButton:hover { background: #15304a; border-color: #3b7092; color: white; }
            QScrollBar:vertical { background: #08101a; width: 8px; margin: 2px; }
            QScrollBar::handle:vertical { background: #23405e; border-radius: 4px; min-height: 30px; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
        """

