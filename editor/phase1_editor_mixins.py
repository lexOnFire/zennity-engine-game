"""Mixins de construção de UI e manipulação de cena/hierarquia para o Phase 1 Editor."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QActionGroup, QKeySequence
from PySide6.QtWidgets import (
    QComboBox,
    QDockWidget,
    QFileDialog,
    QMessageBox,
    QSplitter,
    QTabWidget,
    QToolBar,
    QToolButton,
    QWidget,
)

from editor.premium_editor import (
    AssetPreviewPanel,
    ConsolePanel,
    CreatePanel,
    PrefabsPanel,
    ResourcesPanel,
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
from editor.runtime.tool_manager import EditorTool
from editor.services.workspace_registry import WorkspaceRegistry
from editor.widgets.game_viewport import GameViewportWidget
from editor.widgets.phase1_viewport import Phase1ViewportWidget
from editor.widgets.render_pipeline_profiler import RenderPipelineProfilerPanel
from engine.game_object import GameObject
from engine.physics.collider import BoxCollider
from engine.physics.rigidbody import RigidBody
from engine.scene import load_scene, save_scene


class Phase1EditorUIBuilderMixin:
    """Isola a construção da interface gráfica (menus, barras e painéis)."""

    def _build_menu(self) -> None:
        bar = self.menuBar()
        self._workspace_registry = WorkspaceRegistry(self)
        file_menu = bar.addMenu("Arquivo")
        edit_menu = bar.addMenu("Editar")
        window_menu = bar.addMenu("Janela")
        create_menu = bar.addMenu("Criar")
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

        animator_action = QAction("Animator", self)
        animator_action.triggered.connect(lambda checked=False: self._workspace_registry.open("animation"))
        window_menu.addAction(animator_action)

        logic_action = QAction("Editor de Lógica Visual", self)
        logic_action.triggered.connect(lambda checked=False: self._workspace_registry.open("logic"))
        window_menu.addAction(logic_action)

        self._unused_menu_refs = (edit_menu, window_menu, help_menu)

    def _show_animation_workspace(self) -> None:
        self._workspace_registry.open("animation")

    def _show_visual_tool_dock(self, module_path: str, class_name: str, attr_name: str) -> None:
        """Instancia e exibe a dock do editor visual dinamicamente ao ser clicada no menu."""
        self._workspace_registry.open_dynamic(module_path, class_name, attr_name)

    def _build_toolbar(self) -> None:
        toolbar = QToolBar("MainToolBar")
        toolbar.setObjectName("CommandBar")
        toolbar.setMovable(False)
        toolbar.setFloatable(False)
        toolbar.setAllowedAreas(Qt.TopToolBarArea)
        toolbar.setStyleSheet("QToolBar::handle { width: 0px; image: none; }")
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
        self.addAction(self.act_undo)
        toolbar.addAction(self.act_undo)

        self.act_redo = QAction("Redo", self)
        self.act_redo.setShortcut("Ctrl+Y")
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

        for label, tool, shortcut in (
            ("Select", EditorTool.SELECT, "Q"),
            ("Move", EditorTool.MOVE, "W"),
            ("Rotate", EditorTool.ROTATE, "E"),
            ("Scale", EditorTool.SCALE, "R"),
        ):
            action = QAction(label, self, checkable=True)
            action.setShortcut(QKeySequence(shortcut))
            action.setShortcutContext(Qt.ApplicationShortcut)
            action.setChecked(tool == self.editor_context.tools.active_tool)
            action.triggered.connect(
                lambda checked=False, next_tool=tool: self.editor_context.tools.set_active_tool(next_tool)
            )
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
        self.resources = ResourcesPanel(initial_refresh=False)
        self.create_panel = CreatePanel()
        self.prefabs = PrefabsPanel(initial_refresh=False)
        self.inspector = RealInspectorPanel()
        self.inspector.set_command_manager(self.editor_context.commands)
        if hasattr(self.inspector, "name"):
            self.inspector.name.setVisible(False)
        self.inspector.setMinimumWidth(300)
        self.inspector.setMaximumWidth(360)
        self.console = ConsolePanel()
        self.preview = AssetPreviewPanel()
        self.profiler = RenderPipelineProfilerPanel()

        self.viewport = Phase1ViewportWidget(self)
        self.viewport.setObjectName("ViewportCanvas")
        self.viewport.set_view_mode("scene")
        self.viewport.set_viewmodel(self.scene_view_model)
        self.viewport.set_tool_manager(self.editor_context.tools)
        self.viewport.set_editor_state(self.editor_context.state)
        self.viewport.set_command_manager(self.editor_context.commands)
        self.viewport.set_runtime_manager(self.editor_context.runtime)
        self.editor_scene = self.viewport.active_scene

        self.game_viewport = GameViewportWidget(self)
        self.game_viewport.setObjectName("GameViewportCanvas")
        self.game_viewport.set_view_mode("game")
        self.game_viewport.set_viewmodel(self.scene_view_model)
        self.game_viewport.set_tool_manager(self.editor_context.tools)
        self.game_viewport.set_editor_state(self.editor_context.state)
        self.game_viewport.set_command_manager(self.editor_context.commands)
        self.game_viewport.set_runtime_manager(self.editor_context.runtime)
        self.game_viewport.active_scene = self.editor_scene
        self.profiler.set_viewports(self.viewport, self.game_viewport)

        self.hierarchy_tabs = QTabWidget()
        self.hierarchy_tabs.addTab(self.hierarchy, "Hierarchy")
        self.hierarchy_tabs.addTab(self.create_panel, "Criar")
        self.hierarchy_tabs.setMinimumHeight(90)
        self.hierarchy_tabs.currentChanged.connect(lambda index: self.focus_hierarchy_panel())

        self.asset_tabs = QTabWidget()
        self.asset_tabs.addTab(self.resources, "Assets")
        self.asset_tabs.addTab(self.prefabs, "Adicionar Prefabs")
        self.asset_tabs.setMinimumHeight(90)
        self.asset_tabs.currentChanged.connect(lambda index: self.focus_assets_panel())

        left = QSplitter(Qt.Vertical)
        left.setChildrenCollapsible(False)
        left.addWidget(self.hierarchy_tabs)
        left.addWidget(self.asset_tabs)
        left.setSizes([180, 560])
        left.setMinimumWidth(240)
        left.setMaximumWidth(320)
        left.splitterMoved.connect(self._on_hierarchy_splitter_moved)
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
        self.focus_hierarchy_panel()

    def _on_hierarchy_splitter_moved(self, pos: int, index: int) -> None:
        self._hierarchy_splitter_user_resized = True

    def _sync_hierarchy_panel_height(self, object_count: int) -> None:
        if not hasattr(self, "left_splitter"):
            return
        if self._left_panel_focus == "assets":
            self.left_splitter.setSizes([96, 644])
            return
        target = max(150, min(390, 108 + int(object_count) * 24))
        sizes = self.left_splitter.sizes()
        total = sum(sizes) if sizes else 740
        bottom = max(96, total - target)
        self.left_splitter.setSizes([target, bottom])

    def focus_hierarchy_panel(self) -> None:
        self._left_panel_focus = "hierarchy"
        self._hierarchy_splitter_user_resized = False
        self._sync_hierarchy_panel_height(getattr(self, "object_count", 0))

    def focus_assets_panel(self) -> None:
        self._left_panel_focus = "assets"
        if hasattr(self, "left_splitter"):
            self.left_splitter.setSizes([96, 644])
        if not hasattr(self, "asset_tabs"):
            return
        current = self.asset_tabs.currentWidget()
        if current is getattr(self, "resources", None) and hasattr(self.resources, "ensure_assets_loaded"):
            self.resources.ensure_assets_loaded()
        elif current is getattr(self, "prefabs", None) and hasattr(self.prefabs, "ensure_prefabs_loaded"):
            self.prefabs.ensure_prefabs_loaded()


from editor.phase1_editor_scene_ops import Phase1SceneOperationsMixin


class Phase1HierarchyOperationsMixin:
    """Isola as operações sobre os objetos da hierarquia (reparent, clone, delete)."""

    def _after_hierarchy_command(self, selected: Any = None) -> None:
        if hasattr(self.viewport, "_sync_model_from_scene"):
            self.viewport._sync_model_from_scene()
        self.refresh_hierarchy_from_viewport()
        self.select_object(selected)
        self.on_viewport_object_changed(selected)
        self.viewport.update()
        self.game_viewport.update()
        self._update_undo_redo_states()
        if hasattr(self, "_scene_autosave"):
            self._scene_autosave.schedule()

    def reparent_object(self, obj: Any, parent: Any = None, index: Any = None) -> bool:
        scene = self._editor_scene()
        if scene is None or obj is None:
            return False
        if not can_reparent(obj, parent):
            if hasattr(self, "status_msg"):
                self.status_msg.setText("Reparent invalido: ciclo de hierarquia bloqueado.")
            return False
        command = ReparentGameObjectCommand(scene, obj, parent, index)

        def do() -> None:
            command.execute()
            self._after_hierarchy_command(obj)

        def undo_fn() -> None:
            command.undo()
            self._after_hierarchy_command(obj)

        self.editor_context.commands.execute(FunctionCommand(command.description, do, undo_fn))
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

        def undo_fn() -> None:
            command.undo()
            self._after_hierarchy_command(source)

        self.editor_context.commands.execute(FunctionCommand(command.description, do, undo_fn))
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

        def undo_fn() -> None:
            command.undo()
            self._after_hierarchy_command(target)

        self.editor_context.commands.execute(FunctionCommand(command.description, do, undo_fn))
        return True

    def rename_object(self, obj: Any, new_name: str) -> bool:
        if obj is None or not str(new_name).strip():
            self.refresh_hierarchy_from_viewport()
            return False
        command = RenameGameObjectCommand(obj, str(new_name))

        def do() -> None:
            command.execute()
            self._after_hierarchy_command(obj)

        def undo_fn() -> None:
            command.undo()
            self._after_hierarchy_command(obj)

        self.editor_context.commands.execute(FunctionCommand(command.description, do, undo_fn))
        return True

    def group_objects(self, objs: list[Any]) -> Any:
        scene = self._editor_scene()
        if scene is None or not objs:
            return None

        # Cria objeto Grupo Vazio
        from engine.game_object import GameObject
        group = GameObject("New Group")
        group.is_group = True

        # Calcula centro para o Transform do Grupo
        positions = [getattr(o, "transform", None) for o in objs if getattr(o, "transform", None)]
        if positions:
            avg_x = sum(float(t.x) for t in positions) / len(positions)
            avg_y = sum(float(t.y) for t in positions) / len(positions)
            group.transform.x = avg_x
            group.transform.y = avg_y

        def do() -> None:
            if hasattr(scene, "add_game_object"):
                scene.add_game_object(group)
            elif hasattr(scene, "game_objects"):
                scene.game_objects.append(group)
            for o in objs:
                ReparentGameObjectCommand(scene, o, group).execute()
            self._after_hierarchy_command(group)

        def undo_fn() -> None:
            for o in objs:
                o.parent = None
            if hasattr(scene, "remove_game_object"):
                scene.remove_game_object(group)
            elif hasattr(scene, "game_objects") and group in scene.game_objects:
                scene.game_objects.remove(group)
            self._after_hierarchy_command(objs[0] if objs else None)

        self.editor_context.commands.execute(FunctionCommand("Group Selection", do, undo_fn))
        return group

    def ungroup_object(self, group: Any) -> bool:
        scene = self._editor_scene()
        if scene is None or group is None or not getattr(group, "is_group", False):
            return False

        children = list(getattr(group, "children", []))

        def do() -> None:
            for child in children:
                child.parent = None
            if hasattr(scene, "remove_game_object"):
                scene.remove_game_object(group)
            elif hasattr(scene, "game_objects") and group in scene.game_objects:
                scene.game_objects.remove(group)
            self._after_hierarchy_command(children[0] if children else None)

        def undo_fn() -> None:
            if hasattr(scene, "add_game_object"):
                scene.add_game_object(group)
            elif hasattr(scene, "game_objects"):
                scene.game_objects.append(group)
            for child in children:
                child.parent = group
            self._after_hierarchy_command(group)

        self.editor_context.commands.execute(FunctionCommand("Ungroup", do, undo_fn))
        return True

