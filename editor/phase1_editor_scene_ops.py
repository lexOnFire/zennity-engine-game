"""Mixin de operações de cena para ZennityPhase1Editor."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from PySide6.QtWidgets import QFileDialog

from engine.game_object import GameObject
from engine.physics.collider import BoxCollider
from engine.physics.rigidbody import RigidBody
from engine.scene import load_scene, save_scene


class Phase1SceneOperationsMixin:
    """Isola as operações de persistência e ciclo de vida de arquivos de cena."""

    def _ensure_default_scene(self) -> None:
        if self.scene_model.get_root_objects():
            return

        platform = GameObject("Platform", tag="Ground")
        platform.mesh_type = "rect"
        platform.transform.position = [0.0, 160.0, 0.0]
        platform.transform.scale = [320.0, 24.0, 1.0]

        platform.add_component(BoxCollider(width=320, height=24))
        platform_body = platform.add_component(RigidBody())
        platform_body.is_kinematic = True

        player = GameObject("Player", tag="Player")
        player.mesh_type = "rect"
        player.transform.position = [0.0, 40.0, 0.0]
        player.transform.scale = [36.0, 48.0, 1.0]
        player.add_component(BoxCollider(width=36, height=48))
        player.add_component(RigidBody(mass=1.0, gravity_scale=1.0))

        self.scene_model.add_object(platform)
        self.scene_model.add_object(player)

        self.viewport._sync_scene_from_model()
        self.editor_scene = self.viewport.active_scene
        self.game_viewport.active_scene = self.editor_scene
        self.refresh_hierarchy_from_viewport()

    def _clear_scene_objects(self) -> None:
        self.select_object(None)
        scene = self._editor_scene()
        if scene is None:
            return
        if hasattr(scene, "_remove_go"):
            for obj in list(getattr(scene, "editable_objects", [])):
                scene._remove_go(obj)
        else:
            scene.game_objects.clear()
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

    def _sync_scene_selection_index(self, obj: Any) -> None:
        scene = self._editor_scene()
        if scene is None or not hasattr(scene, "selected_index"):
            return
        objects = list(getattr(scene, "editable_objects", []))
        scene.selected_index = objects.index(obj) if obj in objects else -1

    def new_scene(self) -> None:
        if self.editor_context.runtime.is_playing:
            self.stop()
        self._clear_scene_objects()
        scene = self._editor_scene()
        if scene is not None:
            scene.name = "Untitled"
        self.current_scene_path = None
        self._hierarchy_splitter_user_resized = False
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
        path = Path(file_name)
        if path.suffix.lower() != ".zscene":
            path = path.with_suffix(".zscene")
        self.current_scene_path = path
        self._hierarchy_splitter_user_resized = False
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
        self.current_scene_path = Path(file_name)
        self.save_scene()
