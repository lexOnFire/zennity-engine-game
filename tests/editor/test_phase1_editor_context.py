from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtWidgets import QApplication

from editor.phase1_editor import ZennityPhase1Editor
from editor.runtime import EditorContext
from editor.runtime.tool_manager import EditorTool


@pytest.fixture(scope="session")
def qapp() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture
def phase1_editor(qapp: QApplication):
    editor = ZennityPhase1Editor()
    yield editor
    editor.close()
    editor.deleteLater()
    qapp.processEvents()


def test_phase1_editor_owns_editor_context(phase1_editor: ZennityPhase1Editor) -> None:
    assert isinstance(phase1_editor.editor_context, EditorContext)
    assert phase1_editor.editor_context.commands is not None
    assert phase1_editor.scene_view_model.selection_manager is phase1_editor.editor_context.selection


def test_phase1_toolbar_tools_update_tool_manager(phase1_editor: ZennityPhase1Editor) -> None:
    phase1_editor._tool_actions[EditorTool.MOVE].trigger()

    assert phase1_editor.editor_context.tools.active_tool == EditorTool.MOVE
    assert phase1_editor._tool_actions[EditorTool.MOVE].isChecked()


def test_phase1_selection_uses_editor_context(phase1_editor: ZennityPhase1Editor) -> None:
    objects = phase1_editor.scene_objects()
    selected = objects[0]

    phase1_editor.select_object(selected)

    assert phase1_editor.editor_context.selection.selected is selected
    assert phase1_editor.scene_view_model.selected_object is selected
    assert phase1_editor.viewport.selected_object() is selected
