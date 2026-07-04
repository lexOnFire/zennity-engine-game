from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtCore import Qt
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


def _hierarchy_item_for(editor: ZennityPhase1Editor, obj: object):
    root = editor.hierarchy.tree.topLevelItem(0)
    assert root is not None
    for index in range(root.childCount()):
        item = root.child(index)
        if item.data(0, Qt.UserRole) is obj:
            return item
    raise AssertionError(f"Object {obj!r} was not found in the hierarchy")


def test_phase1_editor_owns_editor_context(phase1_editor: ZennityPhase1Editor) -> None:
    assert isinstance(phase1_editor.editor_context, EditorContext)
    assert phase1_editor.editor_context.commands is not None
    assert phase1_editor.scene_view_model.selection_manager is phase1_editor.editor_context.selection


def test_phase1_toolbar_tools_update_tool_manager(phase1_editor: ZennityPhase1Editor) -> None:
    phase1_editor._tool_actions[EditorTool.MOVE].trigger()

    assert phase1_editor.editor_context.tools.active_tool == EditorTool.MOVE
    assert phase1_editor._tool_actions[EditorTool.MOVE].isChecked()

    phase1_editor.editor_context.tools.set_active_tool(EditorTool.ROTATE)

    assert phase1_editor._tool_actions[EditorTool.ROTATE].isChecked()
    assert not phase1_editor._tool_actions[EditorTool.MOVE].isChecked()


def test_phase1_selection_uses_editor_context(phase1_editor: ZennityPhase1Editor) -> None:
    objects = phase1_editor.scene_objects()
    selected = objects[0]

    phase1_editor.select_object(selected)

    assert phase1_editor.editor_context.selection.selected is selected
    assert phase1_editor.scene_view_model.selected_object is selected
    assert phase1_editor.viewport.selected_object() is selected


def test_phase1_hierarchy_selection_updates_selection_manager(
    phase1_editor: ZennityPhase1Editor,
    qapp: QApplication,
) -> None:
    selected = phase1_editor.scene_objects()[0]
    item = _hierarchy_item_for(phase1_editor, selected)

    phase1_editor.hierarchy.tree.setCurrentItem(item)
    qapp.processEvents()

    assert phase1_editor.editor_context.selection.selected is selected
    assert phase1_editor.scene_view_model.selected_object is selected
    assert phase1_editor.viewport.selected_object() is selected


def test_phase1_viewport_selection_updates_selection_manager(
    phase1_editor: ZennityPhase1Editor,
) -> None:
    selected = phase1_editor.scene_objects()[1]
    phase1_editor.viewport.active_scene.selected_index = 1

    phase1_editor.viewport._sync_selection_to_model()

    assert phase1_editor.editor_context.selection.selected is selected
    assert phase1_editor.scene_view_model.selected_object is selected
    assert phase1_editor.viewport.selected_object() is selected


def test_phase1_selection_manager_syncs_viewport_hierarchy_and_inspector(
    phase1_editor: ZennityPhase1Editor,
    qapp: QApplication,
) -> None:
    selected = phase1_editor.scene_objects()[1]

    phase1_editor.editor_context.selection.set_selected(selected)
    qapp.processEvents()

    assert phase1_editor.viewport.selected_object() is selected
    assert phase1_editor.viewport.active_scene.selected_index == 1
    assert phase1_editor.scene_view_model.selected_object is selected
    assert phase1_editor.inspector.name.text() == selected.name
    assert phase1_editor.hierarchy.tree.currentItem().data(0, Qt.UserRole) is selected
