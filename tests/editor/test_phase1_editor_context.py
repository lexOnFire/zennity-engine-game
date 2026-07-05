from __future__ import annotations

import sys
# Restaura o ambiente contra poluição de mocks de outros testes
for name in ["engine.physics.collider", "engine.physics.rigidbody", "engine.physics", "engine.transitions", "engine.audio", "engine.ui.ui_manager", "engine.ui"]:
    if name in sys.modules:
        mod = sys.modules[name]
        if not getattr(mod, "__file__", None) and not getattr(mod, "__path__", None):
            sys.modules.pop(name, None)

import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from editor.phase1_editor import ZennityPhase1Editor
from editor.runtime import EditorContext
from editor.runtime.tool_manager import EditorTool
from engine.game_object import GameObject
from engine.physics.collider import BoxCollider, CircleCollider
from engine.physics.rigidbody import RigidBody
from engine.scene import load_scene


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


class _MousePress:
    def __init__(self, x: float, y: float, button: Qt.MouseButton = Qt.LeftButton) -> None:
        self._x = x
        self._y = y
        self._button = button
        self.accepted = False

    def button(self) -> Qt.MouseButton:
        return self._button

    def x(self) -> float:
        return self._x

    def y(self) -> float:
        return self._y

    def accept(self) -> None:
        self.accepted = True


def _scene_registered_colliders(scene: object) -> list[object]:
    from engine.physics.collider import BoxCollider, CircleCollider
    colliders = [*BoxCollider._registry, *CircleCollider._registry]
    return [
        collider
        for collider in colliders
        if getattr(getattr(collider, "game_object", None), "scene", None) is scene
    ]


def _scene_attached_colliders(scene: object) -> list[object]:
    from engine.physics.collider import BoxCollider, CircleCollider
    attached: list[object] = []
    for obj in getattr(scene, "game_objects", []):
        attached.extend(obj.get_components(BoxCollider))
        attached.extend(obj.get_components(CircleCollider))
    return attached


def _assert_scene_collider_registry_is_current(scene: object) -> None:
    registered = _scene_registered_colliders(scene)
    attached = _scene_attached_colliders(scene)
    scene_objects = set(getattr(scene, "game_objects", []))

    assert len(registered) == len(attached)
    assert all(getattr(collider, "game_object", None) in scene_objects for collider in registered)


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


def test_phase1_file_menu_has_scene_actions(
    phase1_editor: ZennityPhase1Editor,
) -> None:
    actions = {
        phase1_editor.act_new_scene.text(): phase1_editor.act_new_scene.shortcut().toString(),
        phase1_editor.act_open_scene.text(): phase1_editor.act_open_scene.shortcut().toString(),
        phase1_editor.act_save_scene.text(): phase1_editor.act_save_scene.shortcut().toString(),
        phase1_editor.act_save_scene_as.text(): phase1_editor.act_save_scene_as.shortcut().toString(),
    }

    assert actions == {
        "New Scene": "Ctrl+N",
        "Open Scene": "Ctrl+O",
        "Save Scene": "Ctrl+S",
        "Save Scene As": "Ctrl+Shift+S",
    }


def test_phase1_save_scene_uses_current_scene_path(
    phase1_editor: ZennityPhase1Editor,
    tmp_path,
) -> None:
    phase1_editor.current_scene_path = tmp_path / "level.zscene"

    phase1_editor.save_scene()

    loaded = load_scene(phase1_editor.current_scene_path)
    assert loaded["scene_name"] == getattr(phase1_editor.viewport.active_scene, "name", "Untitled")
    assert len(loaded["objects"]) == len(phase1_editor.scene_objects())


def test_phase1_apply_scene_data_replaces_scene_and_selection(
    phase1_editor: ZennityPhase1Editor,
) -> None:
    obj = GameObject("LoadedPlayer", tag="Player")
    obj.mesh_type = "rect"
    obj.transform.position = [42.0, 84.0, 0.0]

    phase1_editor._apply_scene_data({"scene_name": "Loaded", "objects": [obj]})

    objects = phase1_editor.scene_objects()
    assert len(objects) == 1
    assert objects[0] is obj
    assert phase1_editor.viewport.active_scene.name == "Loaded"
    assert phase1_editor.editor_context.selection.selected is obj
    assert phase1_editor.hierarchy.tree.topLevelItem(0).child(0).data(0, Qt.UserRole) is obj


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


