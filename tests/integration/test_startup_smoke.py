from __future__ import annotations

from pathlib import Path
import pytest
from PySide6.QtWidgets import QApplication

from editor.phase1_editor import ZennityPhase1Editor
from editor.entrypoints import CANONICAL_ENTRYPOINT


@pytest.fixture(scope="session")
def qapp() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_editor_startup_smoke_test(qapp: QApplication) -> None:
    """Verifica se o editor oficial inicializa corretamente sem falhas estruturais."""
    assert CANONICAL_ENTRYPOINT == "editor.phase1_main"

    editor = ZennityPhase1Editor()
    assert editor is not None
    assert editor.editor_context is not None

    # Verifica se os painéis fundamentais foram inicializados
    assert hasattr(editor, "hierarchy")
    assert hasattr(editor, "inspector")
    assert hasattr(editor, "console")

    # Verifica se há uma cena padrão configurada no startup
    assert editor.scene_model is not None
    assert len(editor.scene_model.get_root_objects()) >= 0

    editor.close()
    editor.deleteLater()
    qapp.processEvents()
