from __future__ import annotations

from pathlib import Path
from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QActionGroup
from PySide6.QtWidgets import QFileDialog, QComboBox, QSplitter, QTabWidget, QToolBar, QToolButton, QWidget, QMessageBox

from editor.premium_editor import (
    AssetPreviewPanel,
    ConsolePanel,
    CreatePanel,
    PrefabsPanel,
    ResourcesPanel,
    ZennityPremiumEditor,
    SimplePanel,
)
from editor.premium_panels import RealHierarchyPanel, RealInspectorPanel
from editor.runtime.command_manager import FunctionCommand
from editor.runtime.hierarchy_commands import (
    DeleteGameObjectCommand,
    DuplicateGameObjectCommand,
    RenameGameObjectCommand,
    ReparentGameObjectCommand,
    can_reparent,
)
from editor.runtime.editor_context import EditorContext
from editor.runtime.tool_manager import EditorTool
from editor.widgets.phase1_viewport import Phase1ViewportWidget
from engine.scene import load_scene, save_scene


class ZennityPhase1Editor(ZennityPremiumEditor):
    """Editor Premium com Fase 1 ativada."""

    def __init__(self) -> None:
        self.editor_context = EditorContext()
        self._tool_actions: dict[EditorTool, QAction] = {}
        self._snap_action: QAction | None = None
        self.current_scene_path: Path | None = None
        self.editor_scene: Any | None = None
        super().__init__()
        self.editor_context.tools.subscribe(self._on_runtime_tool_changed)

    def _build_menu(self) -> None:
        bar = self.menuBar()
        file_menu = bar.addMenu("Arquivo")
        edit_menu = bar.addMenu("Editar")
        window_menu = bar.addMenu("Janela")
        create_menu = bar.addMenu("Criar")
        tools_menu = bar.addMenu("Ferramentas")
        build_menu = bar.addMenu("Build + Executar")
        help_menu = bar.addMenu("Ajuda")

        self.act_new_scene = QAction("New Scene", self)
        self.act_new_scene.setShortcut("Ctrl+N")
        self.act_new_scene.triggered.connect(self.new_scene)

        self.act_open_scene = QAction("Open Scene", self)
        self.act_open_scene.setShortcut("Ctrl+O")
        self.act_open_scene.triggered.connect(self.open_scene)

        self.act_save_scene = QAction("Save Scene", self)
        self.act_save_scene.setShortcut("Ctrl+S")
        self.act_save_scene.triggered.connect(self.save_scene)

        self.act_save_scene_as = QAction("Save Scene As", self)
        self.act_save_scene_as.setShortcut("Ctrl+Shift+S")
        self.act_save_scene_as.triggered.connect(self.save_scene_as)

        for action in (
            self.act_new_scene,
            self.act_open_scene,
            self.act_save_scene,
            self.act_save_scene_as,
        ):
            file_menu.addAction(action)
            self.addAction(action)

        for item in ["Player", "Plataforma", "Inimigo", "Sprite 2D", "Camera 2D"]:
            create_menu.addAction(item, lambda checked=False, value=item: self.create_object(value))
        build_menu.addAction("Play", self.play)
        build_menu.addAction("Stop", self.stop)

        prefab_menu = bar.addMenu("Prefabs")
        self.act_create_prefab = QAction("Create Prefab From Selected", self)
        self.act_create_prefab.triggered.connect(self.create_prefab_from_selected)
        prefab_menu.addAction(self.act_create_prefab)

        self.act_instantiate_prefab = QAction("Instantiate Prefab", self)
        self.act_instantiate_prefab.triggered.connect(self.instantiate_prefab_ui)
        prefab_menu.addAction(self.act_instantiate_prefab)

        self._unused_menu_refs = (edit_menu, window_menu, tools_menu, help_menu)

    def _build_toolbar(self) -> None:
        toolbar = QToolBar("MainToolBar")
        toolbar.setObjectName("CommandBar")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        open_button = QToolButton()
        open_button.setText("Open")
        open_button.clicked.connect(self.open_scene)
        toolbar.addWidget(open_button)

        save_button = QToolButton()
        save_button.setText("Save")
        save_button.clicked.connect(self.save_scene)
        toolbar.addWidget(save_button)

        toolbar.addSeparator()

        create_prefab_btn = QToolButton()
        create_prefab_btn.setText("Create Prefab")
        create_prefab_btn.setToolTip("Create Prefab From Selected")
        create_prefab_btn.clicked.connect(self.create_prefab_from_selected)
        toolbar.addWidget(create_prefab_btn)

        instantiate_prefab_btn = QToolButton()
        instantiate_prefab_btn.setText("Instantiate Prefab")
        instantiate_prefab_btn.setToolTip("Instantiate Prefab")
        instantiate_prefab_btn.clicked.connect(self.instantiate_prefab_ui)
        toolbar.addWidget(instantiate_prefab_btn)

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
        self.prefabs = PrefabsPanel()
        self.inspector = RealInspectorPanel()
        self.inspector.set_command_manager(self.editor_context.commands)
        if hasattr(self.inspector, "name"):
            self.inspector.name.setVisible(False)
        self.inspector.setMinimumWidth(300)
        self.inspector.setMaximumWidth(360)
        self.console = ConsolePanel()
        self.preview = AssetPreviewPanel()
        self.profiler = SimplePanel("Profiler", "FPS, CPU, memoria")

        self.viewport = Phase1ViewportWidget(self)
        self.viewport.setObjectName("ViewportCanvas")
        self.viewport.set_view_mode("scene")
        self.viewport.set_viewmodel(self.scene_view_model)
        self.viewport.set_tool_manager(self.editor_context.tools)
        self.viewport.set_editor_state(self.editor_context.state)
        self.viewport.set_command_manager(self.editor_context.commands)
        self.viewport.set_runtime_manager(self.editor_context.runtime)
        self.editor_scene = self.viewport.active_scene

        self.game_viewport = Phase1ViewportWidget(self)
        self.game_viewport.setObjectName("GameViewportCanvas")
        self.game_viewport.set_view_mode("game")
        self.game_viewport.set_viewmodel(self.scene_view_model)
        self.game_viewport.set_tool_manager(self.editor_context.tools)
        self.game_viewport.set_editor_state(self.editor_context.state)
        self.game_viewport.set_command_manager(self.editor_context.commands)
        self.game_viewport.set_runtime_manager(self.editor_context.runtime)
        self.game_viewport.active_scene = self.editor_scene

        self.hierarchy_tabs = QTabWidget()
        self.hierarchy_tabs.addTab(self.hierarchy, "Hierarchy")
        self.hierarchy_tabs.addTab(self.create_panel, "Criar")
        self.hierarchy_tabs.setMinimumHeight(120)

        asset_tabs = QTabWidget()
        asset_tabs.addTab(self.resources, "Assets")
        asset_tabs.addTab(self.prefabs, "Adicionar Prefabs")

        left = QSplitter(Qt.Vertical)
        left.setChildrenCollapsible(False)
        left.addWidget(self.hierarchy_tabs)
        left.addWidget(asset_tabs)
        left.setSizes([150, 590])
        left.setMinimumWidth(240)
        left.setMaximumWidth(320)
        self.left_splitter = left

        self.viewport_tabs = QTabWidget()
        self.viewport_tabs.setObjectName("SceneGameTabs")
        self.viewport_tabs.addTab(self.viewport, "Scene")
        self.viewport_tabs.addTab(self.game_viewport, "Game")

        center = QSplitter(Qt.Vertical)
        center.setChildrenCollapsible(False)
        center.addWidget(self.viewport_tabs)
        console_row = QSplitter(Qt.Horizontal)
        console_row.setChildrenCollapsible(False)
        console_row.addWidget(self.console)
        console_row.addWidget(self.profiler)
        console_row.setSizes([640, 220])
        center.addWidget(console_row)
        center.addWidget(self.preview)
        center.setSizes([560, 150, 170])

        main = QSplitter(Qt.Horizontal)
        main.setChildrenCollapsible(False)
        main.addWidget(left)
        main.addWidget(center)
        main.addWidget(self.inspector)
        main.setStretchFactor(0, 0)
        main.setStretchFactor(1, 1)
        main.setStretchFactor(2, 0)
        main.setSizes([260, 850, 320])
        self.main_splitter = main
        self.setCentralWidget(main)

        self.refresh_hierarchy_from_viewport()

    def _connect(self) -> None:
        self.hierarchy.selected.connect(self.select_object)
        self.hierarchy.create_empty_requested.connect(lambda: self.create_object("Empty"))
        self.hierarchy.duplicate_requested.connect(self.duplicate_object)
        self.hierarchy.delete_requested.connect(self.delete_object)
        self.hierarchy.rename_requested.connect(self.rename_object)
        self.hierarchy.reparent_requested.connect(self.reparent_object)
        self.create_panel.create_requested.connect(self.create_object)
        self.resources.asset_selected.connect(self.preview.load_asset)
        self.prefabs.asset_selected.connect(self.preview.load_asset)
        self.scene_view_model.selection_changed.connect(self.on_viewport_selection_changed)
        self.scene_view_model.hierarchy_updated.connect(self.refresh_hierarchy_from_viewport)
        self.scene_view_model.property_changed.connect(self.on_viewmodel_property_changed)
        self.viewport.object_transform_changed.connect(self.on_viewport_object_changed)
        self.viewport.tool_message_requested.connect(self.on_tool_message_requested)
        self.viewport.history_changed.connect(self._update_undo_redo_states)
        self.game_viewport.tool_message_requested.connect(self.on_tool_message_requested)
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
        self._ensure_scene_collider_registry(scene)
        return list(getattr(scene, "editable_objects", []))

    def _ensure_scene_collider_registry(self, scene: Any) -> None:
        try:
            from engine.physics.collider import BoxCollider, CircleCollider
        except Exception:
            return
        for obj in getattr(scene, "game_objects", []):
            for collider_type in (BoxCollider, CircleCollider):
                for collider in obj.get_components(collider_type):
                    registry = getattr(collider_type, "_registry", None)
                    if isinstance(registry, list) and collider not in registry:
                        registry.append(collider)

    def _active_scene(self) -> Any:
        return getattr(self.viewport, "active_scene", None)

    def _editor_scene(self) -> Any:
        if self.editor_scene is None:
            self.editor_scene = getattr(self.viewport, "active_scene", None)
        return self.editor_scene

    def _clear_scene_objects(self) -> None:
        scene = self._editor_scene()
        if scene is None:
            return

        for obj in list(getattr(scene, "editable_objects", [])):
            if hasattr(scene, "_remove_go"):
                scene._remove_go(obj)
            elif obj in getattr(scene, "game_objects", []):
                scene.game_objects.remove(obj)
                obj.scene = None

        scene.editable_objects.clear()
        if hasattr(scene, "selected_index"):
            scene.selected_index = -1

    def _sync_scene_after_load(self, selected: Any = None) -> None:
        if hasattr(self.viewport, "_sync_model_from_scene"):
            self.viewport._sync_model_from_scene()
        self._sync_scene_selection_index(selected)
        self.refresh_hierarchy_from_viewport()
        self.select_object(selected)
        self._update_undo_redo_states()

    def _apply_scene_data(self, scene_data: dict[str, Any]) -> None:
        scene = self._editor_scene()
        if scene is None:
            return

        self._clear_scene_objects()
        scene.name = str(scene_data.get("scene_name", "Untitled"))

        objects = list(scene_data.get("objects", []))
        for obj in objects:
            if hasattr(scene, "_add_go"):
                scene._add_go(obj)
            else:
                scene.game_objects.append(obj)
                obj.scene = scene
            scene.editable_objects.append(obj)

        selected = objects[0] if objects else None
        if hasattr(scene, "selected_index"):
            scene.selected_index = 0 if selected is not None else -1
        self._sync_scene_after_load(selected)

    def refresh_hierarchy_from_viewport(self) -> None:
        objects = self.scene_objects()
        self.object_count = len(objects)
        if self.editor_context.selection.selected not in objects:
            scene_selected = None
            if hasattr(self.viewport, "_selected_from_scene"):
                scene_selected = self.viewport._selected_from_scene()
            self.select_object(scene_selected if scene_selected in objects else None)
        self.hierarchy.refresh_objects(objects)
        self._sync_hierarchy_panel_height(self.object_count)
        if hasattr(self, "stats"):
            self.stats.setText(f"FPS: 60 | Memoria: 512 MB | Objetos: {self.object_count}")

    def _sync_hierarchy_panel_height(self, object_count: int) -> None:
        if not hasattr(self, "left_splitter"):
            return
        target = max(140, min(340, 108 + int(object_count) * 24))
        sizes = self.left_splitter.sizes()
        total = sum(sizes) if sizes else 740
        bottom = max(180, total - target)
        self.left_splitter.setSizes([target, bottom])

    def select_object(self, obj: Any) -> None:
        self.editor_context.selection.set_selected(obj)
        self._sync_scene_selection_index(obj)

    def _sync_scene_selection_index(self, obj: Any) -> None:
        scene = self._editor_scene()
        if scene is None or not hasattr(scene, "selected_index"):
            return
        objects = list(getattr(scene, "editable_objects", []))
        scene.selected_index = objects.index(obj) if obj in objects else -1

    def _after_hierarchy_command(self, selected: Any = None) -> None:
        if hasattr(self.viewport, "_sync_model_from_scene"):
            self.viewport._sync_model_from_scene()
        self.refresh_hierarchy_from_viewport()
        self.select_object(selected)
        self.on_viewport_object_changed(selected)
        self.viewport.update()
        self.game_viewport.update()
        self._update_undo_redo_states()

    def reparent_object(self, obj: Any, parent: Any = None, index: Any = None) -> bool:
        scene = self._editor_scene()
        if scene is None or obj is None:
            return False
        if not can_reparent(obj, parent):
            if hasattr(self, "status_msg"):
                self.status_msg.setText("Reparent inválido: ciclo de hierarquia bloqueado.")
            return False
        command = ReparentGameObjectCommand(scene, obj, parent, index)

        def do() -> None:
            command.execute()
            self._after_hierarchy_command(obj)

        def undo() -> None:
            command.undo()
            self._after_hierarchy_command(obj)

        self.editor_context.commands.execute(FunctionCommand(command.description, do, undo))
        return True

    def duplicate_object(self, obj: Any = None) -> Any:
        scene = self._editor_scene()
        source = obj or self.editor_context.selection.selected
        if scene is None or source is None:
            return None
        command = DuplicateGameObjectCommand(scene, source)

        def do() -> None:
            command.execute()
            self._after_hierarchy_command(command.clone)

        def undo() -> None:
            command.undo()
            self._after_hierarchy_command(source)

        self.editor_context.commands.execute(FunctionCommand(command.description, do, undo))
        return command.clone

    def delete_object(self, obj: Any = None) -> bool:
        scene = self._editor_scene()
        target = obj or self.editor_context.selection.selected
        if scene is None or target is None:
            return False
        command = DeleteGameObjectCommand(scene, target)

        def do() -> None:
            command.execute()
            self._after_hierarchy_command(None)

        def undo() -> None:
            command.undo()
            self._after_hierarchy_command(target)

        self.editor_context.commands.execute(FunctionCommand(command.description, do, undo))
        return True

    def rename_object(self, obj: Any, new_name: str) -> bool:
        if obj is None or not str(new_name).strip():
            self.refresh_hierarchy_from_viewport()
            return False
        command = RenameGameObjectCommand(obj, str(new_name))

        def do() -> None:
            command.execute()
            self._after_hierarchy_command(obj)

        def undo() -> None:
            command.undo()
            self._after_hierarchy_command(obj)

        self.editor_context.commands.execute(FunctionCommand(command.description, do, undo))
        return True

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

    def new_scene(self) -> None:
        if self.editor_context.runtime.is_playing:
            self.stop()
        self._clear_scene_objects()
        scene = self._editor_scene()
        if scene is not None:
            scene.name = "Untitled"
        self.current_scene_path = None
        self._sync_scene_after_load(None)
        self.status_msg.setText("Nova cena criada.")
        self.console.add("INFO", "Nova cena criada.")

    def open_scene(self) -> None:
        if self.editor_context.runtime.is_playing:
            self.stop()
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Open Scene",
            "",
            "Zennity Scene (*.zscene);;JSON (*.json);;All Files (*)",
        )
        if not file_name:
            return

        scene_data = load_scene(file_name)
        self.current_scene_path = Path(file_name)
        self._apply_scene_data(scene_data)
        self.status_msg.setText(f"Cena aberta: {self.current_scene_path.name}")
        self.console.add("INFO", f"Cena aberta: {self.current_scene_path}")

    def save_scene(self) -> None:
        if self.current_scene_path is None:
            self.save_scene_as()
            return

        scene = self._editor_scene()
        if scene is None:
            return

        save_scene(scene, self.current_scene_path)
        self.status_msg.setText(f"Cena salva: {self.current_scene_path.name}")
        self.console.add("INFO", f"Cena salva: {self.current_scene_path}")

    def save_scene_as(self) -> None:
        file_name, _ = QFileDialog.getSaveFileName(
            self,
            "Save Scene As",
            str(self.current_scene_path or Path("Untitled.zscene")),
            "Zennity Scene (*.zscene);;JSON (*.json);;All Files (*)",
        )
        if not file_name:
            return

        path = Path(file_name)
        if path.suffix.lower() != ".zscene":
            path = path.with_suffix(".zscene")
        self.current_scene_path = path
        self.save_scene()

    def _is_scene_playing(self) -> bool:
        return self.editor_context.runtime.is_playing

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
        editor_scene = self._editor_scene()
        if editor_scene is None:
            return
        editor_selected = self.editor_context.selection.selected
        runtime_scene = self.editor_context.runtime.start_play(editor_scene)
        runtime_selected = runtime_scene.runtime_for_editor(editor_selected)
        self.game_viewport.active_scene = runtime_scene
        self.game_viewport._apply_qt_shims()
        self.game_viewport.resizeGL(self.game_viewport.width(), self.game_viewport.height())
        self.game_viewport._sync_model_from_scene()
        if hasattr(self, "viewport_tabs"):
            self.viewport_tabs.setCurrentWidget(self.game_viewport)
        self.select_object(runtime_selected)
        self._sync_play_controls()
        self.status_msg.setText("Simulacao ativa.")
        self.console.add("INFO", "Play iniciado.")

    def stop(self) -> None:
        if not self._is_scene_playing():
            self._sync_play_controls()
            if hasattr(self, "status_msg"):
                self.status_msg.setText("Simulacao parada.")
            return
        runtime_scene = self.editor_context.runtime.runtime_scene
        runtime_selected = self.editor_context.selection.selected
        editor_selected = runtime_scene.editor_for_runtime(runtime_selected) if runtime_scene is not None else None
        self.editor_context.runtime.stop_play()
        self.viewport.active_scene = self._editor_scene()
        self.game_viewport.active_scene = self._editor_scene()
        self.viewport._apply_qt_shims()
        self.viewport.resizeGL(self.viewport.width(), self.viewport.height())
        self.game_viewport._apply_qt_shims()
        self.game_viewport.resizeGL(self.game_viewport.width(), self.game_viewport.height())
        if hasattr(self, "viewport_tabs"):
            self.viewport_tabs.setCurrentWidget(self.viewport)
        self.refresh_hierarchy_from_viewport()
        self.select_object(editor_selected)
        self._sync_play_controls()
        self.status_msg.setText("Simulacao parada.")
        self.console.add("INFO", "Play finalizado.")

    def create_object(self, name: str) -> None:
        mapping = {
            "Sprite 2D": "Quadrado",
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

    def create_prefab_from_selected(self) -> None:
        """Salva o objeto selecionado como um Prefab (.zprefab)."""
        selected = self.editor_context.selection.selected
        if selected is None:
            QMessageBox.warning(self, "Aviso", "Selecione um objeto na cena antes de criar um Prefab.")
            return

        default_name = f"{selected.name}.zprefab"
        assets_prefabs_dir = str(Path(self.editor_context.project_root) / "Assets" / "Prefabs")
        Path(assets_prefabs_dir).mkdir(parents=True, exist_ok=True)

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Create Prefab From Selected",
            str(Path(assets_prefabs_dir) / default_name),
            "Prefab Files (*.zprefab)"
        )

        if not file_path:
            return

        from engine.prefabs.prefab_loader import create_prefab_from_object
        try:
            prefab_uuid = create_prefab_from_object(selected, file_path)
            self.console.add("INFO", f"Prefab criado: {selected.name} -> {Path(file_path).name} (UUID: {prefab_uuid})")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao criar prefab: {str(e)}")

    def instantiate_prefab_ui(self) -> None:
        """Abre caixa de diálogo para escolher um prefab (.zprefab) e instanciá-lo na cena."""
        if self.editor_context.runtime.is_playing:
            self.stop()
        if not self.viewport or not self._editor_scene():
            return

        assets_prefabs_dir = str(Path(self.editor_context.project_root) / "Assets" / "Prefabs")

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Instantiate Prefab",
            assets_prefabs_dir,
            "Prefab Files (*.zprefab)"
        )

        if not file_path:
            return

        from engine.prefabs.prefab_loader import instantiate_prefab
        try:
            obj = instantiate_prefab(file_path)

            scene = self._editor_scene()
            lay = getattr(scene, "_layout", None)
            if lay is not None:
                layout_data = lay()
                center = scene._vp_to_world(
                    layout_data["vp_left"] + layout_data["vp_w"] / 2,
                    layout_data["vp_top"] + layout_data["vp_h"] / 2,
                    layout_data
                )
                obj.transform.position = center.copy()

            scene._add_go(obj)
            scene.editable_objects.append(obj)

            self.viewport.active_scene = scene
            self.viewport._sync_model_from_scene()
            self.select_object(obj)

            self.console.add("INFO", f"Prefab instanciado: {obj.name} a partir de {Path(file_path).name}")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao instanciar prefab: {str(e)}")
