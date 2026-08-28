from __future__ import annotations

import platform
from pathlib import Path
from datetime import datetime

import psutil
from PySide6.QtCore import QObject, QThread, QTimer, Qt, Signal, Slot
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QDialogButtonBox,
    QInputDialog,
    QListWidget,
    QListWidgetItem,
    QFrame,
    QGridLayout,
    QGroupBox,
    QPlainTextEdit,
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
from core.runtime import AIOSRuntime
from apps.launcher import AppLauncher
from files.manager import FileManager
from ai.workspaces import WorkspaceEngine, WorkspaceStore


class _VoiceWorker(QObject):
    finished = Signal(object)

    def __init__(self, engine) -> None:
        super().__init__()
        self.engine = engine

    @Slot()
    def run(self) -> None:
        result = self.engine.record_and_transcribe(5)
        self.finished.emit(result)


class AiosShell(QMainWindow):
    """AIOS desktop shell v1.3.

    This is still a normal desktop application, not a replacement Windows shell.
    The AI command layer is kept behind the existing Orchestrator/Policy boundary.
    """

    def __init__(self, runtime: AIOSRuntime | None = None) -> None:
        super().__init__()
        self.orchestrator = Orchestrator(runtime)
        services = self.orchestrator.runtime.services
        self.file_manager = services.file_manager
        self.app_launcher = services.app_launcher
        self.workspace_store = services.workspace_store
        self.workspace_engine = services.workspace_engine
        self.voice_engine = services.voice
        self.vision_engine = services.vision
        self._voice_thread: QThread | None = None
        self._voice_worker: object | None = None
        self._pending_task_plan = None
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
        version = QLabel("AI-NATIVE OPERATING ENVIRONMENT  •  v1.3")
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
        layout.addWidget(self._make_command_center())

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

    def _make_command_center(self) -> QFrame:
        """Central AI command surface for text, context, history, and quick actions."""
        panel = QFrame()
        panel.setObjectName("commandCenter")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)

        header = QHBoxLayout()
        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        title = QLabel("AI COMMAND CENTER")
        title.setObjectName("ccTitle")
        subtitle = QLabel("Describe a goal, ask about your computer, or run a protected OS action.")
        subtitle.setObjectName("ccSubtitle")
        subtitle.setWordWrap(True)
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        header.addLayout(title_box, 1)
        self.cc_state = QLabel("READY")
        self.cc_state.setObjectName("ccState")
        header.addWidget(self.cc_state, 0, Qt.AlignmentFlag.AlignTop)
        layout.addLayout(header)

        chips = QHBoxLayout()
        # Prominent media controls
        media_banner = QHBoxLayout()
        media_banner.setSpacing(8)
        media_title = QLabel("INTERACT")
        media_title.setObjectName("mediaTitle")
        media_banner.addWidget(media_title)
        voice_btn = QPushButton("🎙  VOICE INPUT")
        voice_btn.setObjectName("mediaButton")
        voice_btn.setMinimumHeight(42)
        voice_btn.setMinimumWidth(170)
        voice_btn.setToolTip("Record a short offline voice command")
        voice_btn.clicked.connect(self._start_voice_input)
        media_banner.addWidget(voice_btn)
        vision_btn = QPushButton("◉  CAPTURE SCREEN")
        vision_btn.setObjectName("mediaButton")
        vision_btn.setMinimumHeight(42)
        vision_btn.setMinimumWidth(190)
        vision_btn.setToolTip("Capture the current screen for AIOS vision")
        vision_btn.clicked.connect(self._capture_screen)
        media_banner.addWidget(vision_btn)
        self.media_status = QLabel("VOICE: READY   •   VISION: READY")
        self.media_status.setObjectName("mediaStatus")
        media_banner.addWidget(self.media_status, 0, Qt.AlignmentFlag.AlignVCenter)
        media_banner.addStretch(1)
        layout.addLayout(media_banner)

        chips.setSpacing(6)
        quick = (
            ("Context", "show my context"),
            ("Health", "aios health"),
            ("Processes", "what apps are running"),
            ("History", "show recent commands"),
            ("Workspaces", "show workspaces"),
        )
        for label, command in quick:
            button = QPushButton(label)
            button.setObjectName("quickChip")
            button.clicked.connect(lambda checked=False, text=command: self._run_quick_command(text))
            chips.addWidget(button)
        chips.addStretch(1)
        layout.addLayout(chips)

        lower = QHBoxLayout()
        lower.setSpacing(10)
        self.cc_output = QPlainTextEdit()
        self.cc_output.setObjectName("ccOutput")
        self.cc_output.setReadOnly(True)
        self.cc_output.setMaximumBlockCount(200)
        self.cc_output.setPlaceholderText("AIOS responses and execution details appear here…")
        self.cc_output.setMinimumHeight(88)
        lower.addWidget(self.cc_output, 2)

        status = QFrame()
        status.setObjectName("ccStatusPanel")
        status_layout = QVBoxLayout(status)
        status_layout.setContentsMargins(12, 10, 12, 10)
        status_layout.setSpacing(7)
        self.cc_metrics = {}
        for key, label in (("cpu", "CPU"), ("ram", "RAM"), ("app", "ACTIVE APP"), ("workspace", "WORKSPACE")):
            row = QHBoxLayout()
            name = QLabel(label)
            name.setObjectName("ccMetricLabel")
            value = QLabel("—")
            value.setObjectName("ccMetricValue")
            self.cc_metrics[key] = value
            row.addWidget(name)
            row.addStretch(1)
            row.addWidget(value)
            status_layout.addLayout(row)
        lower.addWidget(status, 1)
        layout.addLayout(lower)
        return panel

    def _capture_screen(self) -> None:
        self.media_status.setText("VOICE: READY   •   VISION: ANALYZING")
        QApplication.processEvents()
        result = None
        message = "Vision analysis failed."
        try:
            result = self.vision_engine.capture_screen()
        except Exception as exc:
            message = f"Vision analysis failed: {exc}"
        if result is not None and result.ok:
            data = result.data
            summary = data.get("summary") or result.message
            details = [summary]
            if data.get("image"):
                details.append(f"Screenshot: {data['image']}")
            ocr = data.get("ocr_text")
            if ocr:
                details.append("\nSCREEN TEXT:\n" + ocr[:1800])
            self.output.setText("✓ " + result.message)
            self.cc_output.setPlainText("\n".join(details))
            self.workspace_status.setText("VISION ANALYZED")
            self.media_status.setText("VOICE: READY   •   VISION: READY")
        else:
            if result is not None:
                message = result.message
            self.output.setText("⚠ " + message)
            self.cc_output.setPlainText(self.output.text())
            self.workspace_status.setText("VISION ERROR")
            self.media_status.setText("VOICE: READY   •   VISION: ERROR")

    def _start_voice_input(self) -> None:
        if self._voice_thread is not None and self._voice_thread.isRunning():
            self.output.setText("⚠ Voice capture is already running.")
            return
        status = self.voice_engine.status()
        if not status.get("microphone_backend") or not status.get("vosk") or not status.get("model_path"):
            problems = []
            if not status.get("microphone_backend"):
                problems.append("sounddevice is not installed or microphone backend is unavailable")
            if not status.get("vosk"):
                problems.append("Vosk is not installed")
            if not status.get("model_path"):
                problems.append("Vosk model is not configured")
            message = "⚠ Voice is not ready: " + "; ".join(problems)
            self.output.setText(message)
            self.cc_output.setPlainText(message)
            self.workspace_status.setText("VOICE SETUP")
            self.media_status.setText("VOICE: SETUP REQUIRED   •   VISION: READY")
            return
        self.output.setText("● Listening for 5 seconds… speak a command now")
        self.cc_output.setPlainText(self.output.text())
        self.workspace_status.setText("VOICE LISTENING")
        self.media_status.setText("VOICE: LISTENING   •   VISION: READY")
        thread = QThread(self)
        worker = _VoiceWorker(self.voice_engine)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.finished.connect(self._finish_voice_input)
        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        self._voice_thread = thread
        self._voice_worker = worker
        thread.start()

    @Slot(object)
    def _finish_voice_input(self, result) -> None:
        if result.ok and result.text:
            self.command.setText(result.text)
            self.output.setText(f"✓ Heard: {result.text}")
            self.workspace_status.setText("VOICE READY")
            self.media_status.setText("VOICE: READY   •   VISION: READY")
            self.run_command()
        else:
            message = f"⚠ {result.message}"
            if result.data:
                status = result.data
                details = []
                if not status.get("microphone_backend"):
                    details.append("microphone backend unavailable")
                if not status.get("vosk"):
                    details.append("vosk package unavailable")
                if not status.get("model_path"):
                    details.append("Vosk model not found")
                if details:
                    message += "\nDetails: " + ", ".join(details)
            self.output.setText(message)
            self.cc_output.setPlainText(message)
            self.workspace_status.setText("VOICE SETUP")
            self.media_status.setText("VOICE: SETUP REQUIRED   •   VISION: READY")
        self._voice_thread = None
        self._voice_worker = None

    def _run_quick_command(self, text: str) -> None:
        self.command.setText(text)
        self.run_command()

    def _update_command_center(self, result_text: str | None = None) -> None:
        if result_text:
            self.cc_output.setPlainText(result_text)
        try:
            context = self.orchestrator.context.snapshot()
            active = context.get("active_window") or {}
            self.cc_metrics["cpu"].setText(f"{context.get('cpu_percent', '?')}%")
            self.cc_metrics["ram"].setText(f"{context.get('ram_percent', '?')}%")
            self.cc_metrics["app"].setText(active.get("process") or "Unknown")
            self.cc_metrics["workspace"].setText(self.workspace_status.text())
        except Exception:
            pass

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
        if hasattr(self, "cc_metrics"):
            self.cc_metrics["cpu"].setText(f"{cpu:.0f}%")
            self.cc_metrics["ram"].setText(f"{ram:.0f}%")

    def run_command(self) -> None:
        text = self.command.text().strip()
        if not text:
            return

        # v1.5: multi-step task planning is shown before execution.
        # Risky plans wait for the same confirmation button used elsewhere.
        plan = self.orchestrator.make_task_plan(text)
        if plan is not None:
            self.orchestrator.context.record_command(text)
            self.cc_output.setPlainText("PLAN READY\n\n" + plan.summary)
            self.output.setText("✓ Plan created. " + ("Confirmation required." if plan.requires_confirmation else "Executing safe steps..."))
            self.workspace_status.setText("PLAN READY")
            if plan.requires_confirmation:
                self._pending_task_plan = plan
                self.confirm_button.setVisible(True)
                self.confirm_button.setProperty("task_plan", plan)
                self.confirm_button.setProperty("command_text", "")
                self.confirm_button.setText("Confirm Plan")
                self.command.clear()
                return
            results = self.orchestrator.execute_task_plan(plan, confirmed=False)
            self._show_task_results(plan, results)
            self.command.clear()
            return

        normalized = " ".join(text.lower().split())

        # v1.3: screen-analysis queries are read-only and handled directly by
        # the vision engine so they do not depend on the general planner.
        if normalized in {
            "what is on my screen",
            "what is on my desktop",
            "analyze my screen",
            "analyze the screen",
            "read my screen",
        }:
            self.orchestrator.context.record_command(text)
            result = self.vision_engine.capture_screen()
            if result.ok:
                data = result.data
                self.output.setText("✓ " + result.message)
                self.cc_output.setPlainText(data.get("summary") or result.message)
                self.workspace_status.setText("VISION ANALYZED")
                self.media_status.setText("VOICE: READY   •   VISION: READY")
            else:
                self.output.setText("⚠ " + result.message)
                self.cc_output.setPlainText(self.output.text())
                self.workspace_status.setText("VISION ERROR")
                self.media_status.setText("VOICE: READY   •   VISION: ERROR")
            self.command.clear()
            return

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
            self._update_command_center(self.output.text())
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

        # v1.4: inspect the current foreground window through Windows UI Automation.
        if normalized in {"inspect screen ui", "show screen controls", "what buttons are on screen", "show ui controls", "inspect current window"}:
            result = self.orchestrator.handle(text)
            if result.ok:
                controls = result.data.get("controls", [])
                self.file_list.clear()
                self.path_label.setText("Visible UI Controls")
                for control in controls[:80]:
                    name = control.get("name") or "(unnamed)"
                    ctype = control.get("control_type") or "Control"
                    item = QListWidgetItem(f"◈  {name}   —   {ctype}")
                    item.setData(Qt.ItemDataRole.UserRole, name)
                    self.file_list.addItem(item)
                self.output.setText(f"✓ {result.message}")
                self.workspace_status.setText("UI INSPECTED")
            else:
                self.output.setText(f"⚠ {result.message}")
                self.workspace_status.setText("UI INSPECTION ERROR")
            self.command.clear()
            self._update_command_center(self.output.text())
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
        self._update_command_center(self.output.text())

    def _show_task_results(self, plan, results) -> None:
        lines = [f"GOAL: {plan.goal}"]
        succeeded = 0
        for index, result in enumerate(results, 1):
            prefix = "✓" if result.ok else "⚠"
            lines.append(f"{prefix} Step {index}: {result.message}")
            if result.ok:
                succeeded += 1
        self.cc_output.setPlainText("\n".join(lines))
        self.output.setText(f"✓ Completed {succeeded}/{len(plan.steps)} step(s).")
        self.workspace_status.setText("PLAN COMPLETE" if succeeded == len(plan.steps) else "PLAN STOPPED")
        self._update_command_center(self.output.text())

    def confirm_command(self) -> None:
        plan = self.confirm_button.property("task_plan")
        if plan is not None:
            results = self.orchestrator.execute_task_plan(plan, confirmed=True)
            self.confirm_button.setVisible(False)
            self.confirm_button.setText("Confirm")
            self.confirm_button.setProperty("task_plan", None)
            self.command.clear()
            self._show_task_results(plan, results)
            return

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
            #commandCenter {
                background: #08121f; border: 1px solid #264a68; border-radius: 16px;
            }
            #ccTitle { color: #f0f7ff; font-size: 15px; font-weight: 900; letter-spacing: 1.2px; }
            #ccSubtitle { color: #7e95b9; font-size: 10px; }
            #ccState { color: #78edc3; background: #0b2119; border: 1px solid #174a35; border-radius: 8px; padding: 5px 9px; font-size: 9px; font-weight: 900; }
            #quickChip { background: #0d1d2d; border: 1px solid #234761; color: #aec4dd; border-radius: 9px; padding: 7px 11px; font-size: 10px; font-weight: 700; }
            #quickChip:hover { background: #15304a; border-color: #39739a; color: #fff; }
            #ccOutput { background: #06101a; border: 1px solid #172d43; border-radius: 10px; color: #bdd0e7; font-size: 10px; padding: 8px; }
            #mediaButton { background: #0c1b2b; border: 1px solid #24506f; color: #b9d4ea; border-radius: 9px; padding: 7px 11px; font-size: 10px; font-weight: 800; }
            #mediaButton:hover { background: #13314a; border-color: #3f86aa; color: #ffffff; }
            #mediaStatus { color: #76e5bd; font-size: 9px; font-weight: 800; letter-spacing: 0.8px; }
            #ccStatusPanel { background: #0a1623; border: 1px solid #1c344d; border-radius: 10px; }
            #ccMetricLabel { color: #6880a4; font-size: 9px; font-weight: 800; letter-spacing: 1px; }
            #ccMetricValue { color: #80e3bd; font-size: 10px; font-weight: 800; }
        """

