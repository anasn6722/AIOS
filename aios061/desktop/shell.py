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
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from ai.orchestrator import Orchestrator
from apps.launcher import AppLauncher
from files.manager import FileManager


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
        self.setWindowTitle("AIOS — AI Native Desktop")
        self.resize(1440, 900)
        self.setMinimumSize(1100, 700)
        self._build_ui()
        self._start_system_timer()

    def _build_ui(self) -> None:
        root = QWidget()
        root.setObjectName("root")
        self.setCentralWidget(root)

        outer = QVBoxLayout(root)
        outer.setContentsMargins(18, 18, 18, 12)
        outer.setSpacing(12)

        top = QHBoxLayout()
        brand = QLabel("AIOS")
        brand.setObjectName("brand")
        version = QLabel("AI-NATIVE DESKTOP  •  v0.6")
        version.setObjectName("eyebrow")
        top.addWidget(brand)
        top.addSpacing(12)
        top.addWidget(version)
        top.addStretch(1)
        self.clock = QLabel()
        self.clock.setObjectName("clock")
        top.addWidget(self.clock)
        outer.addLayout(top)

        content = QHBoxLayout()
        content.setSpacing(14)

        sidebar = self._make_sidebar()
        content.addWidget(sidebar)

        main = QVBoxLayout()
        main.setSpacing(14)
        main.addWidget(self._make_hero())
        main.addWidget(self._make_workspace(), 1)
        main.addWidget(self._make_ai_bar())
        content.addLayout(main, 1)
        outer.addLayout(content, 1)

        outer.addWidget(self._make_taskbar())
        root.setStyleSheet(self._stylesheet())

    def _make_sidebar(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("sidebar")
        panel.setFixedWidth(190)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(12, 16, 12, 16)
        layout.setSpacing(8)

        title = QLabel("WORKSPACES")
        title.setObjectName("sectionTitle")
        layout.addWidget(title)

        for label in ("⌂  Home", "◈  AI Workspace", "▣  Files", "◫  Apps", "⚙  Settings"):
            button = QPushButton(label)
            button.setObjectName("navButton")
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            layout.addWidget(button)

        layout.addStretch(1)
        security = QLabel("●  AI CORE ONLINE\n●  POLICY ENGINE ACTIVE")
        security.setObjectName("security")
        layout.addWidget(security)
        return panel

    def _make_hero(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("hero")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(24, 22, 24, 22)
        layout.setSpacing(8)

        greeting = QLabel("SYSTEM ONLINE")
        greeting.setObjectName("heroEyebrow")
        title = QLabel("Your computer,\nwith an AI control layer.")
        title.setObjectName("heroTitle")
        title.setWordWrap(True)
        copy = QLabel(
            "Use the mouse and keyboard normally, or tell AIOS what you want. "
            "Both paths use the same protected system-action layer."
        )
        copy.setObjectName("heroCopy")
        copy.setWordWrap(True)
        layout.addWidget(greeting)
        layout.addWidget(title)
        layout.addWidget(copy)
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

        cards = QHBoxLayout()
        cards.setSpacing(10)
        for icon, title, desc, slot in [
            ("▦", "System Monitor", "Live CPU, RAM and platform status", self._system_status),
            ("▤", "File Manager", "Browse folders and search your files", self._open_file_manager),
            ("◇", "AI Command Center", "Control AIOS using natural-language commands", self._focus_ai),
            ("◫", "Application Launcher", "Discover and launch installed apps", self._open_apps),
        ]:
            card = QFrame()
            card.setObjectName("card")
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(16, 14, 16, 14)
            icon_label = QLabel(icon); icon_label.setObjectName("cardIcon")
            title_label = QLabel(title); title_label.setObjectName("cardTitle")
            desc_label = QLabel(desc); desc_label.setObjectName("cardDesc"); desc_label.setWordWrap(True)
            action = QPushButton("Open"); action.setObjectName("cardButton"); action.clicked.connect(slot)
            card_layout.addWidget(icon_label); card_layout.addWidget(title_label); card_layout.addWidget(desc_label, 1); card_layout.addWidget(action, 0, Qt.AlignmentFlag.AlignLeft)
            cards.addWidget(card, 1)
        layout.addLayout(cards)

        self.file_view = QFrame()
        self.file_view.setObjectName("embeddedPanel")
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

        self.output = QLabel("AIOS ready. AI actions are gated by the policy engine.")
        self.output.setObjectName("output")
        self.output.setWordWrap(True)
        self.output.setMinimumWidth(260)
        layout.addWidget(self.output, 1)
        return panel

    def _make_taskbar(self) -> QFrame:
        bar = QFrame()
        bar.setObjectName("taskbar")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(10, 8, 10, 8)
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

        # UI-native v0.4 intents: route these into AIOS panels rather than
        # treating them as external Windows paths/commands.
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


    def _focus_ai(self) -> None:
        self.command.setFocus()
        self.command.selectAll()

    @staticmethod
    def _stylesheet() -> str:
        return """
            QWidget#root {
                background: #070b14;
                color: #e8eefc;
            }
            QLabel { color: #e8eefc; }
            #brand {
                font-size: 26px;
                font-weight: 800;
                letter-spacing: 3px;
            }
            #eyebrow, #sectionTitle {
                color: #7181a4;
                font-size: 11px;
                font-weight: 700;
                letter-spacing: 1.5px;
            }
            #clock { color: #7f90b5; font-size: 12px; }
            #sidebar, #panel, #taskbar {
                background: #0d1423;
                border: 1px solid #1c2a44;
                border-radius: 16px;
            }
            #hero {
                background: #101b30;
                border: 1px solid #243a61;
                border-radius: 18px;
            }
            #heroEyebrow { color: #55b8ff; font-size: 11px; font-weight: 800; letter-spacing: 2px; }
            #heroTitle { font-size: 34px; font-weight: 800; }
            #heroCopy { color: #92a4c8; font-size: 14px; max-width: 820px; }
            #navButton, #taskButton, #cardButton {
                text-align: left;
                background: transparent;
                border: 0;
                color: #afbdd8;
                border-radius: 9px;
                padding: 10px 12px;
            }
            #navButton:hover, #taskButton:hover, #cardButton:hover { background: #15223a; color: #ffffff; }
            #security { color: #6ee7b7; font-size: 10px; line-height: 1.6; }
            #card {
                background: #0f192b;
                border: 1px solid #1f3150;
                border-radius: 14px;
                min-height: 180px;
            }
            #cardIcon { font-size: 25px; color: #67c7ff; }
            #cardTitle { font-size: 16px; font-weight: 700; }
            #cardDesc { color: #8294b7; font-size: 12px; }
            #cardButton { border: 1px solid #2a4165; padding: 7px 12px; }
            #statusPill { color: #6ee7b7; background: #10281f; border-radius: 10px; padding: 6px 10px; font-size: 10px; font-weight: 700; }
            #aiBar {
                background: #0d1727;
                border: 1px solid #2a456e;
                border-radius: 14px;
            }
            #aiGlyph { color: #60c8ff; font-size: 22px; }
            QLineEdit {
                background: #08101d;
                border: 1px solid #223854;
                border-radius: 9px;
                padding: 10px 12px;
                color: #edf4ff;
                selection-background-color: #1d4d73;
            }
            QLineEdit:focus { border: 1px solid #48b8ff; }
            #confirmButton {
                background: #6f5a19;
                border: 1px solid #a18424;
                border-radius: 9px;
                padding: 10px 14px;
                color: #ffffff;
                font-weight: 700;
            }
            #runButton {
                background: #1594d4;
                border: 0;
                border-radius: 9px;
                padding: 10px 18px;
                color: #ffffff;
                font-weight: 700;
            }
            #runButton:hover { background: #1eaae9; }
            #output { color: #95a8ca; font-size: 11px; }
            #taskStatus { color: #6d81a8; font-size: 11px; }
        """
