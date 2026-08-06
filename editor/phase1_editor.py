import warnings
from pathlib import Path
from typing import Any

warnings.warn(
    "editor.phase1_editor está deprecado (legado embutido). O entrypoint oficial é editor.phase1_main.",
    DeprecationWarning,
    stacklevel=2,
)


from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction, QActionGroup, QKeySequence, QShortcut
from PySide6.QtWidgets import QFileDialog, QComboBox, QSplitter, QTabWidget, QToolBar, QToolButton, QWidget, QMessageBox

from engine.game_object import GameObject
from engine.physics.collider import BoxCollider
from engine.physics.rigidbody import RigidBody
from editor.runtime.editor_extensions import EditorExtensionManager, default_editor_extensions
from editor.runtime.editor_context import EditorContext
from editor.runtime.tool_manager import EditorTool
from editor.runtime.tool_selection import sync_tool_selection
from editor.phase1_editor_mixins import (
    Phase1EditorUIBuilderMixin,
    Phase1SceneOperationsMixin,
    Phase1HierarchyOperationsMixin,
)
from editor.premium_editor import (
    AssetPreviewPanel,
    ConsolePanel,
    CreatePanel,
    PrefabsPanel,
    ResourcesPanel,
    ZennityPremiumEditor,
)


class ZennityPhase1Editor(
    Phase1EditorUIBuilderMixin,
    Phase1SceneOperationsMixin,
    Phase1HierarchyOperationsMixin,
    ZennityPremiumEditor,
):
    """Editor Premium com Fase 1 ativada."""

    def __init__(self) -> None:
        self.editor_context = EditorContext()
        self._tool_actions: dict[EditorTool, QAction] = {}
        self._snap_action: QAction | None = None
        self.current_scene_path: Path | None = None
        self.editor_scene: Any | None = None
        self._left_panel_focus = "hierarchy"
        # Quando True, o usuario ajustou o splitter manualmente:
        # nao recalcular automaticamente.
        self._hierarchy_splitter_user_resized = False
        self._extensions = EditorExtensionManager(self, self._on_extension_error)
        super().__init__()
        self._ensure_default_scene()
        self.editor_context.tools.subscribe(self._on_runtime_tool_changed)

    def _ensure_default_scene(self) -> None:
        if self.scene_model.get_root_objects():
            return

        platform = GameObject("Platform", tag="Ground")
        platform.mesh_type = "rect"
        platform.transform.position = [0.0, 160.0, 0.0]
        platform.transform.scale = [320.0, 24.0, 1.0]

        platform_collider = platform.add_component(
            BoxCollider(width=320, height=24)
        )
        platform_body = platform.add_component(RigidBody())
        platform_body.is_kinematic = True

        player = GameObject("Player", tag="Player")
        player.mesh_type = "rect"
        player.transform.position = [0.0, 40.0, 0.0]
        player.transform.scale = [36.0, 48.0, 1.0]
        player.add_component(BoxCollider(width=36, height=48))
        player.add_component(
            RigidBody(
                mass=1.0,
                gravity_scale=1.0,
            )
        )

        self.scene_model.add_object(platform)
        self.scene_model.add_object(player)

        self.viewport._sync_scene_from_model()
        self.editor_scene = self.viewport.active_scene
        self.game_viewport.active_scene = self.editor_scene
        self.refresh_hierarchy_from_viewport()



    def closeEvent(self, event) -> None:
        self.editor_context.selection.unsubscribe(self.on_viewport_selection_changed)
        self._extensions.uninstall_all()
        resources_controller = getattr(getattr(self, "resources", None), "assets_controller", None)
        if resources_controller is not None:
            resources_controller.uninstall()
        for viewport_name in ("viewport", "game_viewport"):
            viewport = getattr(self, viewport_name, None)
            shutdown = getattr(viewport, "shutdown", None)
            if callable(shutdown):
                shutdown()
        super().closeEvent(event)

    def _connect(self) -> None:
        self.hierarchy.selected.connect(self.select_object)
        self.hierarchy.create_empty_requested.connect(
            lambda: self.create_object("Empty")
        )
        self.hierarchy.duplicate_requested.connect(self.duplicate_object)
        self.hierarchy.delete_requested.connect(self.delete_object)
        self.hierarchy.rename_requested.connect(self.rename_object)
        self.hierarchy.reparent_requested.connect(self.reparent_object)

        self.create_panel.create_requested.connect(self.create_object)

        self.resources.asset_selected.connect(self.preview.load_asset)
        self.prefabs.asset_selected.connect(self.preview.load_asset)

        self.scene_view_model.hierarchy_updated.connect(
            self.refresh_hierarchy_from_viewport
        )
        self.scene_view_model.property_changed.connect(
            self.on_viewmodel_property_changed
        )

        self.viewport.object_transform_changed.connect(
            self.on_viewport_object_changed
        )
        self.viewport.tool_message_requested.connect(
            self.on_tool_message_requested
        )
        self.viewport.history_changed.connect(
            self._update_undo_redo_states
        )

        self.act_undo.triggered.connect(self.undo)
        self.act_redo.triggered.connect(self.redo)

        self._alternate_redo_shortcut = QShortcut(
            QKeySequence("Ctrl+Shift+Z"),
            self,
        )
        self._alternate_redo_shortcut.setContext(
            Qt.ApplicationShortcut
        )
        self._alternate_redo_shortcut.activated.connect(self.redo)

        self.game_viewport.tool_message_requested.connect(
            self.on_tool_message_requested
        )

        # Este callback projeta a seleção para viewport, inspector e hierarchy.
        self.editor_context.selection.subscribe(
            self.on_context_selection_changed
        )

        # Sincronização inicial sem escrever novamente no SelectionManager.
        self.on_context_selection_changed(
            self.editor_context.selection.selected
        )

        self._sync_play_controls()
        self._update_undo_redo_states()
        self._install_editor_extensions()

    def _install_editor_extensions(self) -> None:
        for extension in default_editor_extensions():
            self._extensions.install(extension)

    def _on_extension_error(self, name: str, exc: Exception) -> None:
        if hasattr(self, "console"):
            self.console.add("WARN", f"Extensao '{name}' falhou: {exc}")

    def _update_undo_redo_states(self) -> None:
        if hasattr(self, "act_undo") and hasattr(self, "act_redo"):
            self.act_undo.setEnabled(self.editor_context.commands.can_undo)
            self.act_redo.setEnabled(self.editor_context.commands.can_redo)

    def undo(self) -> None:
        self.editor_context.commands.undo()
        self._refresh_after_undo_redo()

    def redo(self) -> None:
        self.editor_context.commands.redo()
        self._refresh_after_undo_redo()

    def _refresh_after_undo_redo(self) -> None:
        """Refresh minimo apos undo/redo: NAO recalcula tamanho do splitter."""
        sel = self.editor_context.selection.selected
        objects = self.scene_objects()
        # Atualiza lista da hierarquia sem mexer no splitter
        self.hierarchy.refresh_objects(objects)
        if hasattr(self, "stats"):
            self.stats.setText(f"FPS: 60 | Memoria: 512 MB | Objetos: {len(objects)}")
        if sel is not None and sel in objects:
            self.on_viewport_selection_changed(sel)
        elif objects:
            pass  # mantem selecao atual
        self._update_undo_redo_states()
        try:
            self.viewport.update()
        except Exception:
            pass

    def _on_runtime_tool_changed(self, tool: EditorTool) -> None:
        action = self._tool_actions.get(tool)
        if action is not None and not action.isChecked():
            action.setChecked(True)
        if hasattr(self, "status_msg"):
            self.status_msg.setText(f"Ferramenta ativa: {tool.value.title()}")
        if tool in (EditorTool.MOVE, EditorTool.ROTATE, EditorTool.SCALE):
            sync_tool_selection(self)

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
        return getattr(self.viewport, "active_scene", None)



    def refresh_hierarchy_from_viewport(self) -> None:
        """Atualiza hierarquia e ajusta tamanho do splitter.

        O resize automatico so acontece se o usuario ainda nao
        arrastou o splitter manualmente (_hierarchy_splitter_user_resized).
        """
        objects = self.scene_objects()
        self.object_count = len(objects)
        if self.editor_context.selection.selected not in objects:
            scene_selected = None
            if hasattr(self.viewport, "_selected_from_scene"):
                scene_selected = self.viewport._selected_from_scene()
            self.select_object(scene_selected if scene_selected in objects else None)
        self.hierarchy.refresh_objects(objects)
                # So auto-redimensiona se o splitter nunca foi ajustado pelo usuario
        if not getattr(self, "_hierarchy_splitter_user_resized", False):
            self._sync_hierarchy_panel_height(self.object_count)
        if hasattr(self, "stats"):
            self.stats.setText(f"FPS: 60 | Memoria: 512 MB | Objetos: {self.object_count}")

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
        # Reset do flag: ao focar explicitamente, retoma o auto-resize
        self._hierarchy_splitter_user_resized = False
        self._sync_hierarchy_panel_height(getattr(self, "object_count", 0))

    def focus_assets_panel(self) -> None:
        self._left_panel_focus = "assets"
        if hasattr(self, "left_splitter"):
            self.left_splitter.setSizes([96, 644])

    def select_object(self, obj: Any) -> None:
        self.editor_context.selection.set_selected(obj)

    def _after_hierarchy_command(self, selected: Any = None) -> None:
        if hasattr(self.viewport, "_sync_model_from_scene"):
            self.viewport._sync_model_from_scene()
        self.refresh_hierarchy_from_viewport()
        self.select_object(selected)
        self.on_viewport_object_changed(selected)
        self.viewport.update()
        self.game_viewport.update()
        self._update_undo_redo_states()



    def on_viewport_selection_changed(self, obj: Any) -> None:
        self.editor_context.selection.set_selected(obj)

    def on_context_selection_changed(self, obj: Any) -> None:
        if self.viewport.selected_object() is not obj:
            self.viewport.select_object(obj)
        self.inspector.load_object(obj)
        self.hierarchy.select_object(obj)
        self._sync_scene_selection_index(obj)
        QTimer.singleShot(0, self._resync_selection_projection)

    def _resync_selection_projection(self) -> None:
        """Consolida a seleção após os timers legados das viewports."""
        self._sync_scene_selection_index(self.editor_context.selection.selected)

    def on_viewport_object_changed(self, obj: Any) -> None:
        if obj is self.editor_context.selection.selected:
            # Otimização: atualiza apenas o transform em vez de recarregar tudo
            if hasattr(self.inspector, 'update_transform_fields'):
                self.inspector.update_transform_fields(obj)
            else:
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
        return self.editor_context.runtime.is_playing

    def _sync_play_controls(self) -> None:
        playing = self._is_scene_playing()
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
        if hasattr(self, "save_scene"):
            self.save_scene()
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
        # Criar objeto e uma acao explicita: reseta o flag de resize manual
        self._hierarchy_splitter_user_resized = False
        self.refresh_hierarchy_from_viewport()
        if created is not None:
            self.select_object(created)
            self.focus_hierarchy_panel()
        self.console.add("INFO", f"Objeto criado: {name}")

    def create_prefab_from_selected(self) -> None:
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
            self.focus_hierarchy_panel()
            self.console.add("INFO", f"Prefab instanciado: {obj.name} a partir de {Path(file_path).name}")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao instanciar prefab: {str(e)}")
