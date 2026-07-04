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


def test_phase1_toolbar_active_tool_is_visually_checked(
    phase1_editor: ZennityPhase1Editor,
) -> None:
    phase1_editor.editor_context.tools.set_active_tool(EditorTool.SCALE)

    assert phase1_editor._tool_actions[EditorTool.SCALE].isChecked()
    assert not phase1_editor._tool_actions[EditorTool.SELECT].isChecked()
    assert not phase1_editor._tool_actions[EditorTool.MOVE].isChecked()
    assert not phase1_editor._tool_actions[EditorTool.ROTATE].isChecked()


def test_phase1_snap_toolbar_toggle_updates_editor_state(
    phase1_editor: ZennityPhase1Editor,
) -> None:
    assert phase1_editor._snap_action is not None
    assert phase1_editor._snap_action.text() == "Snap: OFF"
    assert not phase1_editor._snap_action.isChecked()
    assert not phase1_editor.editor_context.state.snap_enabled

    phase1_editor._snap_action.trigger()

    assert phase1_editor.editor_context.state.snap_enabled
    assert phase1_editor._snap_action.isChecked()
    assert phase1_editor._snap_action.text() == "Snap: ON"
    assert phase1_editor.status_msg.text() == "Snap ativado"

    phase1_editor._snap_action.trigger()

    assert not phase1_editor.editor_context.state.snap_enabled
    assert not phase1_editor._snap_action.isChecked()
    assert phase1_editor._snap_action.text() == "Snap: OFF"
    assert phase1_editor.status_msg.text() == "Snap desativado"


def test_phase1_rotate_and_scale_report_unimplemented_tools(
    phase1_editor: ZennityPhase1Editor,
) -> None:
    phase1_editor.editor_context.tools.set_active_tool(EditorTool.ROTATE)

    assert phase1_editor.status_msg.text() == "Rotate em desenvolvimento"

    phase1_editor.editor_context.tools.set_active_tool(EditorTool.SCALE)

    assert phase1_editor.status_msg.text() == "Scale em desenvolvimento"


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


def test_phase1_viewport_move_tool_moves_selected_object_and_updates_inspector(
    phase1_editor: ZennityPhase1Editor,
) -> None:
    selected = phase1_editor.scene_objects()[1]
    phase1_editor.select_object(selected)
    phase1_editor.editor_context.tools.set_active_tool(EditorTool.MOVE)
    start = phase1_editor.viewport.world_to_viewport(selected.transform.position)
    original_x = float(selected.transform.position[0])
    original_y = float(selected.transform.position[1])

    assert phase1_editor.viewport._begin_move_drag(selected, start[0], start[1])
    phase1_editor.viewport._update_move_drag(start[0] + 32.0, start[1] + 16.0)
    phase1_editor.viewport._end_move_drag()

    assert float(selected.transform.position[0]) == pytest.approx(original_x + 32.0)
    assert float(selected.transform.position[1]) == pytest.approx(original_y + 16.0)
    assert phase1_editor.editor_context.selection.selected is selected
    assert phase1_editor.inspector.name.text() == selected.name
    assert f"X {float(selected.transform.position[0]):.1f}" in phase1_editor.inspector.transform_label.text()
    assert f"Y {float(selected.transform.position[1]):.1f}" in phase1_editor.inspector.transform_label.text()


def test_phase1_move_tool_does_not_jump_when_drag_starts_off_center(
    phase1_editor: ZennityPhase1Editor,
) -> None:
    selected = phase1_editor.scene_objects()[1]
    phase1_editor.select_object(selected)
    phase1_editor.editor_context.tools.set_active_tool(EditorTool.MOVE)
    center = phase1_editor.viewport.world_to_viewport(selected.transform.position)
    original = selected.transform.position.copy()
    start_x = center[0] + 8.0
    start_y = center[1] + 6.0

    assert phase1_editor.viewport._begin_move_drag(selected, start_x, start_y)
    phase1_editor.viewport._update_move_drag(start_x, start_y)

    assert float(selected.transform.position[0]) == pytest.approx(float(original[0]))
    assert float(selected.transform.position[1]) == pytest.approx(float(original[1]))


def test_phase1_move_tool_snap_disabled_moves_freely(
    phase1_editor: ZennityPhase1Editor,
) -> None:
    selected = phase1_editor.scene_objects()[1]
    selected.transform.position[0] = 101.0
    selected.transform.position[1] = 99.0
    phase1_editor.select_object(selected)
    phase1_editor.editor_context.state.snap_enabled = False
    phase1_editor.editor_context.state.snap_size = 16
    phase1_editor.editor_context.tools.set_active_tool(EditorTool.MOVE)
    start = phase1_editor.viewport.world_to_viewport(selected.transform.position)

    assert phase1_editor.viewport._begin_move_drag(selected, start[0], start[1])
    phase1_editor.viewport._update_move_drag(start[0] + 5.0, start[1] + 7.0)

    assert float(selected.transform.position[0]) == pytest.approx(106.0)
    assert float(selected.transform.position[1]) == pytest.approx(106.0)


