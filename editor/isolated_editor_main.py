"""Inicializa Interface Qt e Viewport Pygame em processos independentes.

Execute a partir da raiz do projeto:
    python -m editor.isolated_editor_main
"""
from __future__ import annotations

import multiprocessing as mp
import sys
import json
import shutil
import uuid
from copy import deepcopy
from pathlib import Path
from typing import Any

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QEvent, Qt, QTimer
from PySide6.QtGui import QAction, QActionGroup, QColor, QPixmap
from PySide6.QtWidgets import (
    QColorDialog, QFileDialog, QInputDialog, QMenu, QToolBar,
    QHBoxLayout, QFormLayout,
    QCheckBox, QLabel, QComboBox, QLineEdit,
    QMessageBox, QPushButton, QDoubleSpinBox,
)
from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem, QWidget

from editor.interface_smoke_test import InterfaceSmokeTest
from editor.controllers.logic_assets import LogicAssetRepository
from editor.isolated_viewport import run_viewport
from editor.runtime.native_ui import normalize_ui
from editor.runtime.viewport_process_controller import ViewportProcessController
from editor.runtime.isolated_play_mode_controller import IsolatedPlayModeController
from editor.runtime.scene_selection_controller import SceneSelectionController
from editor.runtime.viewport_event_dispatcher import ViewportEventDispatcher
from editor.runtime.scene_history import SceneHistory
from editor.runtime.editor_event_router import EditorEventRouter
from editor.inspector_controller import InspectorComponentController, IsolatedInspectorController
from editor.inspector_view_renderer import InspectorViewRenderer
from editor.animation_workspace_controller import AnimationWorkspaceController
from editor.animation_workspace_operations import AnimationWorkspaceOperations
from editor.asset_preview_service import AssetPreviewService
from editor.scene_persistence import EditorScenePersistence
from editor.hierarchy_view_renderer import HierarchyViewRenderer
from editor.script_workspace_controller import ScriptWorkspaceController
from editor.runtime.sprite_rendering import assign_sprite_texture
from editor.widgets.component_picker import ComponentPickerDialog
from editor.widgets.logic_graph_picker import LogicGraphPickerDialog
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
from engine.logic.graph_asset import (
    create_logic_node, default_logic_graph, load_logic_graph,
    save_logic_graph, validate_logic_graph,
)
from engine.prefabs.prefab_asset import (
    apply_exposed_properties, create_prefab_variant, load_prefab_asset,
    resolve_prefab_parameters,
)
from editor.widgets.build_report_dialog import BuildReportDialog
from editor.widgets.project_validation_dialog import ProjectValidationDialog
from engine.build import (
    BuildReport, ProjectValidationReport,
    export_development_project_with_report, validate_project,
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
        self._last_build_report: BuildReport | None = None
        self._last_validation_report: ProjectValidationReport | None = None
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
        self._pending_viewport_size: tuple[int, int] | None = None
        self._last_viewport_size_sent: tuple[int, int] | None = None
        self._viewport_resize_timer = QTimer(self)
        self._viewport_resize_timer.setSingleShot(True)
        self._viewport_resize_timer.setInterval(24)
        self._viewport_resize_timer.timeout.connect(self._flush_viewport_resize)
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
        self._updating_inspector = False
        self._scene_history = SceneHistory(max_commands=100, max_bytes=16 * 1024 * 1024)
        self._inspector_controller = IsolatedInspectorController(self)
        self._inspector_components = InspectorComponentController(self)
        self._inspector_view = InspectorViewRenderer(self)
        self._animation_workspace = AnimationWorkspaceController(self)
        self._script_workspace = ScriptWorkspaceController(self)
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

        # Habilita Drag & Drop na árvore de assets e viewport_host
        self.assets_tree.setDragEnabled(True)
        self.viewport_host.setAcceptDrops(True)
        self.viewport_host.installEventFilter(self)
        self._hierarchy_drop_targets = {self.hierarchy_tree, self.hierarchy_tree.viewport()}
        self._inspector_drop_targets = {self.inspector_panel, *self.inspector_panel.findChildren(QWidget)}
        self._scene_drop_targets = {self.viewport_tabs, self.viewport_tabs.tabBar(), self.viewport_host}
        self._script_drop_targets = self._hierarchy_drop_targets | self._inspector_drop_targets | self._scene_drop_targets
        self._event_router = EditorEventRouter(self)
        for target in self._script_drop_targets:
            target.setAcceptDrops(True)
            target.installEventFilter(self)
        QApplication.instance().installEventFilter(self)
        self._scene_controller.publish_snapshot(self._scene_snapshot)
        self._event_timer = QTimer(self)
        self._event_timer.timeout.connect(self._read_viewport_events)
        self._event_timer.start(33)
        self._animator_preview_timer = QTimer(self)
        self._animator_preview_timer.timeout.connect(self._tick_animation_preview)
        self._animator_preview_timer.start(125)
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
        self._viewport_controller.attach(process)
        self._viewport_process = process

    def native_viewport_size(self) -> tuple[int, int]:
        """Return physical pixels expected by the native Pygame child window."""
        scale = max(1.0, float(self.viewport_host.devicePixelRatioF()))
        return (
            max(32, round(self.viewport_host.width() * scale)),
            max(32, round(self.viewport_host.height() * scale)),
        )

    def eventFilter(self, watched, event) -> bool:
        handled = self._event_router.handle(watched, event)
        if handled is not None:
            return handled
        return super().eventFilter(watched, event)

    def _flush_viewport_resize(self) -> None:
        """Agrupa a rajada de Resize do Qt e envia sempre o último tamanho."""
        size = self._pending_viewport_size
        self._pending_viewport_size = None
        if size is None or size == self._last_viewport_size_sent:
            return
        self._last_viewport_size_sent = size
        self._commands.put({"type": "viewport_size", "w": size[0], "h": size[1]})

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
        self.logic_workspace.message.connect(self._log)
        self.logic_workspace.asset_changed.connect(self._refresh_assets)
        self.logic_workspace.debug_command.connect(self._send_logic_debug_command)
        self.logic_workspace.play_requested.connect(lambda: self._send_toolbar_command({"type": "play"}))
        self.logic_workspace.stop_requested.connect(lambda: self._send_toolbar_command({"type": "stop"}))
        animation_action = QAction(editor_icon("play"), "Editor de Animação", self)
        animation_action.triggered.connect(self._show_animation_window)
        logic_action = QAction(editor_icon("snap"), "Editor de Lógica Visual", self)
        logic_action.triggered.connect(self._show_logic_window)
        self.editor_menus["Janela"].addSeparator()
        self.editor_menus["Janela"].addAction(animation_action)
        self.editor_menus["Janela"].addAction(logic_action)

    def _send_logic_debug_command(self, command: str) -> None:
        """Sincroniza breakpoints e controles do depurador com a Viewport."""
        path = self.logic_workspace.current_path
        if path is None:
            self._log("WARNING", "Abra ou salve um Logic Graph antes de depurar")
            return
        graph = self.logic_workspace.graph_data()
        try:
            graph_path = path.resolve().relative_to(Path.cwd().resolve()).as_posix()
        except (OSError, ValueError):
            graph_path = str(path)
        self._commands.put({
            "type": "logic_debug_command",
            "command": str(command),
            "graph": graph_path,
            "breakpoints": list(graph.get("debug", {}).get("breakpoints", [])),
            "breakpoint_conditions": dict(graph.get("debug", {}).get("breakpoint_conditions", {})),
            "watches": list(graph.get("debug", {}).get("watches", [])),
            "variables": deepcopy(graph.get("variables", {})),
        })


    def _show_logic_window(self, _checked: bool = False, *, preferred_path: Path | None = None) -> None:
        selected = self._selected_name if self._selected_name in self._objects_by_name else None
        if selected is not None:
            bindings = self._logic_graphs_for_object(selected)
            context_path = preferred_path or (bindings[0][0] if bindings else None)
            if not self.logic_workspace.open_for_object(selected, context_path):
                return
            self.logic_window.setWindowTitle(f"Zennity — Lógica Visual — {selected}")
            source = context_path.name if context_path is not None else "novo rascunho"
            self.statusBar().showMessage(f"Lógica Visual: {selected} • {source}")
        elif preferred_path is not None:
            if not self.logic_workspace.open_asset(preferred_path):
                return
            self.logic_window.setWindowTitle("Zennity — Editor de Lógica Visual")
        else:
            self.statusBar().showMessage("Selecione um objeto na Hierarchy para definir o alvo da lógica")
        self.logic_window.show()
        self.logic_window.raise_()
        self.logic_window.activateWindow()
        self._log("INFO", f"Editor de Lógica Visual aberto{f' para {selected}' if selected else ''}")

    def _logic_assets(self) -> list[tuple[Path, dict]]:
        return self._logic_assets_repository.assets()

    def _logic_graphs_for_object(self, object_name: str) -> list[tuple[Path, dict]]:
        obj = self._objects_by_name.get(object_name, {})
        return self._logic_assets_repository.for_object(object_name, obj)

    def _save_logic_binding(self, path: Path, graph: dict) -> None:
        self._logic_assets_repository.save(path, graph)
        self._refresh_assets()
        if self._selected_name in self._objects_by_name:
            self._update_inspector(self._selected_name)

    def _choose_logic_graph_component(self) -> None:
        if self._selected_name not in self._objects_by_name:
            return
        assets = self._logic_assets()
        if not assets:
            self.statusBar().showMessage("Nenhum Logic Graph disponível; use Criar novo")
            self._create_logic_graph_for_selected()
            return
        picker = LogicGraphPickerDialog(assets, self)
        if picker.exec() and picker.selected_path is not None:
            graph = deepcopy(load_logic_graph(picker.selected_path))
            graph["enabled"] = True
            graph["target"] = {"type": "name", "value": self._selected_name}
            self._component_expanded["logic"] = True
            self._save_logic_binding(picker.selected_path, graph)
            self._log("INFO", f"{picker.selected_path.name} vinculado a {self._selected_name}")

    def _create_logic_graph_for_selected(self) -> None:
        if self._selected_name not in self._objects_by_name:
            return
        directory = Path.cwd() / "Assets" / "Logic"
        directory.mkdir(parents=True, exist_ok=True)
        safe_name = "".join(character if character.isalnum() else "_" for character in self._selected_name).strip("_") or "Object"
        path = directory / f"{safe_name}Logic.zlogic"
        suffix = 2
        while path.exists():
            path = directory / f"{safe_name}Logic{suffix}.zlogic"
            suffix += 1
        graph = default_logic_graph(path.stem)
        graph["target"] = {"type": "name", "value": self._selected_name}
        graph["nodes"] = [create_logic_node("event_start", (80.0, 100.0))]
        save_logic_graph(path, graph)
        self._logic_assets_repository.invalidate(path)
        self._component_expanded["logic"] = True
        self._refresh_assets()
        self._update_inspector(self._selected_name)
        self._show_logic_window(preferred_path=path)
        self._log("INFO", f"Logic Graph criado para {self._selected_name}: {path.name}")

    def _selected_logic_path(self) -> Path | None:
        value = self.logic_graph_combo.currentData()
        return Path(str(value)).resolve() if value else None

    def _open_selected_logic_graph(self) -> None:
        path = self._selected_logic_path()
        if path is None or not path.is_file():
            return
        self._show_logic_window(preferred_path=path)

    def _detach_selected_logic_graph(self) -> None:
        path = self._selected_logic_path()
        if path is None or not path.is_file():
            return
        graph = deepcopy(load_logic_graph(path))
        graph["enabled"] = False
        self._save_logic_binding(path, graph)
        self._log("INFO", f"Logic Graph desvinculado: {path.name}")

    def _remove_all_logic_graphs(self) -> None:
        if self._selected_name not in self._objects_by_name:
            return
        bindings = self._logic_graphs_for_object(self._selected_name)
        if not bindings:
            return
        answer = QMessageBox.question(
            self, "Desvincular lógica",
            f"Desvincular {len(bindings)} Logic Graph(s) de {self._selected_name}? Os arquivos serão preservados.",
        )
        if answer != QMessageBox.Yes:
            return
        for path, source in bindings:
            graph = deepcopy(source)
            graph["enabled"] = False
            save_logic_graph(path, graph)
            self._logic_assets_repository.invalidate(path)
        self._refresh_assets()
        self._update_inspector(self._selected_name)
        self._log("INFO", f"Lógica Visual desvinculada de {self._selected_name}")

    def _update_logic_graph_summary(self, _index: int = -1) -> None:
        path = self._selected_logic_path()
        if path is None or not path.is_file():
            self.logic_summary_label.setText("Nenhum Logic Graph selecionado.")
            self.logic_open_button.setEnabled(False)
            self.logic_unlink_button.setEnabled(False)
            return
        try:
            graph = load_logic_graph(path)
            events = [node.get("title", "Evento") for node in graph.get("nodes", []) if str(node.get("type", "")).startswith("event_")]
            issues = validate_logic_graph(graph)
            problem_count = len([issue for issue in issues if issue.get("level") == "error"])
            summary = f"{len(graph.get('nodes', []))} blocos • {len(events)} eventos"
            if events:
                summary += f"\n{', '.join(str(event) for event in events[:3])}"
            summary += f"\n{'Pronto para executar' if not problem_count else f'{problem_count} erro(s) de validação'}"
            self.logic_summary_label.setText(summary)
            self.logic_open_button.setEnabled(True)
            self.logic_unlink_button.setEnabled(True)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            self.logic_summary_label.setText(f"Asset inválido: {exc}")

    def _build_viewport_link_toolbar(self) -> None:
        toolbar = QToolBar("Ligação com Viewport")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        for label, payload in (
            ("Selecionar Player", {"type": "select_object", "name": "Player"}),
            ("Mover ←", {"type": "move_selected", "dx": -16}),
            ("Mover →", {"type": "move_selected", "dx": 16}),
            ("Reset", {"type": "reset_from_interface"}),
        ):
            action = QAction(label, self)
            action.triggered.connect(lambda checked=False, message=payload: self._send_toolbar_command(message))
            toolbar.addAction(action)

    def _configure_main_menus(self) -> None:
        for label in ("Novo", "Abrir", "Salvar"):
            self.editor_menus["Arquivo"].addAction(self.toolbar_actions[label])
        for label in ("Select", "Move", "Rotate", "Scale", "Snap: OFF"):
            self.editor_menus["Ferramentas"].addAction(self.toolbar_actions[label])
        for label in ("Play", "Pause", "Stop"):
            self.editor_menus["Executar"].addAction(self.toolbar_actions[label])
        validate_action = self.editor_menus["Build"].addAction("Validar projeto...")
        validate_action.triggered.connect(self._validate_current_project)
        self.editor_menus["Build"].addSeparator()
        export_action = self.editor_menus["Build"].addAction("Exportar projeto...")
        export_action.triggered.connect(self._export_project)
        report_action = self.editor_menus["Build"].addAction("Último relatório...")
        report_action.setEnabled(False)
        report_action.triggered.connect(self._show_last_build_report)
        self._build_report_action = report_action
        self.toolbar_actions["Pause"].setEnabled(False)
        self.toolbar_actions["Stop"].setEnabled(False)
        snap_action = self.toolbar_actions["Snap: OFF"]
        snap_action.setCheckable(True)
        snap_action.toggled.connect(self._toggle_snap)

    def _toggle_snap(self, enabled: bool) -> None:
        self._snap_enabled = bool(enabled)
        action = self.toolbar_actions["Snap: OFF"]
        action.setText("Snap: ON" if enabled else "Snap: OFF")
        self._commands.put({"type": "set_snap", "enabled": bool(enabled), "size": 16.0, "angle": 15.0})
        self.statusBar().showMessage("Snap ativado" if enabled else "Snap desativado")

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
        self.prefab_tree.clear()
        root = QTreeWidgetItem(["📦 Prefabs"])
        self.prefab_tree.addTopLevelItem(root)
        directory = Path.cwd() / "Assets" / "Prefabs"
        directory.mkdir(parents=True, exist_ok=True)
        for path in sorted(directory.rglob("*.zprefab"), key=lambda item: str(item).lower()):
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
                variant = bool(payload.get("base_prefab")) if isinstance(payload, dict) else False
            except (OSError, json.JSONDecodeError):
                variant = False
            item = QTreeWidgetItem([("↳ " if variant else "🧩 ") + path.stem])
            item.setToolTip(0, str(path))
            root.addChild(item)
        root.setExpanded(True)

    def _save_selected_as_prefab(self) -> None:
        if self._selected_name not in self._objects_by_name:
            return
        default_name = self._selected_name
        name, accepted = QInputDialog.getText(self, "Criar Prefab", "Nome do Prefab:", text=default_name)
        name = "".join(char for char in name.strip() if char.isalnum() or char in "-_ ")
        if not accepted or not name:
            return
        path = Path.cwd() / "Assets" / "Prefabs" / f"{name}.zprefab"
        prefab_object = deepcopy(self._objects_by_name[self._selected_name])
        prefab_object.pop("id", None)
        exposed = [
            {"name": "width", "label": "Largura", "type": "number", "default": float(prefab_object.get("w", 64.0)), "target": "w"},
            {"name": "height", "label": "Altura", "type": "number", "default": float(prefab_object.get("h", 64.0)), "target": "h"},
            {"name": "color", "label": "Cor", "type": "color", "default": prefab_object.get("color", "#ffffff"), "target": "color"},
            {"name": "image", "label": "Imagem", "type": "image", "default": prefab_object.get("texture", ""), "target": "texture"},
            {"name": "tag", "label": "Tag", "type": "text", "default": prefab_object.get("tag", "Untagged"), "target": "tag"},
            {"name": "layer", "label": "Layer", "type": "text", "default": prefab_object.get("layer", "Default"), "target": "layer"},
        ]
        payload = {"format_version": 2, "prefab_name": name, "object": prefab_object, "exposed_properties": exposed}
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        self._refresh_prefabs()
        self._refresh_assets()
        self._log("INFO", f"Prefab criado: {path.name}")

    def _instantiate_prefab_item(self, item: QTreeWidgetItem) -> None:
        path_value = item.toolTip(0)
        if not path_value:
            return
        try:
            payload = load_prefab_asset(path_value, Path.cwd())
            prefab_object = deepcopy(payload["object"])
            definitions = payload.get("exposed_properties", [])
            values = resolve_prefab_parameters(definitions, {})
            apply_exposed_properties(prefab_object, definitions, values)
            if any(key in prefab_object for key in ("transform", "visual", "components")):
                raise ValueError("use o Play Mode para instanciar este formato legado")
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            self._log("ERROR", f"Falha ao abrir Prefab: {exc}")
            return
        self._record_history()
        obj = deepcopy(prefab_object)
        obj["id"] = str(uuid.uuid4())
        obj["name"] = self._unique_name(str(obj.get("name") or payload.get("prefab_name") or "Prefab"))
        obj["x"] = float(obj.get("x", 0.0)) + 16.0
        obj["y"] = float(obj.get("y", 0.0)) + 16.0
        self._scene_snapshot.append(obj)
        self._objects_by_name[obj["name"]] = obj
        self._selected_name = obj["name"]
        self._refresh_hierarchy()
        self._scene_controller.publish_snapshot(self._scene_snapshot)
        self._scene_controller.select(obj["name"])
        self._update_inspector(obj["name"])
        self._log("INFO", f"Prefab adicionado: {obj['name']}")

    def _open_prefab_menu(self, position) -> None:
        item = self.prefab_tree.itemAt(position)
        path_value = item.toolTip(0) if item is not None else ""
        if not path_value or not Path(path_value).is_file():
            return
        menu = QMenu(self)
        instantiate = menu.addAction("Adicionar à cena")
        variant = menu.addAction("Criar variante...")
        instantiate.triggered.connect(lambda _checked=False: self._instantiate_prefab_item(item))
        variant.triggered.connect(lambda _checked=False: self._create_prefab_variant(Path(path_value)))
        menu.exec(self.prefab_tree.viewport().mapToGlobal(position))

    def _create_prefab_variant(self, base_path: Path) -> None:
        name, accepted = QInputDialog.getText(
            self, "Criar variante de Prefab", "Nome da variante:", text=f"{base_path.stem}Variant"
        )
        safe = "".join(char for char in name.strip() if char.isalnum() or char in "-_ ")
        if not accepted or not safe:
            return
        target = base_path.parent / f"{safe}.zprefab"
        if target.exists() and QMessageBox.question(self, "Substituir variante", f"{target.name} já existe. Substituir?") != QMessageBox.Yes:
            return
        try:
            create_prefab_variant(base_path, target, project_root=Path.cwd())
        except (OSError, ValueError) as exc:
            self._log("ERROR", f"Falha ao criar variante: {exc}")
            return
        self._refresh_prefabs()
        self._refresh_assets()
        self._log("INFO", f"Variante criada: {target.name} → {base_path.name}")

    def _export_project(self) -> None:
        self._save_scene_snapshot()
        if self._current_scene_path is None:
            return
        validation = validate_project(Path.cwd(), self._current_scene_path)
        self._last_validation_report = validation
        if not validation.valid:
            self._log("ERROR", f"Exportação bloqueada por {len(validation.errors)} erro(s) de validação")
            self.statusBar().showMessage("Corrija os erros de validação antes de exportar")
            ProjectValidationDialog(validation, self).exec()
            return
        output = QFileDialog.getExistingDirectory(self, "Pasta para exportar", str(Path.cwd() / "Builds"))
        if not output:
            return
        default_name = str((self._scene_document or {}).get("scene_name", "ZennityGame"))
        project_name, accepted = QInputDialog.getText(self, "Exportar projeto", "Nome do jogo:", text=default_name)
        if not accepted or not project_name.strip():
            return
        report = export_development_project_with_report(
            Path.cwd(), self._current_scene_path, Path(output), project_name
        )
        self._last_build_report = report
        self._build_report_action.setEnabled(True)
        if report.success:
            self._log(
                "INFO",
                f"Projeto exportado: {report.destination} "
                f"({report.file_count} arquivos, {len(report.warnings)} aviso(s))",
            )
            self.statusBar().showMessage(f"Build criado em {report.destination}")
        else:
            self._log("ERROR", f"Build não concluído: {len(report.errors)} erro(s)")
            self.statusBar().showMessage("Build não concluído — consulte o relatório")
        self._show_last_build_report()

    def _validate_current_project(self) -> None:
        self._save_scene_snapshot()
        if self._current_scene_path is None:
            return
        report = validate_project(Path.cwd(), self._current_scene_path)
        self._last_validation_report = report
        if report.valid:
            self._log("INFO", f"Projeto validado: {len(report.warnings)} aviso(s), nenhum erro")
            self.statusBar().showMessage("Projeto pronto para exportar")
        else:
            self._log("ERROR", f"Validação encontrou {len(report.errors)} erro(s) e {len(report.warnings)} aviso(s)")
            self.statusBar().showMessage("Projeto precisa de correções antes da exportação")
        ProjectValidationDialog(report, self).exec()

    def _show_last_build_report(self) -> None:
        if self._last_build_report is None:
            return
        BuildReportDialog(self._last_build_report, self).exec()

    def _connect_existing_toolbar_actions(self) -> None:
        commands = {
            "Novo": {"type": "new_scene"},
            "Abrir": {"type": "load_scene"},
            "Salvar": {"type": "save_scene"},
            "Play": {"type": "play"},
            "Pause": {"type": "pause"},
            "Stop": {"type": "stop"},
        }
        for action in self.findChildren(QAction):
            label = action.toolTip() if action.toolTip() else action.text()
            payload = commands.get(label)
            if payload is not None:
                action.triggered.connect(
                    lambda checked=False, message=payload: self._send_toolbar_command(message)
                )

    def _configure_tool_actions(self) -> None:
        group = QActionGroup(self)
        group.setExclusive(True)
        shortcuts = {"select": "Q", "move": "W", "rotate": "E", "scale": "R"}
        for action in self.findChildren(QAction):
            label = action.toolTip() if action.toolTip() else action.text()
            tool = label.lower()
            if tool not in {"select", "move", "rotate", "scale"}:
                continue
            action.setCheckable(True)
            action.setShortcut(shortcuts[tool])
            action.setChecked(tool == "select")
            group.addAction(action)
            action.triggered.connect(lambda checked=False, name=tool: checked and self._commands.put({"type": "set_tool", "tool": name}))
        self._tool_action_group = group

    def _send_toolbar_command(self, message: dict) -> None:
        command_type = str(message.get("type", ""))
        if self._play_controller.blocks(command_type):
            self.statusBar().showMessage("Pare o Play Mode antes de alterar a cena")
            return
        if message.get("type") == "new_scene":
            self._new_scene()
            return
        if message.get("type") == "save_scene":
            self._save_scene_snapshot()
            return
        if message.get("type") == "load_scene":
            self._load_scene_snapshot()
            return
        if message.get("type") == "reset_from_interface":
            self._record_history()
            self._scene_snapshot = deepcopy(self._initial_scene_snapshot)
            self._objects_by_name = {item["name"]: item for item in self._scene_snapshot}
            self._refresh_hierarchy()
            self._scene_controller.publish_snapshot(self._scene_snapshot)
            if self._selected_name in self._objects_by_name:
                self._update_inspector(self._selected_name)
            return
        if command_type in {"play", "pause", "stop"}:
            plan = self._play_controller.plan(
                message,
                scene_objects=self._scene_snapshot,
                selected_name=self._selected_name,
                scene_blackboard=(self._scene_document or {}).get("blackboard", {}),
            )
            if command_type == "play":
                self._runtime_playing = True
                self._set_play_mode_editing_locked(True)
                self.logic_workspace.set_play_state(True)
                self.toolbar_actions["Play"].setEnabled(False)
                self.toolbar_actions["Pause"].setEnabled(False)
                self.toolbar_actions["Stop"].setEnabled(True)
                self.viewport_tabs.setCurrentIndex(1)
                if plan.resuming:
                    self._log("INFO", "Retomando Play pausado")
                else:
                    logic_directory = Path.cwd() / "Assets" / "Logic"
                    logic_assets = list(logic_directory.rglob("*.zlogic")) if logic_directory.exists() else []
                    self._log("INFO", f"Play solicitado com {len(logic_assets)} Logic Graph(s); scripts Python desativados")
                    audio_sources = plan.audio_sources or {}
                    enabled_audio = [name for name, audio in audio_sources.items() if audio.get("autoplay") and audio.get("path")]
                    self._log("INFO", f"Play enviando {len(audio_sources)} Audio Source(s); {len(enabled_audio)} configurado(s) para iniciar")
            elif command_type == "stop":
                self.viewport_tabs.setCurrentIndex(0)
            for command in plan.commands:
                self._commands.put(command)
            return
        if message.get("type") == "move_selected" and self._selected_name is not None:
            self._record_history()
        self._commands.put(message)

    def _set_play_mode_editing_locked(self, locked: bool) -> None:
        """Mantém a inspeção visível, mas impede alterações na cena em execução."""
        self.inspector_panel.setEnabled(not locked)
        self.hierarchy_tree.setDragEnabled(not locked)
        for label in ("Desfazer", "Refazer", "Move", "Rotate", "Scale", "Snap: OFF"):
            action = self.toolbar_actions.get(label)
            if action is not None:
                action.setEnabled(not locked)
        create_menu = self.editor_menus.get("Criar")
        if create_menu is not None:
            for action in create_menu.actions():
                action.setEnabled(not locked)

    def _configure_create_menu(self) -> None:
        for menu_action in self.menuBar().actions():
            menu = menu_action.menu()
            if menu is None or menu.title() != "Criar":
                continue
            menu.clear()
            for label, kind in (
                ("Empty Object", "Empty"), ("Sprite 2D", "Sprite"),
                ("Player 2D", "Player"), ("Platform 2D", "Platform"),
                ("Enemy 2D", "Enemy"), ("Trigger 2D", "Trigger"),
                ("Camera 2D", "Camera"),
            ):
                action = menu.addAction(label)
                action.triggered.connect(lambda checked=False, object_kind=kind: self._create_object(object_kind))
            break

    def _configure_edit_menu(self) -> None:
        for menu_action in self.menuBar().actions():
            menu = menu_action.menu()
            if menu is None or menu.title() != "Editar":
                continue
            menu.clear()
            undo_action = self.toolbar_actions["Desfazer"]
            undo_action.setShortcut("Ctrl+Z")
            undo_action.triggered.connect(self._undo)
            menu.addAction(undo_action)
            redo_action = self.toolbar_actions["Refazer"]
            redo_action.setShortcut("Ctrl+Y")
            redo_action.triggered.connect(self._redo)
            menu.addAction(redo_action)
            menu.addSeparator()
            duplicate_action = menu.addAction("Duplicar")
            duplicate_action.setShortcut("Ctrl+D")
            duplicate_action.triggered.connect(self._duplicate_selected)
            delete_action = menu.addAction("Excluir")
            delete_action.setShortcut("Delete")
            delete_action.triggered.connect(
                lambda _checked=False: self._selected_name is not None and self._delete_object(self._selected_name)
            )
            break

    def _record_history(self, snapshot: list[dict] | None = None) -> None:
        if snapshot is None:
            self._scene_history.begin(self._scene_snapshot)
        else:
            self._scene_history.commit(snapshot, self._scene_snapshot)

    def _restore_history(self, snapshot: list[dict]) -> None:
        self._scene_snapshot = deepcopy(snapshot)
        self._objects_by_name = {item["name"]: item for item in self._scene_snapshot}
        if self._selected_name not in self._objects_by_name:
            self._selected_name = None
        self._refresh_hierarchy()
        self._scene_controller.publish_snapshot(self._scene_snapshot)
        if self._selected_name is not None:
            self._scene_controller.select(self._selected_name)
            self._update_inspector(self._selected_name)

    def _undo(self) -> None:
        restored = self._scene_history.undo(self._scene_snapshot)
        if restored is not None:
            self._restore_history(restored)

    def _redo(self) -> None:
        restored = self._scene_history.redo(self._scene_snapshot)
        if restored is not None:
            self._restore_history(restored)

    def _new_scene(self) -> None:
        self._record_history()
        self._scene_snapshot = []
        self._objects_by_name = {}
        self._scene_document = {"format_version": 1, "scene_name": "Untitled", "engine_version": "Zennity 0.1.0", "objects": []}
        self._current_scene_path = None
        self._selected_name = None
        self._refresh_hierarchy()
        self._scene_controller.publish_snapshot([])
        self.statusBar().showMessage("Nova cena criada")
        self._log("INFO", "Nova cena criada")

    def _unique_name(self, base: str) -> str:
        if base not in self._objects_by_name:
            return base
        index = 2
        while f"{base}_{index}" in self._objects_by_name:
            index += 1
        return f"{base}_{index}"

    def _create_object(self, kind: str) -> None:
        if self._play_session.is_running:
            return
        self._record_history()
        presets = {
            "Empty": ("GameObject", 40.0, 40.0, (160, 164, 174), None),
            "Sprite": ("Sprite", 64.0, 64.0, (180, 180, 190), None),
            "Player": ("Player", 36.0, 48.0, (88, 117, 255), {"is_kinematic": False, "use_gravity": True, "gravity_scale": 1.0}),
            "Platform": ("Platform", 160.0, 32.0, (91, 194, 100), {"is_kinematic": True, "use_gravity": False}),
            "Enemy": ("Enemy", 40.0, 40.0, (220, 88, 88), {"is_kinematic": False, "use_gravity": True, "gravity_scale": 1.0}),
            "Trigger": ("Trigger", 80.0, 80.0, (222, 178, 72), {"is_kinematic": True, "use_gravity": False}),
            "Camera": ("Camera2D", 96.0, 54.0, (110, 190, 210), None),
        }
        base, width, height, color, rigidbody = presets[kind]
        name = self._unique_name(base)
        obj = {"id": str(uuid.uuid4()), "name": name, "x": 450.0, "y": 250.0, "w": width, "h": height, "rotation": 0.0, "color": color, "mesh_type": kind}
        if rigidbody is not None:
            obj["rigidbody"] = rigidbody
            obj["collider"] = {"type": "box"}
        if kind == "Trigger":
            obj["collider"]["is_trigger"] = True
        if kind == "Camera":
            obj["component_names"] = ["Camera2D"]
            obj["camera"] = {"active": True, "zoom": 1.0}
        self._scene_snapshot.append(obj)
        self._objects_by_name[name] = obj
        self._selected_name = name
        self._refresh_hierarchy()
        self._scene_controller.publish_snapshot(self._scene_snapshot)
        self._scene_controller.select(name)
        self._update_inspector(name)
        self._log("INFO", f"Objeto criado: {name}")

    def _create_object_at(self, kind: str, screen_x: float, screen_y: float) -> None:
        self._record_history()
        self._commands.put({
            "type": "create_object_at",
            "kind": kind,
            "screen_x": screen_x,
            "screen_y": screen_y
        })

    def _create_sprite_at(self, texture_path: Path, screen_x: float, screen_y: float) -> None:
        try:
            relative = str(texture_path.resolve().relative_to(Path.cwd().resolve())).replace("\\", "/")
        except ValueError:
            relative = str(texture_path.resolve())
        pixmap = QPixmap(str(texture_path))
        width = float(pixmap.width()) if not pixmap.isNull() else 64.0
        height = float(pixmap.height()) if not pixmap.isNull() else 64.0
        self._record_history()
        self._commands.put({
            "type": "create_sprite_at", "texture": relative,
            "screen_x": screen_x, "screen_y": screen_y,
            "width": max(1.0, width), "height": max(1.0, height),
        })

    def _save_scene_snapshot(self) -> None:
        filename, _ = QFileDialog.getSaveFileName(
            self, "Salvar cena", str(self._current_scene_path or "Untitled.zscene"),
            "Zennity Scene (*.zscene);;Cena JSON (*.json)",
        )
        if not filename:
            return
        path = Path(filename)
        try:
            payload = self._scene_persistence.save(
                path, self._scene_snapshot, self._scene_document,
            )
        except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
            self.statusBar().showMessage(f"Falha ao salvar cena: {exc}")
            return
        self._scene_document = payload
        self._current_scene_path = path
        self.statusBar().showMessage(f"Cena salva: {filename}")
        self._log("INFO", f"Cena salva: {filename}")

    def _collect_logic_variables(self, scope: str) -> dict[str, dict[str, Any]]:
        return self._scene_persistence.collect_logic_variables(scope)

    def _load_scene_snapshot(self, _checked: bool = False, scene_path: Path | None = None) -> None:
        if scene_path is not None:
            filename = str(scene_path)
        else:
            filename, _ = QFileDialog.getOpenFileName(
                self, "Abrir cena", "", "Zennity Scene (*.zscene);;Cena JSON (*.json)",
            )
        if not filename:
            return
        try:
            payload, snapshots, typed = self._scene_persistence.load(Path(filename))
        except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
            self.statusBar().showMessage(f"Falha ao abrir cena: {exc}")
            return
        self._record_history()
        self._scene_snapshot = snapshots
        self._objects_by_name = {item["name"]: item for item in snapshots}
        self._scene_document = payload if typed else None
        self._current_scene_path = Path(filename)
        self._selected_name = None
        self._refresh_hierarchy()
        self._scene_controller.publish_snapshot(self._scene_snapshot)
        self.statusBar().showMessage(f"Cena aberta: {filename}")
        self._log("INFO", f"Cena aberta: {filename}")

    def _connect_hierarchy_to_viewport(self) -> None:
        self.hierarchy_tree.setDragEnabled(True)
        self.hierarchy_tree.setAcceptDrops(True)
        self.hierarchy_tree.setDragDropMode(QTreeWidget.InternalMove)
        self.hierarchy_tree.itemClicked.connect(self._select_hierarchy_item)
        self.hierarchy_tree.itemDoubleClicked.connect(lambda item: self._rename_object(self._hierarchy_item_name(item)))
        self.hierarchy_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.hierarchy_tree.customContextMenuRequested.connect(self._open_hierarchy_menu)

    def _open_hierarchy_menu(self, position) -> None:
        item = self.hierarchy_tree.itemAt(position)
        item_name = self._hierarchy_item_name(item)
        if item is None or item_name not in self._objects_by_name:
            return
        menu = QMenu(self)
        rename_action = menu.addAction("Renomear")
        duplicate_action = menu.addAction("Duplicar")
        prefab_action = menu.addAction("Criar Prefab")
        delete_action = menu.addAction("Excluir")
        rename_action.triggered.connect(lambda _checked=False: self._rename_object(item_name))
        duplicate_action.triggered.connect(lambda _checked=False: self._select_and_duplicate(item_name))
        prefab_action.triggered.connect(lambda _checked=False: self._select_and_save_prefab(item_name))
        delete_action.triggered.connect(lambda _checked=False: self._delete_object(item_name))
        menu.exec(self.hierarchy_tree.viewport().mapToGlobal(position))

    def _select_and_duplicate(self, name: str) -> None:
        self._selected_name = name
        self._duplicate_selected()

    def _select_and_save_prefab(self, name: str) -> None:
        self._selected_name = name
        self._save_selected_as_prefab()

    def _rename_object(self, old_name: str) -> None:
        if self._play_session.is_running:
            return
        new_name, accepted = QInputDialog.getText(self, "Renomear objeto", "Nome:", text=old_name)
        new_name = new_name.strip()
        if not accepted or not new_name or (new_name != old_name and new_name in self._objects_by_name):
            return
        self._record_history()
        obj = self._objects_by_name.pop(old_name)
        obj["name"] = new_name
        self._objects_by_name[new_name] = obj
        if self._selected_name == old_name:
            self._selected_name = new_name
        self._refresh_hierarchy()
        self._scene_controller.publish_snapshot(self._scene_snapshot)
        self._scene_controller.select(new_name)
        self._update_inspector(new_name)

    def _delete_object(self, name: str) -> None:
        if self._play_session.is_running:
            return
        self._record_history()
        self._scene_snapshot = [obj for obj in self._scene_snapshot if obj["name"] != name]
        self._objects_by_name.pop(name, None)
        if self._selected_name == name:
            self._selected_name = None
            for header, body in self.script_containers:
                self.inspector_layout.removeWidget(header)
                self.inspector_layout.removeWidget(body)
                header.deleteLater()
                body.deleteLater()
            self.script_containers.clear()
            self._clear_inspector_view()
        self._refresh_hierarchy()
        self._scene_controller.publish_snapshot(self._scene_snapshot)

    def _duplicate_selected(self) -> None:
        if self._play_session.is_running:
            return
        if self._selected_name not in self._objects_by_name:
            return
        self._record_history()
        duplicate = deepcopy(self._objects_by_name[self._selected_name])
        duplicate["id"] = str(uuid.uuid4())
        duplicate["name"] = self._unique_name(f"{self._selected_name}_copy")
        duplicate["x"] = float(duplicate.get("x", 0.0)) + 16.0
        duplicate["y"] = float(duplicate.get("y", 0.0)) + 16.0
        self._scene_snapshot.append(duplicate)
        self._objects_by_name[duplicate["name"]] = duplicate
        self._selected_name = duplicate["name"]
        self._refresh_hierarchy()
        self._scene_controller.publish_snapshot(self._scene_snapshot)
        self._scene_controller.select(self._selected_name)
        self._update_inspector(self._selected_name)

    def _refresh_hierarchy(self) -> None:
        self._hierarchy_view.refresh()

    def _hierarchy_item_name(self, item: QTreeWidgetItem | None) -> str:
        return self._hierarchy_view.item_name(item)

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
        if self._selected_name not in self._objects_by_name:
            return
        filename, _ = QFileDialog.getOpenFileName(self, "Selecionar textura", str(Path.cwd() / "Assets"), "Imagens (*.png *.jpg *.jpeg *.bmp *.webp)")
        if not filename:
            return
        path = Path(filename)
        try:
            texture = str(path.resolve().relative_to(Path.cwd().resolve())).replace("\\", "/")
        except ValueError:
            textures_dir = Path.cwd() / "Assets" / "Textures"
            textures_dir.mkdir(parents=True, exist_ok=True)
            destination = textures_dir / path.name
            index = 1
            while destination.exists() and destination.read_bytes() != path.read_bytes():
                destination = textures_dir / f"{path.stem}_{index}{path.suffix}"
                index += 1
            if not destination.exists():
                shutil.copy2(path, destination)
            texture = str(destination.relative_to(Path.cwd())).replace("\\", "/")
            self._refresh_assets()
        self._record_history()
        obj = self._objects_by_name[self._selected_name]
        assign_sprite_texture(obj, texture)
        self.sprite_texture_field.setText(texture)
        self.sprite_color_button.setStyleSheet("background: rgb(255, 255, 255);")
        self._send_inspector_renderer(record_history=False)
        self._log("INFO", f"Textura aplicada sem tint: {Path(texture).name}")

    def _choose_sprite_color(self) -> None:
        if self._selected_name not in self._objects_by_name:
            return
        current = self._objects_by_name[self._selected_name].get("color", (255, 255, 255))
        color = QColorDialog.getColor(QColor(*current[:3]), self, "Cor do Sprite")
        if not color.isValid():
            return
        self._record_history()
        self._objects_by_name[self._selected_name]["color"] = (color.red(), color.green(), color.blue())
        self.sprite_color_button.setStyleSheet(f"background: rgb({color.red()}, {color.green()}, {color.blue()});")
        self._send_inspector_renderer(record_history=False)

    def _send_inspector_renderer(self, record_history: bool = True) -> None:
        self._inspector_components.send_renderer(record_history)

    def _toggle_audio_component(self, checked: bool) -> None:
        self._inspector_components.toggle_audio(checked)

    def _get_available_audio_files(self) -> list[str]:
        audio_dir = Path.cwd() / "Assets" / "Audio"
        if not audio_dir.exists():
            return []
        audio_files = []
        for file in audio_dir.rglob("*"):
            if file.is_file() and file.suffix.lower() in {".wav", ".ogg", ".mp3"}:
                try:
                    rel_p = str(file.resolve().relative_to(Path.cwd().resolve())).replace("\\", "/")
                except ValueError:
                    rel_p = str(file).replace("\\", "/")
                audio_files.append(rel_p)
        return sorted(audio_files, key=str.lower)

    def _send_inspector_audio(self) -> None:
        self._inspector_components.send_audio()

    def _test_selected_audio(self) -> None:
        self._inspector_components.preview_audio()

    def _toggle_rigidbody_component(self, checked: bool) -> None:
        self._inspector_components.toggle_rigidbody(checked)

    def _toggle_collider_component(self, checked: bool) -> None:
        self._inspector_components.toggle_collider(checked)


    @staticmethod












































    def _toggle_camera_component(self, checked: bool) -> None:
        self._inspector_components.toggle_camera(checked)

    def _send_inspector_camera(self) -> None:
        self._inspector_components.send_camera()

    def _choose_camera_color(self) -> None:
        if self._selected_name not in self._objects_by_name:
            return
        camera = self._objects_by_name[self._selected_name].get("camera")
        if not isinstance(camera, dict):
            return
        current = camera.get("background_color", [22, 24, 31])
        color = QColorDialog.getColor(QColor(*current[:3]), self, "Cor de fundo da câmera")
        if not color.isValid():
            return
        self._record_history()
        camera["background_color"] = [color.red(), color.green(), color.blue()]
        self.camera_color_button.setStyleSheet(f"background: rgb({color.red()}, {color.green()}, {color.blue()});")
        self._scene_controller.publish_snapshot(self._scene_snapshot)

    def _toggle_ui_visibility(self, checked: bool) -> None:
        if self._updating_inspector or self._selected_name not in self._objects_by_name:
            return
        ui = self._objects_by_name[self._selected_name].get("ui")
        if not isinstance(ui, dict):
            return
        self._record_history()
        ui["visible"] = bool(checked)
        self._scene_controller.publish_snapshot(self._scene_snapshot)

    def _delete_ui_component(self) -> None:
        if self._selected_name not in self._objects_by_name:
            return
        obj = self._objects_by_name[self._selected_name]
        if "ui" not in obj:
            return
        self._record_history()
        obj.pop("ui", None)
        self._scene_controller.publish_snapshot(self._scene_snapshot)
        self._update_inspector(self._selected_name)

    def _choose_ui_color(self) -> None:
        if self._selected_name not in self._objects_by_name:
            return
        ui = normalize_ui(self._objects_by_name[self._selected_name].get("ui"))
        if ui is None:
            return
        current = tuple(ui.get("color", (255, 255, 255)))[:3]
        color = QColorDialog.getColor(QColor(*current), self, "Cor da UI")
        if not color.isValid():
            return
        self._record_history()
        self._objects_by_name[self._selected_name]["ui"]["color"] = [color.red(), color.green(), color.blue()]
        self.ui_color_button.setStyleSheet(f"background: rgb({color.red()}, {color.green()}, {color.blue()});")
        self._scene_controller.publish_snapshot(self._scene_snapshot)

    def _choose_ui_image(self) -> None:
        if self._selected_name not in self._objects_by_name:
            return
        filename, _ = QFileDialog.getOpenFileName(
            self, "Selecionar imagem da UI", str(Path.cwd() / "Assets"),
            "Imagens (*.png *.jpg *.jpeg *.bmp *.webp)",
        )
        if not filename:
            return
        path = Path(filename)
        try:
            value = str(path.resolve().relative_to(Path.cwd().resolve())).replace("\\", "/")
        except ValueError:
            value = str(path.resolve())
        self.ui_image_path_field.setText(value)
        self._send_inspector_ui()

    def _send_inspector_ui(self) -> None:
        if self._updating_inspector or self._selected_name not in self._objects_by_name:
            return
        obj = self._objects_by_name[self._selected_name]
        ui = normalize_ui(obj.get("ui"))
        if ui is None:
            return
        self._record_history()
        ui.update({key: float(field.value()) for key, field in self.ui_position_fields.items()})
        ui.update({
            "visible": self.show_ui_chk.isChecked(),
            "text": self.ui_text_field.text(),
            "path": self.ui_image_path_field.text(),
            "interactable": self.ui_interactable_field.isChecked(),
            "event": self.ui_event_field.text().strip() or "click",
            "target": "" if self.ui_target_combo.currentText() == "Este objeto" else self.ui_target_combo.currentText(),
        })
        obj["ui"] = ui
        self._scene_controller.publish_snapshot(self._scene_snapshot)

    def _ensure_canvas(self) -> None:
        if any((normalize_ui(obj.get("ui")) or {}).get("type") == "canvas" for obj in self._scene_snapshot):
            return
        name = self._unique_name("Canvas")
        canvas = {
            "id": str(uuid.uuid4()), "name": name, "x": 0.0, "y": 0.0,
            "w": 1.0, "h": 1.0, "rotation": 0.0, "color": (255, 255, 255),
            "mesh_type": "UI", "renderer_enabled": False,
            "ui": normalize_ui({"type": "canvas"}),
        }
        self._scene_snapshot.append(canvas)
        self._objects_by_name[name] = canvas
        self._log("INFO", "Canvas criado automaticamente para a interface do jogo")

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
        name = self._hierarchy_item_name(item)
        if name in self._objects_by_name or (self._runtime_playing and name in self._runtime_objects_by_name):
            self._scene_controller.select(name)
            self._selected_name = name
            self._update_inspector(name)
            source = "Runtime" if name in self._runtime_objects_by_name and name not in self._objects_by_name else "Interface"
            self.statusBar().showMessage(f"{source}: {name} selecionado")

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
        self._selected_name = message["name"]
        self._update_inspector(self._selected_name)
        self.statusBar().showMessage(f"Viewport: {self._selected_name} selecionado")

    def _handle_transform_event(self, message: dict) -> None:
        event_type = message.get("type")
        if event_type == "transform_begin":
            self._drag_history_snapshot = deepcopy(self._scene_snapshot)
            return
        if event_type == "transform_end":
            if self._drag_history_snapshot is not None and self._drag_history_snapshot != self._scene_snapshot:
                self._record_history(self._drag_history_snapshot)
            self._drag_history_snapshot = None
            return
        obj = self._objects_by_name.get(message["name"])
        if obj is not None and not self._runtime_playing:
            obj["x"] = float(message["x"])
            obj["y"] = float(message["y"])
            for field in ("w", "h", "rotation"):
                if field in message:
                    obj[field] = float(message[field])
            if message["name"] == self._selected_name:
                self._update_inspector(self._selected_name)
        self.statusBar().showMessage(
            f"Viewport: {message['name']} em X={message['x']:.1f}, Y={message['y']:.1f}"
        )

    def _handle_play_state_event(self, message: dict) -> None:
        state = message["state"]
        if state in {"play", "pause"}:
            self._play_session.set_runtime_state(state)
        if state == "edit":
            self._runtime_objects_by_name.clear()
            self.logic_workspace.clear_runtime_trace()
            self._runtime_animator_states.clear()
            if self._animator_controller_dialog is not None:
                self._animator_controller_dialog.set_runtime_state(None, {})
            self._scene_snapshot, self._selected_name = self._play_session.finish()
            self._objects_by_name = {item["name"]: item for item in self._scene_snapshot}
            self._runtime_keys = {key: False for key in self._runtime_keys}
            self._commands.put({"type": "runtime_input", "keys": dict(self._runtime_keys)})
            self._refresh_hierarchy()
            if self._selected_name in self._objects_by_name:
                self._scene_controller.select(self._selected_name)
                self._update_inspector(self._selected_name)
        self._runtime_playing = self._play_session.is_running
        running = state in {"play", "pause"}
        self._set_play_mode_editing_locked(running)
        self.toolbar_actions["Play"].setEnabled(state != "play")
        self.toolbar_actions["Pause"].setEnabled(running)
        self.toolbar_actions["Stop"].setEnabled(running)
        self.logic_workspace.set_play_state(running)
        self.statusBar().showMessage(
            {"play": "Viewport: PLAY", "pause": "Viewport: PAUSE", "edit": "Viewport: EDIT — cena restaurada"}[state]
        )
        self._log(
            "INFO",
            {"play": "Play iniciado/retomado", "pause": "Play pausado", "edit": "Play finalizado; cena restaurada"}[state],
        )

    def _handle_scene_snapshot_event(self, message: dict) -> None:
        self._scene_snapshot, restored_selection = self._play_session.consume_scene_snapshot(
            [deepcopy(item) for item in message.get("objects", [])]
        )
        if restored_selection is not None:
            self._selected_name = restored_selection
        self._objects_by_name = {item["name"]: item for item in self._scene_snapshot}
        self._refresh_hierarchy()
        if self._selected_name in self._objects_by_name:
            self._update_inspector(self._selected_name)

    def _handle_runtime_objects_event(self, message: dict) -> None:
        previous_names = set(self._runtime_objects_by_name)
        self._runtime_objects_by_name = {
            str(item.get("name")): deepcopy(item)
            for item in message.get("objects", [])
            if isinstance(item, dict) and item.get("name")
        }
        if set(self._runtime_objects_by_name) != previous_names:
            self._refresh_hierarchy()
        if self._selected_name in self._runtime_objects_by_name:
            self._update_inspector(str(self._selected_name))
        elif self._selected_name in previous_names and self._selected_name not in self._objects_by_name:
            self._selected_name = None
            self._clear_inspector_view()

    def _handle_viewport_mode_event(self, message: dict) -> None:
        state = "embutida" if message.get("embedded") else "em janela separada (fallback)"
        self.statusBar().showMessage(f"Viewport {state}")

    def _handle_script_log_event(self, message: dict) -> None:
        self._log(str(message.get("level", "INFO")), str(message.get("message", "")))

    def _handle_logic_trace_event(self, message: dict) -> None:
        if message.get("type") == "logic_trace":
            self.logic_workspace.apply_runtime_trace(dict(message))
        else:
            self.logic_workspace.clear_runtime_trace()



    def _handle_attach_script_event(self, message: dict) -> None:
        self._attach_script(str(message.get("name", "")), Path(str(message.get("path", ""))))

    def _handle_stats_event(self, message: dict) -> None:
        command_stats = self._commands.stats()
        self.profiler_label.setText(
            f"FPS: {message.get('fps', 0):.0f}\n"
            f"Objetos: {message.get('objects', 0)}\n"
            f"Modo: {message.get('mode', 'EDIT')} / {message.get('view', 'SCENE')}\n"
            f"Câmera: {message.get('camera', 'Editor')}\n"
            f"Jogador: {message.get('player') or '—'}\n"
            f"Zoom: {message.get('zoom', 1.0):.2f}\n"
            f"Spawn: {message.get('spawned', 0)} • Reuso: {message.get('reused', 0)} • "
            f"Pool: {message.get('pooled', 0)} • "
            f"Removidos: {message.get('destroyed', 0)}\n"
            f"IPC: {command_stats['sent']} enviados • {command_stats['coalesced']} unidos"
        )

    def _read_viewport_events(self) -> None:
        while True:
            try:
                message = self._events.get_nowait()
            except Exception:
                return
            self._viewport_events.dispatch(message)

    def closeEvent(self, event) -> None:
        self._viewport_controller.shutdown()
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
