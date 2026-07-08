from __future__ import annotations
import numpy as np

from engine.core import Scene
from engine.game_object import GameObject
from engine.graphics.camera2d import Camera2D


class Editor2DScene(Scene):
    def start(self) -> None:
        self.game_objects = []
        self.editable_objects = []
        self.selected_index = -1
        self.playing = False
        self.name = "Editor2DScene"
        self.show_grid = True
        self.grid_size = 32
        self.show_scale_handles = True

        self.cam_obj = GameObject("EditorCamera")
        self.camera = self.cam_obj.add_component(Camera2D(zoom=1.0))
        self.cam_obj.transform.position = np.array([400.0, 300.0, 0.0], dtype=np.float32)
        self._add_go(self.cam_obj)
        Camera2D.main = self.camera

    def _add_go(self, go: GameObject) -> None:
        go.scene = self
        if go not in self.game_objects:
            self.game_objects.append(go)

    def _remove_go(self, go: GameObject) -> None:
        if go in self.game_objects:
            self.game_objects.remove(go)
        if go in self.editable_objects:
            self.editable_objects.remove(go)
        go.scene = None

    def _draw_object(self, screen, obj) -> None:
        if hasattr(obj, "draw"):
            obj.draw(screen)

