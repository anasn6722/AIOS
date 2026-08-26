from __future__ import annotations

import sys
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication

from desktop.shell import AiosShell


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("AIOS")
    app.setOrganizationName("AIOS")
    app.setFont(QFont("Segoe UI", 10))

    window = AiosShell()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
