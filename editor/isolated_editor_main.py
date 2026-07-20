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
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QHBoxLayout, QFormLayout,
    QCheckBox, QLabel, QComboBox, QLineEdit,
    QMessageBox, QPushButton, QDoubleSpinBox,
)
from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem, QWidget

from editor.interface_smoke_test import InterfaceSmokeTest
from editor.controllers.logic_assets import LogicAssetRepository
from editor.isolated_viewport import run_viewport
from editor.runtime.viewport_process_controller import ViewportProcessController
from editor.runtime.isolated_play_mode_controller import IsolatedPlayModeController
from editor.runtime.scene_selection_controller import SceneSelectionController
from editor.runtime.viewport_event_dispatcher import ViewportEventDispatcher
from editor.runtime.scene_history import SceneHistory
from editor.editor_session_controller import EditorSessionController
from editor.inspector_controller import InspectorComponentController, IsolatedInspectorController
from editor.inspector_view_renderer import InspectorViewRenderer
from editor.animation_workspace_controller import AnimationWorkspaceController
from editor.animation_workspace_operations import AnimationWorkspaceOperations
from editor.asset_preview_service import AssetPreviewService
from editor.scene_persistence import EditorScenePersistence
from editor.hierarchy_view_renderer import HierarchyViewRenderer
from editor.script_workspace_controller import ScriptWorkspaceController
from editor.logic_workspace_controller import LogicWorkspaceController
from editor.prefab_workspace_controller import PrefabWorkspaceController
from editor.scene_object_controller import SceneObjectController
from editor.editor_command_controller import EditorCommandController
from editor.project_workflow_controller import ProjectWorkflowController
from editor.viewport_event_controller import ViewportEventController
from editor.hierarchy_controller import HierarchyController
from editor.scene_history_controller import SceneHistoryController
from editor.widgets.component_picker import ComponentPickerDialog
from editor.widgets.animation_picker import AnimationPickerDialog
from editor.widgets.animator_controller_editor import AnimatorControllerEditorDialog
from editor.ui.icons import component_title, editor_icon
from editor.ui.tokens import DEFAULT_TOKENS
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
        self._console_records: list[tuple[str, str]] = []
        self._last_build_report = None
        self._last_validation_report = None
        self._logic_assets_repository = LogicAssetRepository(Path.cwd())
        super().__init__()
        self._asset_preview_service = AssetPreviewService(DEFAULT_TOKENS.danger)
        self._scene_persistence = EditorScenePersistence(Path.cwd())
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
        self._viewport_controller = viewport_controller or ViewportProcessController.from_queues(
            commands,
            events,
            viewport_process,
        )
        self._viewport_process = self._viewport_controller.process
        self._commands = self._viewport_controller.commands
        self._events = self._viewport_controller.events
        self._scene_controller = SceneSelectionController(self._commands)
        self._viewport_events = ViewportEventDispatcher({
            "selected": self._handle_selected_event,
            "transform_begin": self._handle_transform_event,
            "transform_end": self._handle_transform_event,
            "transform": self._handle_transform_event,
            "play_state": self._handle_play_state_event,
            "scene_snapshot": self._handle_scene_snapshot_event,
            "runtime_objects": self._handle_runtime_objects_event,
            "viewport_mode": self._handle_viewport_mode_event,
            "script_log": self._handle_script_log_event,
            "logic_trace": self._handle_logic_trace_event,
            "logic_trace_clear": self._handle_logic_trace_event,
            "animator_state": self._handle_animator_state_event,
            "animation_event": self._handle_animation_event,
            "attach_script": self._handle_attach_script_event,
            "stats": self._handle_stats_event,
        })
        self._session_controller = EditorSessionController(self)
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
        self._hierarchy_view = HierarchyViewRenderer(self)
        self._hierarchy_controller = HierarchyController(self, self._hierarchy_view)
        self._updating_inspector = False
        self._scene_history = SceneHistory(max_commands=100, max_bytes=16 * 1024 * 1024)
        self._history_controller = SceneHistoryController(self)
        self._inspector_controller = IsolatedInspectorController(self)
        self._inspector_components = InspectorComponentController(self)
        self._inspector_view = InspectorViewRenderer(self)
        self._animation_workspace = AnimationWorkspaceController(self)
        self._script_workspace = ScriptWorkspaceController(self)
        self._logic_workspace_controller = LogicWorkspaceController(self)
        self._prefab_workspace = PrefabWorkspaceController(self)
        self._scene_objects = SceneObjectController(self)
        self._editor_commands = EditorCommandController(self)
        self._project_workflow = ProjectWorkflowController(self)
        self._viewport_event_controller = ViewportEventController(self)
        self._drag_history_snapshot: list[dict] | None = None
        self._snap_enabled = False
        self._runtime_playing = False
        self._play_controller = IsolatedPlayModeController()
        self._play_session = self._play_controller.session
        self._runtime_keys = {
            key: False for key in ("left", "right", "up", "down", "jump", "restart")
        }
        self.setWindowTitle("Zennity Engine Editor — Phase 1")
        self.statusBar().showMessage(
            "Zennity Phase 1 pronto — Viewport em processo dedicado."
        )
        self._connect_existing_toolbar_actions()
        self._configure_main_menus()
        self._configure_tool_actions()
        self._configure_create_menu()
        self._connect_create_panel()
        self._configure_edit_menu()
        self._refresh_assets()
        self._refresh_prefabs()
        self.prefab_tree.itemDoubleClicked.connect(self._instantiate_prefab_item)
        self.prefab_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.prefab_tree.customContextMenuRequested.connect(self._open_prefab_menu)
        for check in self.console_level_checks.values():
            check.toggled.connect(self._refresh_console)
        self.console_clear_button.clicked.connect(self._clear_console)
        self.assets_tree.itemClicked.connect(self._preview_asset)
        self.assets_tree.itemDoubleClicked.connect(self._open_logic_asset_item)
        self._connect_hierarchy_to_viewport()
        self._refresh_hierarchy()
        self._connect_inspector_to_viewport()
        self._configure_animation_workspace()
        self._configure_logic_workspace()
        self.script_containers = []
        self._clear_inspector_view()
        self.add_component_button.clicked.connect(self._open_add_component_menu)
        self.viewport_tabs.currentChanged.connect(self._change_view_mode)

        self._session_controller.configure()
        self._scene_controller.publish_snapshot(self._scene_snapshot)
        self._log("INFO", "Zennity Phase 1 iniciado com Viewport em processo separado")

    def _log(self, level: str, message: str) -> None:
        normalized = str(level).upper()
        self._console_records.append((normalized, str(message)))
        self._console_records = self._console_records[-2000:]
        if self.console_level_checks.get(normalized) is None or self.console_level_checks[normalized].isChecked():
            self.console_output.appendPlainText(f"[{normalized}] {message}")

    def _refresh_console(self) -> None:
        visible = {level for level, check in self.console_level_checks.items() if check.isChecked()}
        self.console_output.setPlainText("\n".join(f"[{level}] {message}" for level, message in self._console_records if level in visible))

    def _clear_console(self) -> None:
        self._console_records.clear()
        self.console_output.clear()

    def _connect_create_panel(self) -> None:
        for kind, button in self.create_buttons.items():
            button.clicked.connect(lambda checked=False, object_kind=kind: self._create_object(object_kind))

    def _preview_asset(self, item: QTreeWidgetItem) -> None:
        path_value = item.toolTip(0)
        if not path_value:
            return
        preview = self._asset_preview_service.preview(Path(path_value))
        self._set_asset_preview_state("content")
        self.preview_label.clear()
        if preview.pixmap is not None:
            self.preview_label.setPixmap(preview.pixmap.scaled(
                self.preview_label.width(), self.preview_label.height(),
                Qt.KeepAspectRatio, Qt.SmoothTransformation,
            ))
        else:
            self.preview_label.setText(preview.label)
        self.preview_details_label.setText(preview.details)

    def _set_asset_preview_state(self, state: str) -> None:
        """Atualiza somente o estado visual, preservando o conteúdo da prévia."""
        self.preview_label.setProperty("uiState", state)
        self.preview_label.style().unpolish(self.preview_label)
        self.preview_label.style().polish(self.preview_label)

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

    def _dragged_asset_path(self) -> Path | None:
        selected_items = self.assets_tree.selectedItems()
        if not selected_items:
            return None
        path_value = selected_items[0].toolTip(0)
        return Path(path_value) if path_value else None

    def _attach_script(self, object_name: str, path: Path) -> None:
        self._script_workspace.attach(object_name, path)

    def _get_available_scripts(self) -> list[Path]:
        return self._script_workspace.available_scripts()

    def _change_attached_script(self, old_path: str, new_path: str) -> None:
        self._script_workspace.change(old_path, new_path)

    def _remove_single_script(self, script_path: str) -> None:
        self._script_workspace.remove(script_path)

    def _update_script_config_val(self, script_path: str, key: str, value: float | bool | str) -> None:
        self._script_workspace.update_property(script_path, key, value)

    def _remove_all_scripts(self) -> None:
        self._script_workspace.remove_all()

    def _create_script_asset(self) -> None:
        self._script_workspace.create_asset()

    def _edit_selected_script(self) -> None:
        self._script_workspace.edit_selected()

    def _edit_script_path(self, path: Path) -> None:
        self._script_workspace.edit_path(path)

    def _change_view_mode(self, index: int) -> None:
        mode = "scene" if index == 0 else "game"
        self._commands.put({"type": "set_view_mode", "mode": mode})
        self._log("INFO", f"Aba alterada para: {mode.upper()}")

    def _configure_logic_workspace(self) -> None:
        self._logic_workspace_controller.connect()

    def _send_logic_debug_command(self, command: str) -> None:
        self._logic_workspace_controller.send_debug_command(command)


    def _show_logic_window(self, _checked: bool = False, *, preferred_path: Path | None = None) -> None:
        self._logic_workspace_controller.show(preferred_path=preferred_path)

    def _logic_assets(self) -> list[tuple[Path, dict]]:
        return self._logic_workspace_controller.assets()

    def _logic_graphs_for_object(self, object_name: str) -> list[tuple[Path, dict]]:
        return self._logic_workspace_controller.graphs_for_object(object_name)

    def _save_logic_binding(self, path: Path, graph: dict) -> None:
        self._logic_workspace_controller.save_binding(path, graph)

    def _choose_logic_graph_component(self) -> None:
        self._logic_workspace_controller.choose_component()

    def _create_logic_graph_for_selected(self) -> None:
        self._logic_workspace_controller.create_for_selected()

    def _selected_logic_path(self) -> Path | None:
        return self._logic_workspace_controller.selected_path()

    def _open_selected_logic_graph(self) -> None:
        self._logic_workspace_controller.open_selected()

    def _detach_selected_logic_graph(self) -> None:
        self._logic_workspace_controller.detach_selected()

    def _remove_all_logic_graphs(self) -> None:
        self._logic_workspace_controller.remove_all()

    def _update_logic_graph_summary(self, _index: int = -1) -> None:
        self._logic_workspace_controller.update_summary()

    def _build_viewport_link_toolbar(self) -> None:
        self._editor_commands.build_viewport_toolbar()

    def _configure_main_menus(self) -> None:
        self._editor_commands.configure_main_menus()

    def _toggle_snap(self, enabled: bool) -> None:
        self._editor_commands.toggle_snap(enabled)

    def _refresh_assets(self) -> None:
        self.assets_tree.clear()
        root_path = Path.cwd() / "Assets"
        if not root_path.exists():
            root_path = Path.cwd() / "assets"
        root_item = QTreeWidgetItem(["📁 " + (root_path.name if root_path.exists() else "Assets")])
        self.assets_tree.addTopLevelItem(root_item)

        def add_directory(parent_item: QTreeWidgetItem, directory: Path) -> None:
            for child in sorted(directory.iterdir(), key=lambda path: (path.is_file(), path.name.lower())):
                if (
                    child.name.startswith(".")
                    or child.suffix == ".meta"
                    or child.suffix.lower() in {".py", ".zbehavior"}
                    or (child.is_dir() and child.name.casefold() in {"scripts", "behaviors"})
                ):
                    continue
                if child.is_dir():
                    icon = "📁 "
                elif child.suffix.lower() in (".png", ".jpg", ".jpeg"):
                    icon = "🖼️ "
                elif child.suffix.lower() in (".ogg", ".wav", ".mp3"):
                    icon = "🔊 "
                elif child.suffix.lower() == ".zanim":
                    icon = "🎞 "
                elif child.suffix.lower() == ".zanimator":
                    icon = "◉ "
                elif child.suffix.lower() == ".zlogic":
                    icon = "◇ "
                else:
                    icon = "📄 "
                item = QTreeWidgetItem([icon + child.name])
                item.setToolTip(0, str(child))
                parent_item.addChild(item)
                if child.is_dir():
                    add_directory(item, child)

        if root_path.exists():
            add_directory(root_item, root_path)
        root_item.setExpanded(True)

    def _open_logic_asset_item(self, item: QTreeWidgetItem, _column: int = 0) -> None:
        path_value = item.toolTip(0)
        path = Path(path_value) if path_value else None
        if path is None or not path.is_file() or path.suffix.lower() != ".zlogic":
            return
        self._show_logic_window(preferred_path=path)

    def _refresh_prefabs(self) -> None:
        self._prefab_workspace.refresh()

    def _save_selected_as_prefab(self) -> None:
        self._prefab_workspace.save_selected()

    def _instantiate_prefab_item(self, item: QTreeWidgetItem) -> None:
        self._prefab_workspace.instantiate_item(item)

    def _open_prefab_menu(self, position) -> None:
        self._prefab_workspace.open_menu(position)

    def _create_prefab_variant(self, base_path: Path) -> None:
        self._prefab_workspace.create_variant(base_path)

    def _export_project(self) -> None:
        self._project_workflow.export_project()

    def _validate_current_project(self) -> None:
        self._project_workflow.validate_current_project()

    def _show_last_build_report(self) -> None:
        self._project_workflow.show_last_build_report()

    def _connect_existing_toolbar_actions(self) -> None:
        self._editor_commands.connect_toolbar_actions()

    def _configure_tool_actions(self) -> None:
        self._editor_commands.configure_tools()

    def _send_toolbar_command(self, message: dict) -> None:
        self._editor_commands.dispatch(message)

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