def test_phase1_move_tool_snap_enabled_snaps_drag_position(
    phase1_editor: ZennityPhase1Editor,
) -> None:
    selected = phase1_editor.scene_objects()[1]
    selected.transform.position[0] = 101.0
    selected.transform.position[1] = 99.0
    phase1_editor.select_object(selected)
    phase1_editor.editor_context.state.snap_enabled = True
    phase1_editor.editor_context.state.snap_size = 16
    phase1_editor.editor_context.tools.set_active_tool(EditorTool.MOVE)
    start = phase1_editor.viewport.world_to_viewport(selected.transform.position)

    assert phase1_editor.viewport._begin_move_drag(selected, start[0], start[1])
    phase1_editor.viewport._update_move_drag(start[0] + 5.0, start[1] + 7.0)

    assert float(selected.transform.position[0]) == pytest.approx(112.0)
    assert float(selected.transform.position[1]) == pytest.approx(112.0)


def test_phase1_move_tool_does_not_drag_while_playing(
    phase1_editor: ZennityPhase1Editor,
) -> None:
    selected = phase1_editor.scene_objects()[1]
    phase1_editor.select_object(selected)
    phase1_editor.editor_context.tools.set_active_tool(EditorTool.MOVE)
    start = phase1_editor.viewport.world_to_viewport(selected.transform.position)
    original = selected.transform.position.copy()
    phase1_editor.viewport.active_scene.playing = True

    assert not phase1_editor.viewport._begin_move_drag(selected, start[0], start[1])
    phase1_editor.viewport._update_move_drag(start[0] + 32.0, start[1] + 16.0)
    assert phase1_editor.viewport._move_drag_object is None
    assert float(selected.transform.position[0]) == pytest.approx(float(original[0]))
    assert float(selected.transform.position[1]) == pytest.approx(float(original[1]))


def test_phase1_gizmo_is_hidden_while_playing(
    phase1_editor: ZennityPhase1Editor,
) -> None:
    selected = phase1_editor.scene_objects()[1]
    phase1_editor.select_object(selected)

    assert phase1_editor.viewport._should_draw_gizmo(selected)

    phase1_editor.viewport.active_scene.playing = True

    assert not phase1_editor.viewport._should_draw_gizmo(selected)


def test_phase1_select_tool_does_not_start_move_drag(phase1_editor: ZennityPhase1Editor) -> None:
    selected = phase1_editor.scene_objects()[1]
    phase1_editor.select_object(selected)
    phase1_editor.editor_context.tools.set_active_tool(EditorTool.SELECT)
    start = phase1_editor.viewport.world_to_viewport(selected.transform.position)
    original = selected.transform.position.copy()

    assert not phase1_editor.viewport._begin_move_drag(selected, start[0], start[1])
    phase1_editor.viewport.select_object(phase1_editor.viewport._object_at_viewport_point(start[0], start[1]))
    phase1_editor.viewport._update_move_drag(start[0] + 32.0, start[1] + 16.0)

    assert phase1_editor.editor_context.selection.selected is selected
    assert phase1_editor.viewport._move_drag_object is None
    assert float(selected.transform.position[0]) == pytest.approx(float(original[0]))
    assert float(selected.transform.position[1]) == pytest.approx(float(original[1]))


def test_phase1_world_to_viewport_uses_scene_camera_transform(
    phase1_editor: ZennityPhase1Editor,
) -> None:
    selected = phase1_editor.scene_objects()[1]
    phase1_editor.viewport.active_scene.cam_obj.transform.position[0] = 320.0
    phase1_editor.viewport.active_scene.cam_obj.transform.position[1] = 240.0
    phase1_editor.viewport.active_scene.camera.zoom = 2.0

    sx, sy = phase1_editor.viewport.world_to_viewport(selected.transform.position)

    assert not (
        sx == pytest.approx(float(selected.transform.position[0]))
        and sy == pytest.approx(float(selected.transform.position[1]))
    )
    assert phase1_editor.viewport.viewport_to_world((sx, sy))[0] == pytest.approx(float(selected.transform.position[0]))
    assert phase1_editor.viewport.viewport_to_world((sx, sy))[1] == pytest.approx(float(selected.transform.position[1]))
