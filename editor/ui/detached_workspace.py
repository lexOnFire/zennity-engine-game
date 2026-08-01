"""Detached editor workspace window without composition-root dependencies."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMainWindow, QWidget


class DetachedWorkspaceWindow(QMainWindow):
    """Independent tool window that hides instead of being destroyed."""

    def __init__(self, title: str, workspace: QWidget, parent: QWidget | None = None) -> None:
        super().__init__(parent, Qt.Window)
        self.setWindowTitle(title)
        self.resize(1180, 760)
        self.setMinimumSize(820, 560)
        self.setCentralWidget(workspace)
        workspace.show()

    def closeEvent(self, event) -> None:
        event.ignore()
        self.hide()
