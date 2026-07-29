"""Composition root and UI wiring for the isolated editor."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from PySide6.QtCore import Qt

from editor.animation_workspace_controller import AnimationWorkspaceController
from editor.asset_browser_controller import AssetBrowserController
from editor.console_controller import ConsoleController
from editor.editor_command_controller import EditorCommandController
from editor.editor_session_controller import EditorSessionController
from editor.hierarchy_controller import HierarchyController
from editor.hierarchy_view_renderer import HierarchyViewRenderer
from editor.inspector_controller import InspectorComponentController, IsolatedInspectorController
from editor.inspector_view_renderer import InspectorViewRenderer
from editor.logic_workspace_controller import LogicWorkspaceController
from editor.prefab_workspace_controller import PrefabWorkspaceController
from editor.project_workflow_controller import ProjectWorkflowController
from editor.runtime.isolated_play_mode_controller import IsolatedPlayModeController
from editor.runtime.scene_history import SceneHistory
from editor.runtime.scene_selection_controller import SceneSelectionController
from editor.runtime.viewport_event_dispatcher import ViewportEventDispatcher
from editor.runtime.viewport_process_controller import ViewportProcessController
from editor.scene_history_controller import SceneHistoryController
from editor.scene_object_controller import SceneObjectController
from editor.scene_persistence import EditorScenePersistence
from editor.controllers.selection_controller import EditorSelectionController
from editor.controllers.tool_controller import ToolController
from editor.controllers.viewport_controller import ViewportController
from editor.viewport_event_controller import ViewportEventController


class EditorBootstrapController:
    """Build collaborators and connect the already-created Qt view."""

    def __init__(self, host: Any, project_root: Path) -> None:
        self.host = host
        self.project_root = Path(project_root)
        self._composed = False
        self._configured = False

    def compose(
        self,
        viewport_process: Any,
        commands: Any,
        events: Any,
        viewport_controller: ViewportProcessController | None = None,
    ) -> None:
        if self._composed:
            return
        h = self.host
        h._console_controller = ConsoleController(h)
        h._console_records = h._console_controller.records
        h._asset_browser = AssetBrowserController(h, self.project_root)
        h._scene_persistence = EditorScenePersistence(self.project_root)
        h._viewport_controller = viewport_controller or ViewportProcessController.from_queues(
            commands, events, viewport_process,
        )
        h._viewport_process = h._viewport_controller.process
        h._commands = h._viewport_controller.commands
        h._events = h._viewport_controller.events
        h._scene_controller = SceneSelectionController(h._commands)
        h._viewport_events = ViewportEventDispatcher(self._viewport_handlers())
        h._session_controller = EditorSessionController(h)
        h._hierarchy_view = HierarchyViewRenderer(h)
        h._hierarchy_controller = HierarchyController(h, h._hierarchy_view)
        h._scene_history = SceneHistory(max_commands=100, max_bytes=16 * 1024 * 1024)
        h._history_controller = SceneHistoryController(h)
        h._inspector_controller = IsolatedInspectorController(h)
        h._inspector_components = InspectorComponentController(h)
        h._inspector_view = InspectorViewRenderer(h)
        h._animation_workspace = AnimationWorkspaceController(h)
        h._logic_workspace_controller = LogicWorkspaceController(h)
        h._prefab_workspace = PrefabWorkspaceController(h)
        h._scene_objects = SceneObjectController(h)
        h._editor_commands = EditorCommandController(h)
        h._selection = EditorSelectionController(h)
        h._viewport_commands = ViewportController(h)
        h._tool_controller = ToolController(h)
        h._project_workflow = ProjectWorkflowController(h)
        h._viewport_event_controller = ViewportEventController(h)
        h._play_controller = IsolatedPlayModeController()
        h._play_session = h._play_controller.session
        self._composed = True

    def configure(self) -> None:
        if self._configured:
            return
        if not self._composed:
            raise RuntimeError("editor collaborators must be composed before configuration")
        h = self.host
        h.setWindowTitle("Zennity Engine Editor — Phase 1")
        h.statusBar().showMessage("Zennity Phase 1 pronto — Viewport em processo dedicado.")
        h._editor_commands.connect_toolbar_actions()
        h._editor_commands.configure_main_menus()
        h._tool_controller.configure()
        h._configure_create_menu()
        h._connect_create_panel()
        h._configure_edit_menu()
        h._asset_browser.refresh()
        h._prefab_workspace.refresh()
        h.prefab_tree.itemDoubleClicked.connect(h._prefab_workspace.instantiate_item)
        h.prefab_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        h.prefab_tree.customContextMenuRequested.connect(h._prefab_workspace.open_menu)
        h._console_controller.connect()
        h._asset_browser.connect()
        h._connect_hierarchy_to_viewport()
        h._refresh_hierarchy()
        h._connect_inspector_to_viewport()
        h._configure_animation_workspace()
        h._logic_workspace_controller.connect()
        h._clear_inspector_view()
        h.add_component_button.clicked.connect(h._open_add_component_menu)
        h.viewport_tabs.currentChanged.connect(h._change_view_mode)
        h._session_controller.configure()
        h._scene_controller.publish_snapshot(h._scene_snapshot)
        h._log("INFO", "Zennity Phase 1 iniciado com Viewport em processo separado")
        self._configured = True

    def _viewport_handlers(self) -> dict[str, Any]:
        h = self.host
        return {
            "selected": h._handle_selected_event,
            "transform_begin": h._handle_transform_event,
            "transform_end": h._handle_transform_event,
            "transform": h._handle_transform_event,
            "play_state": h._handle_play_state_event,
            "scene_snapshot": h._handle_scene_snapshot_event,
            "runtime_objects": h._handle_runtime_objects_event,
            "viewport_mode": h._handle_viewport_mode_event,
            "runtime_log": h._handle_runtime_log_event,
            "logic_trace": h._handle_logic_trace_event,
            "logic_trace_clear": h._handle_logic_trace_event,
            "animator_state": h._handle_animator_state_event,
            "animation_event": h._handle_animation_event,
            "stats": h._handle_stats_event,
        }
