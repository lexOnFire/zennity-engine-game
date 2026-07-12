"""Entrypoint oficial do Zennity Phase 1."""
from __future__ import annotations

import sys


def main() -> None:
    if "--legacy-embedded" in sys.argv:
        from PySide6.QtWidgets import QApplication
        from editor.phase1_editor import ZennityPhase1Editor
        from editor.premium_theme import PREMIUM_QSS

        app = QApplication(sys.argv)
        app.setStyleSheet(PREMIUM_QSS)
        window = ZennityPhase1Editor()
        window.show()
        raise SystemExit(app.exec())

    from editor.isolated_editor_main import main as isolated_main
    isolated_main()


if __name__ == "__main__":
    main()
