from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_visual_logic_does_not_boot_the_pygame_runtime() -> None:
    source = (ROOT / "editor/visual_scripting/visual_scripting_dock.py").read_text(
        encoding="utf-8"
    )
    assert "EngineBootstrap" not in source
    assert "ensure_editor_metadata_context" in source


def test_editor_metadata_context_does_not_create_a_display(monkeypatch) -> None:
    import pygame
    from PySide6.QtWidgets import QApplication
    from engine.core.context import EngineContext
    from engine.metadata.manager import MetadataManager
    from editor.visual_scripting.editor_metadata_context import (
        ensure_editor_metadata_context,
    )
    from editor.visual_scripting.visual_scripting_dock import (
        VisualScriptingEditorDock,
    )

    pygame.display.quit()
    monkeypatch.setattr(EngineContext, "_current", None)
    context = ensure_editor_metadata_context()

    assert context.config["editor_metadata_only"] is True
    assert context.services.get_optional(MetadataManager) is not None
    assert not pygame.display.get_init()

    app = QApplication.instance() or QApplication([])
    window = VisualScriptingEditorDock()
    app.processEvents()
    assert not pygame.display.get_init()
    window.deleteLater()
    app.processEvents()
