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
        super().__init__()
        self.editor_context.tools.subscribe(self._on_runtime_tool_changed)

    def _build_toolbar(self) -> None:
        toolbar = QToolBar("MainToolBar")
        toolbar.setObjectName("CommandBar")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        for text in ["Open", "Save", "Undo", "Redo"]:
            toolbar.addWidget(QToolButton(text=text))

        spacer = QWidget()
        spacer.setMinimumWidth(180)
        toolbar.addWidget(spacer)

        self._build_tool_buttons(toolbar)

        self.btn_play = QToolButton()
        self.btn_play.setText("Play")
        self.btn_play.clicked.connect(self.play)
        toolbar.addWidget(self.btn_play)

        btn_stop = QToolButton()
        btn_stop.setText("Stop")
        btn_stop.clicked.connect(self.stop)
        toolbar.addWidget(btn_stop)
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
        self.viewport.object_transform_changed.connect(self.on_viewport_object_changed)
        self.viewport.tool_message_requested.connect(self.on_tool_message_requested)
        self.on_viewport_selection_changed(self.editor_context.selection.selected)

    def _on_runtime_tool_changed(self, tool: EditorTool) -> None:
        action = self._tool_actions.get(tool)
        if action is not None and not action.isChecked():
            action.setChecked(True)
        if hasattr(self, "status_msg"):
            if tool in (EditorTool.ROTATE, EditorTool.SCALE):
                self.status_msg.setText(f"{tool.value.title()} em desenvolvimento")
            else:
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

    def on_tool_message_requested(self, message: str) -> None:
        if hasattr(self, "status_msg"):
            self.status_msg.setText(message)
        if hasattr(self, "console"):
            self.console.add("INFO", message)

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
