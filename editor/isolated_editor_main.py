"""Inicializa Interface Qt e Viewport Pygame em processos independentes.

Execute a partir da raiz do projeto:
    python -m editor.isolated_editor_main
"""
from __future__ import annotations

import multiprocessing as mp
import sys

from PySide6.QtWidgets import QApplication

from editor.interface_smoke_test import InterfaceSmokeTest
from editor.isolated_viewport import run_viewport


class IsolatedEditorWindow(InterfaceSmokeTest):
    def __init__(self, viewport_process: mp.Process) -> None:
        super().__init__()
        self._viewport_process = viewport_process
        self.setWindowTitle("Zennity — Interface isolada (PySide6)")
        self.statusBar().showMessage(
            "Viewport Pygame está em outra janela/processo. Arraste painéis aqui sem afetá-la."
        )

    def closeEvent(self, event) -> None:
        if self._viewport_process.is_alive():
            self._viewport_process.terminate()
            self._viewport_process.join(timeout=2)
        super().closeEvent(event)


def main() -> None:
    context = mp.get_context("spawn")
    viewport_process = context.Process(target=run_viewport, name="ZennityViewport")
    viewport_process.start()

    app = QApplication.instance() or QApplication(sys.argv)
    window = IsolatedEditorWindow(viewport_process)
    window.show()
    exit_code = app.exec()

    if viewport_process.is_alive():
        viewport_process.terminate()
        viewport_process.join(timeout=2)
    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
