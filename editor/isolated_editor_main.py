"""Inicializa Interface Qt e Viewport Pygame em processos independentes.

Execute a partir da raiz do projeto:
    python -m editor.isolated_editor_main
"""
from __future__ import annotations

import faulthandler
import logging
import multiprocessing as mp
import sys
import json
import traceback
from copy import deepcopy
from pathlib import Path
from typing import Any

from PySide6.QtCore import QtMsgType, qInstallMessageHandler
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QHBoxLayout, QFormLayout,
    QCheckBox, QLabel, QComboBox, QLineEdit,
    QMessageBox, QPushButton, QDoubleSpinBox,
)
from PySide6.QtWidgets import QTreeWidgetItem, QWidget

from editor.interface_smoke_test import InterfaceSmokeTest
from editor.inspector_component_delegates_mixin import InspectorComponentDelegatesMixin
from editor.controllers.logic_assets import LogicAssetRepository
from editor.isolated_viewport import run_viewport
from editor.runtime.viewport_process_controller import ViewportProcessController
from editor.runtime.editor_context import EditorContext
from editor.runtime.editor_bridge_orchestrator import EditorBridgeOrchestrator
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


_CRASH_LOG_HANDLE = None


def _install_crash_logging(project_root: Path) -> None:
    """Registra rastros de falhas silenciosas em .zennity_crash.log."""
    global _CRASH_LOG_HANDLE
    if _CRASH_LOG_HANDLE is not None:
        return

    log_path = project_root / ".zennity_crash.log"
    _CRASH_LOG_HANDLE = log_path.open("a", encoding="utf-8", buffering=1)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=[logging.StreamHandler(_CRASH_LOG_HANDLE)],
        force=True,
    )
    faulthandler.enable(file=_CRASH_LOG_HANDLE, all_threads=True)

    def excepthook(exc_type, exc, tb) -> None:
        logging.critical("Exceção não tratada no editor", exc_info=(exc_type, exc, tb))
        traceback.print_exception(exc_type, exc, tb, file=_CRASH_LOG_HANDLE)
        sys.__excepthook__(exc_type, exc, tb)

    def qt_message_handler(mode, context, message) -> None:
        level = logging.ERROR if mode in {QtMsgType.QtCriticalMsg, QtMsgType.QtFatalMsg} else logging.WARNING
        logging.log(level, "Qt: %s", message)

    sys.excepthook = excepthook
    qInstallMessageHandler(qt_message_handler)
    logging.info("Crash logging instalado em %s", log_path)