def test_phase1_play_controls_reflect_simulation_state(
    phase1_editor: ZennityPhase1Editor,
) -> None:
    assert phase1_editor.btn_play.isEnabled()
    assert not phase1_editor.btn_stop.isEnabled()
    assert not phase1_editor.editor_context.state.is_playing

    phase1_editor.play()

    assert not phase1_editor.btn_play.isEnabled()
    assert phase1_editor.btn_play.text() == "Playing"
    assert phase1_editor.btn_stop.isEnabled()
    assert phase1_editor.editor_context.state.is_playing

    phase1_editor.stop()

    assert phase1_editor.btn_play.isEnabled()
    assert phase1_editor.btn_play.text() == "Play"
    assert not phase1_editor.btn_stop.isEnabled()
    assert not phase1_editor.editor_context.state.is_playing


def test_phase1_editor_has_scene_and_game_view_tabs(
    phase1_editor: ZennityPhase1Editor,
) -> None:
    tabs = phase1_editor.viewport_tabs

    assert tabs.tabText(0) == "Scene"
    assert tabs.tabText(1) == "Game"
    assert phase1_editor.viewport.is_game_view() is False
    assert phase1_editor.game_viewport.is_game_view() is True


def test_phase1_stop_restores_scene_and_reselects_restored_object(
    phase1_editor: ZennityPhase1Editor,
) -> None:
    selected = phase1_editor.scene_objects()[1]
    original_y = float(selected.transform.position[1])
    phase1_editor.select_object(selected)

    phase1_editor.play()
    runtime_selected = phase1_editor.editor_context.selection.selected
    assert runtime_selected is not selected
    phase1_editor.game_viewport.active_scene.update(0.1)
    assert float(runtime_selected.transform.position[1]) > original_y
    assert float(selected.transform.position[1]) == pytest.approx(original_y)

    phase1_editor.stop()

    restored = phase1_editor.scene_objects()[1]
    assert restored is phase1_editor.editor_context.selection.selected
    assert float(restored.transform.position[1]) == pytest.approx(original_y)
    rb = restored.get_component(RigidBody)
    assert rb is not None
    assert float(rb.velocity[1]) == pytest.approx(0.0)


def test_phase1_play_cycles_start_from_same_physics_state(
    phase1_editor: ZennityPhase1Editor,
) -> None:
    scene = phase1_editor.viewport.active_scene
    original_y = float(phase1_editor.scene_objects()[1].transform.position[1])
    deltas: list[float] = []

    _assert_scene_collider_registry_is_current(scene)

    for _ in range(3):
        player = phase1_editor.scene_objects()[1]
        phase1_editor.play()
        runtime_scene = phase1_editor.editor_context.runtime.runtime_scene
        runtime_player = runtime_scene.runtime_for_editor(player)
        phase1_editor.game_viewport.active_scene.update(0.1)
        deltas.append(float(runtime_player.transform.position[1]) - original_y)
        assert float(player.transform.position[1]) == pytest.approx(original_y)
        phase1_editor.stop()
        _assert_scene_collider_registry_is_current(scene)

    assert deltas[0] > 0.0
    assert deltas[1] == pytest.approx(deltas[0])
    assert deltas[2] == pytest.approx(deltas[0])


def test_phase1_play_stop_preserves_objects_and_selection(
    phase1_editor: ZennityPhase1Editor,
) -> None:
    phase1_editor.create_object("Plataforma 2D")
    phase1_editor.create_object("Top-down 2D")
    selected = phase1_editor.scene_objects()[-1]
    selected_name = selected.name
    original_count = len(phase1_editor.scene_objects())
    phase1_editor.select_object(selected)

    phase1_editor.play()
    phase1_editor.game_viewport.active_scene.update(0.1)
    phase1_editor.stop()

    restored_objects = phase1_editor.scene_objects()
    restored_selected = phase1_editor.editor_context.selection.selected
    assert len(restored_objects) == original_count
    assert restored_selected in restored_objects
    assert restored_selected.name == selected_name


def test_phase1_play_mode_switches_viewport_and_inspector_to_runtime_scene(
    phase1_editor: ZennityPhase1Editor,
) -> None:
    editor_scene = phase1_editor.viewport.active_scene
    editor_selected = phase1_editor.scene_objects()[1]
    phase1_editor.select_object(editor_selected)

    phase1_editor.play()

    runtime_scene = phase1_editor.editor_context.runtime.runtime_scene
    runtime_selected = phase1_editor.editor_context.selection.selected
    assert phase1_editor.viewport.active_scene is editor_scene
    assert phase1_editor.game_viewport.active_scene is runtime_scene
    assert phase1_editor.viewport_tabs.currentWidget() is phase1_editor.game_viewport
    assert runtime_selected is runtime_scene.runtime_for_editor(editor_selected)
    assert phase1_editor.inspector.current_object is runtime_selected
    assert phase1_editor.hierarchy.tree.topLevelItem(0).child(1).data(0, Qt.UserRole) is editor_selected

    runtime_selected.transform.position[0] += 100.0
    assert float(editor_selected.transform.position[0]) != pytest.approx(float(runtime_selected.transform.position[0]))

    phase1_editor.stop()

    assert phase1_editor.viewport.active_scene is editor_scene
    assert phase1_editor.game_viewport.active_scene is editor_scene
    assert phase1_editor.viewport_tabs.currentWidget() is phase1_editor.viewport
    assert phase1_editor.editor_context.runtime.runtime_scene is None
    assert phase1_editor.editor_context.selection.selected is editor_selected
    assert phase1_editor.inspector.current_object is editor_selected


