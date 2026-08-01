"""Inicializa Interface Qt e Viewport Pygame em processos independentes.

Execute a partir da raiz do projeto:
    python -m editor.isolated_editor_main
"""
from __future__ import annotations

import multiprocessing as mp
import sys
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QHBoxLayout, QFormLayout,
    QCheckBox, QLabel, QComboBox, QLineEdit,
    QMessageBox, QPushButton, QDoubleSpinBox,
)
from PySide6.QtWidgets import QTreeWidgetItem, QWidget

from editor.interface_smoke_test import InterfaceSmokeTest
from editor.controllers.logic_assets import LogicAssetRepository
from editor.isolated_viewport import run_viewport
from editor.runtime.viewport_process_controller import ViewportProcessController
from editor.editor_bootstrap_controller import EditorBootstrapController
from editor.animation_workspace_operations import AnimationWorkspaceOperations
from editor.widgets.component_picker import ComponentPickerDialog
from editor.widgets.animation_picker import AnimationPickerDialog
from editor.widgets.animator_controller_editor import AnimatorControllerEditorDialog
from editor.ui.icons import component_title, editor_icon
from engine.animation.clip_asset import (
    animation_asset_from_clip,
    animation_asset_to_clip,
    default_animation_asset,
    save_animation_asset,
)