class IsolatedEditorWindow(InspectorComponentDelegatesMixin, AnimationWorkspaceOperations, InterfaceSmokeTest):
    def __init__(
        self,
        viewport_process: mp.Process | None,
        commands,
        events,
        viewport_controller: ViewportProcessController | None = None,
    ) -> None:
        self._last_build_report = None
        self._last_validation_report = None
        self.editor_context = EditorContext(Path.cwd())
        self._logic_assets_repository = LogicAssetRepository(Path.cwd())
        super().__init__()
        self.bridge_orchestrator = EditorBridgeOrchestrator(self.editor_context)
        self.bridge_orchestrator.setup(animation_dock=self.animation_track_studio)
        self._graph_hub_bridges_attached = False
        self._current_animation_asset_path: Path | None = None
        self._animation_draft_name = "NewAnimation"
        self._animation_events: list[dict] = []
        self._animation_frames: list[int] = [0]
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
            "behavior": False,
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
        if hasattr(self, "_event_router"):
            self._event_router.reset_runtime_input("troca de Scene/Game")
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
        self._autosave.schedule()

    def _restore_history(self, snapshot: list[dict]) -> None:
        self._history_controller.restore(snapshot)
        self._autosave.schedule()

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

    def _group_objects(self, names: list[str]) -> None:
        if not names or len(names) < 2:
            return
        group_name = self._scene_objects.unique_name("Novo Grupo")
        # Cria objeto Grupo na cena com atributos de Transform padrão
        group_obj = {
            "name": group_name,
            "is_group": True,
            "x": 0.0, "y": 0.0, "w": 0.0, "h": 0.0, "rotation": 0.0,
            "parent": None,
            "children": []
        }
        for n in names:
            if n in self._objects_by_name:
                obj = self._objects_by_name[n]
                obj["parent"] = group_name
                group_obj["children"].append(obj)
        self._scene_snapshot.append(group_obj)
        self._objects_by_name[group_name] = group_obj
        self._refresh_hierarchy(force=True)
        self._record_history()

    def _duplicate_selected(self) -> None:
        self._scene_objects.duplicate_selected()

    def _refresh_hierarchy(self, force: bool = False) -> None:
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

    def _on_inspector_tag_changed(self, new_tag: str) -> None:
        if getattr(self, "_updating_inspector", False) or not self._selected_name:
            return
        obj = self._objects_by_name.get(self._selected_name)
        if not obj:
            return
        tag_str = str(new_tag).strip()
        if tag_str == "+ Criar Nova Tag...":
            from PySide6.QtWidgets import QInputDialog
            custom_tag, ok = QInputDialog.getText(self, "Criar Nova Tag", "Digite o nome da nova Tag:")
            if ok and custom_tag.strip():
                tag_str = custom_tag.strip()
            else:
                curr = str(obj.get("tag", "Untagged"))
                if hasattr(self, "tag_combo"):
                    self.tag_combo.blockSignals(True)
                    self.tag_combo.setCurrentText(curr)
                    self.tag_combo.blockSignals(False)
                return

        if not tag_str:
            tag_str = "Untagged"

        if hasattr(self, "tag_combo"):
            if self.tag_combo.findText(tag_str) < 0:
                idx = max(0, self.tag_combo.count() - 1) if self.tag_combo.findText("+ Criar Nova Tag...") >= 0 else self.tag_combo.count()
                self.tag_combo.insertItem(idx, tag_str)

            self.tag_combo.blockSignals(True)
            self.tag_combo.setCurrentText(tag_str)
            self.tag_combo.blockSignals(False)

        obj["tag"] = tag_str
        if hasattr(self, "_notify_scene_changed"):
            self._notify_scene_changed()

    def _send_inspector_identity(self) -> None:
        if not self._selected_name or getattr(self, "_updating_inspector", False):
            return
        obj = self._objects_by_name.get(self._selected_name)
        if not obj:
            return
        if hasattr(self, "tag_combo"):
            tag_val = str(self.tag_combo.currentText()).strip() or "Untagged"
            if tag_val != "+ Criar Nova Tag...":
                obj["tag"] = tag_val
        if hasattr(self, "layer_combo"):
            obj["layer"] = str(self.layer_combo.currentText()).strip() or "Default"
        if hasattr(self, "_notify_scene_changed"):
            self._notify_scene_changed()

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

    def _update_transform_fields_only(self, name: str, obj: dict[str, Any]) -> None:
        if name != self._selected_name:
            return
        self._updating_inspector = True
        try:
            for key in ("x", "y", "w", "h", "rotation"):
                if key in obj and key in self.inspector_fields:
                    widget = self.inspector_fields[key]
                    widget.blockSignals(True)
                    widget.setValue(float(obj[key]))
                    widget.blockSignals(False)
        finally:
            self._updating_inspector = False

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
            self._inspector_view.render_behavior(name, obj)
            self._inspector_view.render_runtime(obj)
        finally:
            self._updating_inspector = False
    def _handle_selected_event(self, message: dict) -> None:
        self._viewport_event_controller.selected(message)

    def _handle_tool_changed_event(self, message: dict) -> None:
        self._viewport_event_controller.tool_changed(message)

    def _handle_delete_selected_requested(self, message: dict) -> None:
        self._viewport_event_controller.delete_selected_requested(message)

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

    def _handle_runtime_log_event(self, message: dict) -> None:
        self._viewport_event_controller.runtime_log(message)

    def _handle_logic_trace_event(self, message: dict) -> None:
        self._viewport_event_controller.logic_trace(message)



    def _handle_stats_event(self, message: dict) -> None:
        self._viewport_event_controller.stats(message)

    def _handle_runtime_metrics_event(self, message: dict) -> None:
        self._viewport_event_controller.runtime_metrics(message)

    def _handle_load_scene_event(self, message: dict) -> None:
        raw_path = message.get("scene_path") or message.get("path")
        if raw_path:
            p = Path(str(raw_path))
            project_root = (getattr(self, "_project_root", None) or Path.cwd()).resolve()
            p = p if p.is_absolute() else (project_root / p)
            if p.exists():
                self._load_scene_snapshot(scene_path=p)
                self._commands.put({
                    "type": "scene_snapshot",
                    "objects": deepcopy(self._scene_snapshot),
                })

    def _read_viewport_events(self) -> None:
        self._viewport_event_controller.poll()

    def closeEvent(self, event) -> None:
        self._session_controller.shutdown()
        super().closeEvent(event)

    def _refresh_assets(self) -> None:
        """Atualiza o painel de Assets após criar ou salvar arquivos."""
        candidates = (
            getattr(self, "assets_panel", None),
            getattr(self, "asset_browser", None),
            getattr(self, "resources_panel", None),
            getattr(self, "project_panel", None),
            getattr(self, "asset_manager_panel", None),
        )

        for panel in candidates:
            if panel is None:
                continue

            for method_name in (
                "refresh",
                "refresh_assets",
                "reload",
                "reload_assets",
                "scan_assets",
                "rescan",
            ):
                method = getattr(panel, method_name, None)

                if callable(method):
                    method()
                    return


def main() -> None:
    _install_crash_logging(Path.cwd())
    context = mp.get_context("spawn")

    # The Qt editor must not boot the complete runtime in this process.
    # Pygame/SDL belongs exclusively to the isolated viewport child process.
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
