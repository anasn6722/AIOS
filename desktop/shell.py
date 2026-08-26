from __future__ import annotations

import platform
from datetime import datetime

import psutil
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
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


class AiosShell(QMainWindow):
    """AIOS desktop shell v0.2.

    This is still a normal desktop application, not a replacement Windows shell.
    The AI command layer is kept behind the existing Orchestrator/Policy boundary.
    """

    def __init__(self) -> None:
        super().__init__()
        self.orchestrator = Orchestrator()
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
        version = QLabel("AI-NATIVE DESKTOP  •  v0.3")
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
        label = QLabel("CURRENT WORKSPACE")
        label.setObjectName("sectionTitle")
        header.addWidget(label)
        header.addStretch(1)
        self.workspace_status = QLabel("READY")
        self.workspace_status.setObjectName("statusPill")
        header.addWidget(self.workspace_status)
        layout.addLayout(header)

        grid = QGridLayout()
        grid.setSpacing(10)
        cards = [
            ("▦", "System Monitor", "Live CPU, RAM and platform status", self._system_status),
            ("▤", "File Space", "Open and organize local files", self._open_home),
            ("◇", "Command Center", "Talk to the AI system layer", self._focus_ai),
            ("◌", "App Launcher", "Quick-launch everyday apps", self._open_apps),
        ]
        for index, (icon, title, desc, slot) in enumerate(cards):
            card = QFrame()
            card.setObjectName("card")
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(16, 14, 16, 14)
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
            grid.addWidget(card, index // 2, index % 2)
        layout.addLayout(grid)
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
        self.command.setText("open .")
        self.run_command()

    def _open_apps(self) -> None:
        self.output.setText("Try: open chrome, open notepad, open calculator, open terminal, or open task manager.")
        self.workspace_status.setText("APP LAUNCHER")

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
