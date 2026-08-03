"""Bootstrap boundaries for the official Phase 1 editor."""
from __future__ import annotations


def run_legacy_embedded_editor(args: list[str]) -> None:
    """Run the deprecated embedded viewport only when explicitly requested."""
    from PySide6.QtWidgets import QApplication
    from editor.phase1_editor import ZennityPhase1Editor
    from editor.premium_theme import PREMIUM_QSS

    app = QApplication(args)
    app.setStyleSheet(PREMIUM_QSS)
    window = ZennityPhase1Editor()
    window.show()
    raise SystemExit(app.exec())


def run_isolated_editor() -> None:
    """Run the modern isolated viewport editor."""
    from editor.isolated_editor_main import main as isolated_main

    isolated_main()
