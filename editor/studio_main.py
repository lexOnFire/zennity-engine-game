from __future__ import annotations
"""
----------------------------------------------------

LEGACY MODULE

Este módulo foi substituído pela arquitetura baseada em:

- ZennityPhase1Editor
- EditorContext
- SceneViewModel
- SelectionManager
- RuntimeManager

Ele não faz parte do runtime atual.

Não adicionar novas funcionalidades aqui.

Antes de remover definitivamente, garantir que nenhum import externo exista.

----------------------------------------------------
"""


import os
import sys

from PySide6.QtCore import QFile, QTextStream
from PySide6.QtWidgets import QApplication

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from editor.windows.studio_window import StudioWindow


def load_stylesheet(app: QApplication) -> None:
    theme_path = os.path.join(os.path.dirname(__file__), "themes", "dark_theme.qss")
    file = QFile(theme_path)
    if file.open(QFile.ReadOnly | QFile.Text):
        stream = QTextStream(file)
        app.setStyleSheet(stream.readAll())
        file.close()


def main() -> None:
    app = QApplication(sys.argv)
    load_stylesheet(app)
    window = StudioWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
