from __future__ import annotations
import numpy as np

from engine.core import Scene
from engine.game_object import GameObject
from engine.graphics.camera2d import Camera2D
from engine.physics.rigidbody import RigidBody
from engine.physics.collider import BoxCollider
from engine.physics.rigidbody import RigidBody
from engine.physics.collider import BoxCollider


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
        self.spawn_default_scene()
        self.spawn_default_scene()


    def spawn_default_scene(self) -> None:
        floor = GameObject("Chao")
        floor.transform.position = np.array([400.0, 500.0, 0.0], dtype=np.float32)
        floor.transform.scale = np.array([600.0, 32.0, 1.0], dtype=np.float32)
        floor.add_component(BoxCollider(width=600, height=32))
        rb_floor = floor.add_component(RigidBody())
        rb_floor.is_kinematic = True
        floor.mesh_type = "Plataforma"
        self._add_go(floor)
        self.editable_objects.append(floor)

        player = GameObject("Player")
        player.transform.position = np.array([400.0, 200.0, 0.0], dtype=np.float32)
        player.transform.scale = np.array([36.0, 48.0, 1.0], dtype=np.float32)
        player.add_component(BoxCollider(width=36, height=48))
        player.add_component(RigidBody(mass=1.0, gravity_scale=1.0))
        player.mesh_type = "Player"
        self._add_go(player)
        self.editable_objects.append(player)

        self.selected_index = 1

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

