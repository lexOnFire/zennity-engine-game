from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QActionGroup
from PySide6.QtWidgets import QComboBox, QSplitter, QToolBar, QToolButton, QWidget

from editor.premium_editor import (
    ConsolePanel,
    CreatePanel,
    ResourcesPanel,
    SimplePanel,
    ZennityPremiumEditor,
)
from editor.premium_panels import RealHierarchyPanel, RealInspectorPanel
from editor.runtime.editor_context import EditorContext
from editor.runtime.tool_manager import EditorTool
from editor.widgets.phase1_viewport import Phase1ViewportWidget


class ZennityPhase1Editor(ZennityPremiumEditor):
    """Editor Premium com Fase 1 ativada.

    Primeira entrega funcional:
    - Hierarchy usa objetos reais da Viewport.
    - Inspector mostra Transform real.
    - Criar objeto sincroniza Viewport, Hierarchy e Inspector.
    - Selecionar na Hierarchy seleciona o objeto real na cena.
    """

    def __init__(self) -> None:
        self.editor_context = EditorContext()
        self._tool_actions: dict[EditorTool, QAction] = {}
        self._snap_action: QAction | None = None
        super().__init__()
        self.editor_context.tools.subscribe(self._on_runtime_tool_changed)

    def _build_toolbar(self) -> None:
        toolbar = QToolBar("MainToolBar")
        toolbar.setObjectName("CommandBar")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        for text in ["Open", "Save"]:
            toolbar.addWidget(QToolButton(text=text))

        self.act_undo = QAction("Undo", self)
        self.act_undo.setShortcut("Ctrl+Z")
        self.act_undo.triggered.connect(self.undo)
        self.addAction(self.act_undo)
        toolbar.addAction(self.act_undo)

        self.act_redo = QAction("Redo", self)
        self.act_redo.setShortcut("Ctrl+Y")
        self.act_redo.triggered.connect(self.redo)
        self.addAction(self.act_redo)
        toolbar.addAction(self.act_redo)

        spacer = QWidget()
        spacer.setMinimumWidth(180)
        toolbar.addWidget(spacer)

        self._build_tool_buttons(toolbar)
        toolbar.addSeparator()
        self._build_snap_button(toolbar)

        self.btn_play = QToolButton()
        self.btn_play.setText("Play")
        self.btn_play.clicked.connect(self.play)
        toolbar.addWidget(self.btn_play)

        self.btn_stop = QToolButton()
        self.btn_stop.setText("Stop")
        self.btn_stop.clicked.connect(self.stop)
        self.btn_stop.setEnabled(False)
        toolbar.addWidget(self.btn_stop)
        toolbar.addWidget(QComboBox())

    def _build_tool_buttons(self, toolbar: QToolBar) -> None:
        group = QActionGroup(self)
        group.setExclusive(True)

        for label, tool in (
            ("Select", EditorTool.SELECT),
            ("Move", EditorTool.MOVE),
            ("Rotate", EditorTool.ROTATE),
            ("Scale", EditorTool.SCALE),
        ):
            action = QAction(label, self, checkable=True)
            action.setChecked(tool == self.editor_context.tools.active_tool)
            action.triggered.connect(lambda checked=False, next_tool=tool: self.editor_context.tools.set_active_tool(next_tool))
            group.addAction(action)
            toolbar.addAction(action)
            self._tool_actions[tool] = action

        self.tool_action_group = group

    def _build_snap_button(self, toolbar: QToolBar) -> None:
        action = QAction(self._snap_label(), self, checkable=True)
        action.setChecked(self.editor_context.state.snap_enabled)
        action.triggered.connect(lambda checked=False: self.set_snap_enabled(bool(checked)))
        toolbar.addAction(action)
        self._snap_action = action

    def _snap_label(self) -> str:
        state = "ON" if self.editor_context.state.snap_enabled else "OFF"
        return f"Snap: {state}"

    def set_snap_enabled(self, enabled: bool) -> None:
        self.editor_context.state.snap_enabled = enabled
        self._sync_snap_action()
        if hasattr(self, "status_msg"):
            self.status_msg.setText(f"Snap {'ativado' if enabled else 'desativado'}")

    def _sync_snap_action(self) -> None:
        if self._snap_action is None:
            return
        self._snap_action.setChecked(self.editor_context.state.snap_enabled)
        self._snap_action.setText(self._snap_label())

    def _build_layout(self) -> None:
        self.hierarchy = RealHierarchyPanel()
        self.resources = ResourcesPanel()
        self.create_panel = CreatePanel()
        self.inspector = RealInspectorPanel()
        self.console = ConsolePanel()
        self.preview = SimplePanel("Asset Preview", "Preview de assets")
        self.profiler = SimplePanel("Profiler", "FPS, CPU, memoria")

        self.viewport = Phase1ViewportWidget(self)
        self.viewport.setObjectName("ViewportCanvas")
        self.viewport.set_viewmodel(self.scene_view_model)
        self.viewport.set_tool_manager(self.editor_context.tools)
        self.viewport.set_editor_state(self.editor_context.state)
        self.viewport.set_command_manager(self.editor_context.commands)

        left = QSplitter(Qt.Vertical)
        left.addWidget(self.hierarchy)
        left.addWidget(self.resources)
        left.addWidget(self.create_panel)
        left.setSizes([320, 260, 220])

        center = QSplitter(Qt.Vertical)
        center.addWidget(self.viewport)
        bottom = QSplitter(Qt.Horizontal)
        bottom.addWidget(self.console)
        bottom.addWidget(self.preview)
        bottom.addWidget(self.profiler)
        bottom.setSizes([520, 260, 260])
        center.addWidget(bottom)
        center.setSizes([560, 240])

        main = QSplitter(Qt.Horizontal)
        main.addWidget(left)
        main.addWidget(center)
        main.addWidget(self.inspector)
        main.setSizes([260, 850, 300])
        self.setCentralWidget(main)

        self.refresh_hierarchy_from_viewport()

    def _connect(self) -> None:
        self.hierarchy.selected.connect(self.select_object)
        self.create_panel.create_requested.connect(self.create_object)
        self.scene_view_model.selection_changed.connect(self.on_viewport_selection_changed)
        self.scene_view_model.property_changed.connect(self.on_viewmodel_property_changed)
        self.viewport.object_transform_changed.connect(self.on_viewport_object_changed)
        self.viewport.tool_message_requested.connect(self.on_tool_message_requested)
        self.viewport.history_changed.connect(self._update_undo_redo_states)
        self.on_viewport_selection_changed(self.editor_context.selection.selected)
        self._sync_play_controls()
        self._update_undo_redo_states()

    def _update_undo_redo_states(self) -> None:
        if hasattr(self, "act_undo") and hasattr(self, "act_redo"):
            self.act_undo.setEnabled(self.editor_context.commands.can_undo)
            self.act_redo.setEnabled(self.editor_context.commands.can_redo)

    def undo(self) -> None:
        self.editor_context.commands.undo()
        self.refresh_hierarchy_from_viewport()
        sel = self.editor_context.selection.selected
        if sel is not None:
            self.on_viewport_selection_changed(sel)
        self._update_undo_redo_states()

    def redo(self) -> None:
        self.editor_context.commands.redo()
        self.refresh_hierarchy_from_viewport()
        sel = self.editor_context.selection.selected
        if sel is not None:
            self.on_viewport_selection_changed(sel)
        self._update_undo_redo_states()

    def _on_runtime_tool_changed(self, tool: EditorTool) -> None:
        action = self._tool_actions.get(tool)
        if action is not None and not action.isChecked():
            action.setChecked(True)
        if hasattr(self, "status_msg"):
            self.status_msg.setText(f"Ferramenta ativa: {tool.value.title()}")

    def scene_objects(self) -> list[Any]:
        scene = getattr(self.viewport, "active_scene", None)
        if scene is None:
            return []
        return list(getattr(scene, "editable_objects", []))

    def refresh_hierarchy_from_viewport(self) -> None:
        objects = self.scene_objects()
        self.object_count = len(objects)
        self.hierarchy.refresh_objects(objects)
        if hasattr(self, "stats"):
            self.stats.setText(f"FPS: 60 | Memoria: 512 MB | Objetos: {self.object_count}")

    def select_object(self, obj: Any) -> None:
        self.editor_context.selection.set_selected(obj)

    def on_viewport_selection_changed(self, obj: Any) -> None:
        self.inspector.load_object(obj)
        self.hierarchy.select_object(obj)

    def on_viewport_object_changed(self, obj: Any) -> None:
        if obj is self.editor_context.selection.selected:
            self.inspector.load_object(obj)

    def on_viewmodel_property_changed(self, component_name: str, property_name: str, value: object) -> None:
        if component_name == "Transform":
            self.on_viewport_object_changed(self.editor_context.selection.selected)

    def on_tool_message_requested(self, message: str) -> None:
        if hasattr(self, "status_msg"):
            self.status_msg.setText(message)
        if hasattr(self, "console"):
            self.console.add("INFO", message)

    def _is_scene_playing(self) -> bool:
        return bool(getattr(getattr(self.viewport, "active_scene", None), "playing", False))

    def _sync_play_controls(self) -> None:
        playing = self._is_scene_playing()
        self.editor_context.state.is_playing = playing
        if hasattr(self, "btn_play"):
            self.btn_play.setEnabled(not playing)
            self.btn_play.setText("Playing" if playing else "Play")
        if hasattr(self, "btn_stop"):
            self.btn_stop.setEnabled(playing)

    def play(self) -> None:
        if self._is_scene_playing():
            self._sync_play_controls()
            if hasattr(self, "status_msg"):
                self.status_msg.setText("Simulacao ja ativa.")
            return
        self.viewport._on_play_state_changed("play")
        self._sync_play_controls()
        self.status_msg.setText("Simulacao ativa.")
        self.console.add("INFO", "Play iniciado.")

    def stop(self) -> None:
        if not self._is_scene_playing():
            self._sync_play_controls()
            if hasattr(self, "status_msg"):
                self.status_msg.setText("Simulacao parada.")
            return
        self.viewport._on_play_state_changed("stop")
        self.refresh_hierarchy_from_viewport()
        self.viewport.sync_selection_from_scene()
        self._sync_play_controls()
        self.status_msg.setText("Simulacao parada.")
        self.console.add("INFO", "Play finalizado.")

    def create_object(self, name: str) -> None:
        mapping = {
            "Sprite 2D": "Quadrado",
            "Cube 3D": "Cube",
            "Plane 3D": "Plane",
            "Plataforma 2D": "Plataforma",
            "Top-down 2D": "Player",
        }
        value = mapping.get(name, name)
        self.viewport.create_object(value)

        objects = self.scene_objects()
        created = objects[-1] if objects else None
        self.refresh_hierarchy_from_viewport()
        if created is not None:
            self.select_object(created)

        self.console.add("INFO", f"Objeto criado: {name}")