class IsolatedEditorWindow(AnimationWorkspaceOperations, InterfaceSmokeTest):
    def __init__(
        self,
        viewport_process: mp.Process | None,
        commands,
        events,
        viewport_controller: ViewportProcessController | None = None,
    ) -> None:
        self._last_build_report = None
        self._last_validation_report = None
        self._logic_assets_repository = LogicAssetRepository(Path.cwd())
        super().__init__()
        self._current_animation_asset_path: Path | None = None
        self._animation_draft_name = "NewAnimation"
        self._animation_events: list[dict] = []
        self._animation_asset_dirty = False
        self._animation_preview_playing = True
        self._animation_bound_key: tuple[str, str] | None = None
        # A workspace usa este índice durante sua configuração inicial.
        self._animator_preview_index = 0
        self._animator_controller_dialog: AnimatorControllerEditorDialog | None = None
        self._runtime_animator_states: dict[str, dict] = {}
        self._component_expanded = {
            "transform": True,
            "sprite": True,
            "audio": False,
            "logic": False,
            "rigidbody": False,
            "collider": False,
            "camera": False,
            "ui": True,
            "runtime": True,
        }
        self._initial_scene_snapshot = [
            {"id": "floor", "name": "Chao", "x": 0.0, "y": 150.0, "w": 600.0, "h": 32.0, "rotation": 0.0, "color": (91, 194, 100), "rigidbody": {"is_kinematic": True, "use_gravity": False}, "collider": {"type": "box"}},
            {"id": "player", "name": "Player", "x": 0.0, "y": 0.0, "w": 36.0, "h": 48.0, "rotation": 0.0, "color": (88, 117, 255), "rigidbody": {"is_kinematic": False, "use_gravity": True, "gravity_scale": 1.0}, "collider": {"type": "box"}},
        ]
        self._scene_snapshot = deepcopy(self._initial_scene_snapshot)
        self._scene_document: dict | None = None
        self._current_scene_path: Path | None = None
        self._objects_by_name = {item["name"]: item for item in self._scene_snapshot}
        self._runtime_objects_by_name: dict[str, dict] = {}
        self._selected_name: str | None = None
        self._updating_inspector = False
        self._drag_history_snapshot: list[dict] | None = None
        self._snap_enabled = False
        self._runtime_playing = False
        self._runtime_keys = {
            key: False for key in ("left", "right", "up", "down", "jump", "restart")
        }
        self._bootstrap = EditorBootstrapController(self, Path.cwd())
        self._bootstrap.compose(viewport_process, commands, events, viewport_controller)
        self._bootstrap.configure()

    def _log(self, level: str, message: str) -> None:
        self._console_controller.log(level, message)

    def _refresh_console(self) -> None:
        self._console_controller.refresh()

    def _clear_console(self) -> None:
        self._console_controller.clear()

    def _connect_create_panel(self) -> None:
        for kind, button in self.create_buttons.items():
            button.clicked.connect(lambda checked=False, object_kind=kind: self._create_object(object_kind))

    def _preview_asset(self, item: QTreeWidgetItem) -> None:
        self._asset_browser.preview(item)

    def _set_asset_preview_state(self, state: str) -> None:
        """Atualiza somente o estado visual, preservando o conteúdo da prévia."""
        self._asset_browser.set_preview_state(state)

    def attach_viewport_process(self, process: mp.Process) -> None:
        self._session_controller.attach_viewport_process(process)

    def native_viewport_size(self) -> tuple[int, int]:
        """Return physical pixels expected by the native Pygame child window."""
        return self._session_controller.native_viewport_size()

    def eventFilter(self, watched, event) -> bool:
        handled = self._session_controller.handle_event(watched, event)
        if handled is not None:
            return handled
        return super().eventFilter(watched, event)

    def _flush_viewport_resize(self) -> None:
        """Agrupa a rajada de Resize do Qt e envia sempre o último tamanho."""
        self._session_controller.flush_viewport_resize()

    def _change_view_mode(self, index: int) -> None:
        mode = "game" if int(index) == 1 else "scene"
        self._commands.put({
            "type": "set_view_mode",
            "mode": mode,
        })

        label = "Game View" if mode == "game" else "Scene View"
        self.statusBar().showMessage(f"{label} ativa")

    def _set_play_mode_editing_locked(self, locked: bool) -> None:
        self._editor_commands.set_editing_locked(locked)

    def _configure_create_menu(self) -> None:
        self._editor_commands.configure_create_menu()

    def _configure_edit_menu(self) -> None:
        self._editor_commands.configure_edit_menu()

    def _record_history(self, snapshot: list[dict] | None = None) -> None:
        self._history_controller.record(snapshot)

    def _restore_history(self, snapshot: list[dict]) -> None:
        self._history_controller.restore(snapshot)

    def _undo(self) -> None:
        self._history_controller.undo()

    def _redo(self) -> None:
        self._history_controller.redo()

    def _new_scene(self) -> None:
        self._scene_objects.new_scene()

    def _unique_name(self, base: str) -> str:
        return self._scene_objects.unique_name(base)

    def _create_object(self, kind: str) -> None:
        self._scene_objects.create(kind)

    def _create_object_at(self, kind: str, screen_x: float, screen_y: float) -> None:
        self._scene_objects.create_at(kind, screen_x, screen_y)

    def _create_sprite_at(self, texture_path: Path, screen_x: float, screen_y: float) -> None:
        self._scene_objects.create_sprite_at(texture_path, screen_x, screen_y)

    def _save_scene_snapshot(self) -> None:
        self._project_workflow.save_scene()

    def _collect_logic_variables(self, scope: str) -> dict[str, dict[str, Any]]:
        return self._project_workflow.collect_logic_variables(scope)

    def _load_scene_snapshot(self, _checked: bool = False, scene_path: Path | None = None) -> None:
        self._project_workflow.load_scene(scene_path)

    def _connect_hierarchy_to_viewport(self) -> None:
        self._hierarchy_controller.connect()

    def _open_hierarchy_menu(self, position) -> None:
        self._hierarchy_controller.open_context_menu(position)

    def _select_and_duplicate(self, name: str) -> None:
        self._hierarchy_controller.select_and_duplicate(name)

    def _select_and_save_prefab(self, name: str) -> None:
        self._hierarchy_controller.select_and_save_prefab(name)

    def _rename_object(self, old_name: str) -> None:
        self._scene_objects.rename(old_name)

    def _delete_object(self, name: str) -> None:
        self._scene_objects.delete(name)

    def _duplicate_selected(self) -> None:
        self._scene_objects.duplicate_selected()

    def _refresh_hierarchy(self) -> None:
        self._hierarchy_controller.refresh()

    def _hierarchy_item_name(self, item: QTreeWidgetItem | None) -> str:
        return self._hierarchy_controller.item_name(item)

    def _connect_inspector_to_viewport(self) -> None:
        self._inspector_controller.connect()

    def _inspector_card(self, key: str):
        return self._inspector_controller.card(key)

    def _set_inspector_card_present(self, key: str, present: bool) -> None:
        self._inspector_controller.set_card_present(key, present)

    def _toggle_inspector_card(self, key: str) -> None:
        self._inspector_controller.toggle_card(key)

    def _toggle_dynamic_inspector_card(self, key: str, body: QWidget, button) -> None:
        self._inspector_controller.toggle_dynamic_card(key, body, button)

    def _clear_inspector_view(self) -> None:
        self._inspector_controller.clear()

    def _toggle_renderer_component(self, checked: bool) -> None:
        self._inspector_components.toggle_renderer(checked)

    def _choose_sprite_texture(self) -> None:
        self._inspector_components.choose_sprite_texture()

    def _choose_sprite_color(self) -> None:
        self._inspector_components.choose_sprite_color()

    def _send_inspector_renderer(self, record_history: bool = True) -> None:
        self._inspector_components.send_renderer(record_history)

    def _toggle_audio_component(self, checked: bool) -> None:
        self._inspector_components.toggle_audio(checked)

    def _get_available_audio_files(self) -> list[str]:
        return self._inspector_components.available_audio_files()

    def _send_inspector_audio(self) -> None:
        self._inspector_components.send_audio()

    def _test_selected_audio(self) -> None:
        self._inspector_components.preview_audio()

    def _toggle_rigidbody_component(self, checked: bool) -> None:
        self._inspector_components.toggle_rigidbody(checked)

    def _toggle_collider_component(self, checked: bool) -> None:
        self._inspector_components.toggle_collider(checked)

    def _toggle_camera_component(self, checked: bool) -> None:
        self._inspector_components.toggle_camera(checked)

    def _send_inspector_camera(self) -> None:
        self._inspector_components.send_camera()

    def _choose_camera_color(self) -> None:
        self._inspector_components.choose_camera_color()

    def _toggle_ui_visibility(self, checked: bool) -> None:
        self._inspector_components.toggle_ui_visibility(checked)

    def _delete_ui_component(self) -> None:
        self._inspector_components.delete_ui()

    def _choose_ui_color(self) -> None:
        self._inspector_components.choose_ui_color()

    def _choose_ui_image(self) -> None:
        self._inspector_components.choose_ui_image()

    def _send_inspector_ui(self) -> None:
        self._inspector_components.send_ui()

    def _ensure_canvas(self) -> None:
        self._inspector_components.ensure_canvas()

    def _open_add_component_menu(self) -> None:
        if self._play_session.is_running:
            return
        if self._selected_name not in self._objects_by_name:
            return
        picker = ComponentPickerDialog(self)
        if picker.exec() and picker.selected_component:
            self._add_component(picker.selected_component)

    def _add_component(self, component: str) -> None:
        self._inspector_components.add_component(component)


    def _send_inspector_physics(self) -> None:
        self._inspector_components.send_physics()

    def _send_inspector_transform(self) -> None:
        if self._updating_inspector or self._selected_name not in self._objects_by_name:
            return
        obj = self._objects_by_name[self._selected_name]
        self._record_history()
        for key, field in self.inspector_fields.items():
            obj[key] = float(field.value())
        self._commands.put({"type": "set_transform", "name": self._selected_name, **{k: obj[k] for k in ("x", "y", "w", "h", "rotation")}})

    def _send_inspector_collider(self) -> None:
        self._inspector_components.send_collider()

    def _select_hierarchy_item(self, item: QTreeWidgetItem) -> None:
        self._hierarchy_controller.select_item(item)

    def _update_inspector(self, name: str) -> None:
        obj = self._runtime_objects_by_name.get(name) if self._runtime_playing else None
        obj = obj or self._objects_by_name.get(name)
        if obj is None:
            return
        self._updating_inspector = True
        try:
            self._inspector_view.render_identity_transform(name, obj)
            self._inspector_view.render_renderer(obj)
            self._inspector_view.render_audio(obj)
            self._inspector_view.render_physics(obj)
            self._inspector_view.render_animator(name, obj)
            self._inspector_view.render_camera(name, obj)
            self._inspector_view.render_ui(name, obj)
            self._inspector_view.render_logic(name)
            self._inspector_view.render_runtime(obj)
            for header, body in self.script_containers:
                self.inspector_layout.removeWidget(header)
                self.inspector_layout.removeWidget(body)
                header.deleteLater()
                body.deleteLater()
            self.script_containers.clear()
        finally:
            self._updating_inspector = False
    def _handle_selected_event(self, message: dict) -> None:
        self._viewport_event_controller.selected(message)

    def _handle_transform_event(self, message: dict) -> None:
        self._viewport_event_controller.transform(message)

    def _handle_play_state_event(self, message: dict) -> None:
        self._viewport_event_controller.play_state(message)

    def _handle_scene_snapshot_event(self, message: dict) -> None:
        self._viewport_event_controller.scene_snapshot(message)

    def _handle_runtime_objects_event(self, message: dict) -> None:
        self._viewport_event_controller.runtime_objects(message)

    def _handle_viewport_mode_event(self, message: dict) -> None:
        self._viewport_event_controller.viewport_mode(message)

    def _handle_script_log_event(self, message: dict) -> None:
        self._viewport_event_controller.script_log(message)

    def _handle_logic_trace_event(self, message: dict) -> None:
        self._viewport_event_controller.logic_trace(message)



    def _handle_attach_script_event(self, message: dict) -> None:
        self._viewport_event_controller.attach_script(message)

    def _handle_stats_event(self, message: dict) -> None:
        self._viewport_event_controller.stats(message)

    def _read_viewport_events(self) -> None:
        self._viewport_event_controller.poll()

    def closeEvent(self, event) -> None:
        self._session_controller.shutdown()
        super().closeEvent(event)


def main() -> None:
    context = mp.get_context("spawn")
    viewport_controller = ViewportProcessController.create(context)
    commands = viewport_controller.command_queue
    events = viewport_controller.events
    app = QApplication.instance() or QApplication(sys.argv)
    from editor.ui import apply_editor_theme
    apply_editor_theme(app)
    window = IsolatedEditorWindow(
        None,
        commands,
        events,
        viewport_controller=viewport_controller,
    )
    window.show()
    app.processEvents()

    host_id = int(window.viewport_host.winId())
    host_size = window.native_viewport_size()
    viewport_process = viewport_controller.start(
        target=run_viewport,
        args=(commands, events, host_id, host_size),
        name="ZennityViewport",
    )
    window.attach_viewport_process(viewport_process)
    exit_code = app.exec()

    viewport_controller.shutdown()
    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
