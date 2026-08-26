from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ai.orchestrator import Orchestrator


class AiosShell(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.orchestrator = Orchestrator()
        self.setWindowTitle("AIOS — AI Native Desktop")
        self.resize(1100, 700)
        self._build_ui()

    def _build_ui(self) -> None:
        root = QWidget()
        root.setObjectName("root")
        self.setCentralWidget(root)

        layout = QVBoxLayout(root)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(18)

        title = QLabel("AIOS")
        title.setObjectName("title")
        subtitle = QLabel("AI-native operating environment")
        subtitle.setObjectName("subtitle")

        status_card = QFrame()
        status_card.setObjectName("card")
        status_layout = QVBoxLayout(status_card)
        status_layout.addWidget(QLabel("SYSTEM CORE"))
        self.status = QLabel("ONLINE • Manual + AI control ready")
        status_layout.addWidget(self.status)

        command_row = QHBoxLayout()
        self.command = QLineEdit()
        self.command.setPlaceholderText('Try: "system status" or "open C:\\Users"')
        self.command.returnPressed.connect(self.run_command)
        button = QPushButton("Run AI Command")
        button.clicked.connect(self.run_command)
        command_row.addWidget(self.command, 1)
        command_row.addWidget(button)

        self.output = QLabel("AIOS foundation initialized.")
        self.output.setWordWrap(True)
        self.output.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.output.setObjectName("output")

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addWidget(status_card)
        layout.addLayout(command_row)
        layout.addWidget(self.output, 1)

        root.setStyleSheet("""
            #root { background: #0b1020; color: #edf2ff; }
            #title { font-size: 42px; font-weight: 700; }
            #subtitle { color: #8fa3c7; font-size: 16px; }
            #card, #output { background: #121a2c; border: 1px solid #263657; border-radius: 14px; padding: 16px; }
            QLineEdit { background: #11192a; border: 1px solid #2b3b60; border-radius: 10px; padding: 12px; color: #edf2ff; }
            QPushButton { background: #3b82f6; border: 0; border-radius: 10px; padding: 12px 18px; color: white; font-weight: 600; }
            QPushButton:hover { background: #2563eb; }
        """)

    def run_command(self) -> None:
        text = self.command.text().strip()
        if not text:
            return
        result = self.orchestrator.handle(text)
        if result.ok:
            self.output.setText(f"✓ {result.message}\n{result.data}")
        else:
            self.output.setText(f"⚠ {result.message}")