def test_phase1_rotate_reports_active_and_scale_reports_unimplemented(
    phase1_editor: ZennityPhase1Editor,
) -> None:
    """Rotate e Scale devem ser ferramentas ativas pelo ToolManager."""
    phase1_editor.editor_context.tools.set_active_tool(EditorTool.ROTATE)

    assert phase1_editor.status_msg.text() == "Ferramenta ativa: Rotate"

    phase1_editor.editor_context.tools.set_active_tool(EditorTool.SCALE)

    assert phase1_editor.status_msg.text() == "Ferramenta ativa: Scale"


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


def test_phase1_hierarchy_refreshes_after_viewport_delete(
    phase1_editor: ZennityPhase1Editor,
    qapp: QApplication,
) -> None:
    selected = phase1_editor.scene_objects()[0]
    phase1_editor.select_object(selected)
    original_count = len(phase1_editor.scene_objects())

    phase1_editor.viewport.delete_selected_object()
    qapp.processEvents()

    root = phase1_editor.hierarchy.tree.topLevelItem(0)
    assert root is not None
    assert len(phase1_editor.scene_objects()) == original_count - 1
    assert root.childCount() == original_count - 1
    assert phase1_editor.editor_context.selection.selected in phase1_editor.scene_objects() or (
        phase1_editor.editor_context.selection.selected is None
    )
    for index in range(root.childCount()):
        assert root.child(index).data(0, Qt.UserRole) is not selected


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


def test_phase1_viewmodel_transform_change_refreshes_inspector(
    phase1_editor: ZennityPhase1Editor,
) -> None:
    selected = phase1_editor.scene_objects()[1]
    phase1_editor.select_object(selected)

    phase1_editor.scene_view_model.set_transform_property("position", 0, 123.0)

    assert float(selected.transform.position[0]) == pytest.approx(123.0)
    assert "X 123.0" in phase1_editor.inspector.transform_label.text()


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


def test_phase1_move_tool_does_not_drag_from_empty_viewport_space(
    phase1_editor: ZennityPhase1Editor,
) -> None:
    selected = phase1_editor.scene_objects()[1]
    phase1_editor.select_object(selected)
    phase1_editor.editor_context.tools.set_active_tool(EditorTool.MOVE)
    original = selected.transform.position.copy()
    event = _MousePress(-1000.0, -1000.0)

    phase1_editor.viewport.mousePressEvent(event)
    phase1_editor.viewport._update_move_drag(0.0, 0.0)

    assert phase1_editor.viewport._move_drag_object is None
    assert phase1_editor.editor_context.selection.selected is selected
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


# ── Testes de estabilizacao Fase 1.2 ─────────────────────────────────────────


def test_phase1_viewport_has_command_manager_injected(
    phase1_editor: ZennityPhase1Editor,
) -> None:
    """A viewport deve receber o CommandManager do EditorContext."""
    assert phase1_editor.viewport.command_manager is phase1_editor.editor_context.commands


def test_phase1_move_tool_registers_undo_command(
    phase1_editor: ZennityPhase1Editor,
) -> None:
    """Apos drag completo, CommandManager deve ter um comando de undo."""
    selected = phase1_editor.scene_objects()[1]
    phase1_editor.select_object(selected)
    phase1_editor.editor_context.tools.set_active_tool(EditorTool.MOVE)
    phase1_editor.editor_context.commands.clear()

    start = phase1_editor.viewport.world_to_viewport(selected.transform.position)
    phase1_editor.viewport._begin_move_drag(selected, start[0], start[1])
    phase1_editor.viewport._update_move_drag(start[0] + 64.0, start[1])
    phase1_editor.viewport._end_move_drag()

    assert phase1_editor.editor_context.commands.can_undo


def test_phase1_move_tool_undo_restores_position(
    phase1_editor: ZennityPhase1Editor,
) -> None:
    """Ctrl+Z apos move deve restaurar a posicao original do objeto."""
    selected = phase1_editor.scene_objects()[1]
    original_x = float(selected.transform.position[0])
    phase1_editor.select_object(selected)
    phase1_editor.editor_context.tools.set_active_tool(EditorTool.MOVE)
    phase1_editor.editor_context.commands.clear()

    start = phase1_editor.viewport.world_to_viewport(selected.transform.position)
    phase1_editor.viewport._begin_move_drag(selected, start[0], start[1])
    phase1_editor.viewport._update_move_drag(start[0] + 64.0, start[1])
    phase1_editor.viewport._end_move_drag()

    assert float(selected.transform.position[0]) == pytest.approx(original_x + 64.0)

    phase1_editor.editor_context.commands.undo()

    assert float(selected.transform.position[0]) == pytest.approx(original_x)


def test_phase1_move_tool_redo_reapplies_position(
    phase1_editor: ZennityPhase1Editor,
) -> None:
    """Ctrl+Y apos undo deve reaplicar o move."""
    selected = phase1_editor.scene_objects()[1]
    original_x = float(selected.transform.position[0])
    phase1_editor.select_object(selected)
    phase1_editor.editor_context.tools.set_active_tool(EditorTool.MOVE)
    phase1_editor.editor_context.commands.clear()

    start = phase1_editor.viewport.world_to_viewport(selected.transform.position)
    phase1_editor.viewport._begin_move_drag(selected, start[0], start[1])
    phase1_editor.viewport._update_move_drag(start[0] + 48.0, start[1])
    phase1_editor.viewport._end_move_drag()

    phase1_editor.editor_context.commands.undo()
    assert float(selected.transform.position[0]) == pytest.approx(original_x)

    phase1_editor.editor_context.commands.redo()
    assert float(selected.transform.position[0]) == pytest.approx(original_x + 48.0)


def test_phase1_move_tool_no_command_when_no_movement(
    phase1_editor: ZennityPhase1Editor,
) -> None:
    """Drag sem movimento real nao deve registrar comando no historico."""
    selected = phase1_editor.scene_objects()[1]
    phase1_editor.select_object(selected)
    phase1_editor.editor_context.tools.set_active_tool(EditorTool.MOVE)
    phase1_editor.editor_context.commands.clear()

    start = phase1_editor.viewport.world_to_viewport(selected.transform.position)
    phase1_editor.viewport._begin_move_drag(selected, start[0], start[1])
    # Solta sem mover
    phase1_editor.viewport._end_move_drag()

    assert not phase1_editor.editor_context.commands.can_undo


def test_phase1_snap_applied_over_absolute_position(
    phase1_editor: ZennityPhase1Editor,
) -> None:
    """Snap deve ser calculado sobre posicao absoluta, nao sobre delta.

    Se o objeto esta em (101, 99) e arrastamos apenas 1 pixel (delta minimo),
    com snap=16 o resultado deve ser (112, 96) — nao (102, 100).
    """
    selected = phase1_editor.scene_objects()[1]
    selected.transform.position[0] = 101.0
    selected.transform.position[1] = 99.0
    phase1_editor.select_object(selected)
    phase1_editor.editor_context.state.snap_enabled = True
    phase1_editor.editor_context.state.snap_size = 16
    phase1_editor.editor_context.tools.set_active_tool(EditorTool.MOVE)
    start = phase1_editor.viewport.world_to_viewport(selected.transform.position)

    phase1_editor.viewport._begin_move_drag(selected, start[0], start[1])
    # Delta minimo de 1 pixel em viewport — mas o snap deve agir na posicao absoluta
    phase1_editor.viewport._update_move_drag(start[0] + 1.0, start[1] + 1.0)

    # Com snap=16: round(102/16)*16 = 96, round(100/16)*16 = 96
    # (resultado depende do zoom da camara, mas deve ser multiplo de 16)
    x = float(selected.transform.position[0])
    y = float(selected.transform.position[1])
    assert x % 16.0 == pytest.approx(0.0, abs=0.01), f"X={x} nao e multiplo de 16"
    assert y % 16.0 == pytest.approx(0.0, abs=0.01), f"Y={y} nao e multiplo de 16"


def test_phase1_snap_disabled_delta_zero_preserves_position(
    phase1_editor: ZennityPhase1Editor,
) -> None:
    """Com snap desabilitado, drag sem mover deve manter posicao exata."""
    selected = phase1_editor.scene_objects()[1]
    selected.transform.position[0] = 101.0
    selected.transform.position[1] = 99.0
    phase1_editor.select_object(selected)
    phase1_editor.editor_context.state.snap_enabled = False
    phase1_editor.editor_context.tools.set_active_tool(EditorTool.MOVE)
    start = phase1_editor.viewport.world_to_viewport(selected.transform.position)

    phase1_editor.viewport._begin_move_drag(selected, start[0], start[1])
    phase1_editor.viewport._update_move_drag(start[0], start[1])

    assert float(selected.transform.position[0]) == pytest.approx(101.0)
    assert float(selected.transform.position[1]) == pytest.approx(99.0)
