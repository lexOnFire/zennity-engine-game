from __future__ import annotations
import numpy as np

from engine.core import Scene
from engine.game_object import GameObject
from engine.graphics.camera2d import Camera2D
from engine.physics.rigidbody import RigidBody
from engine.physics.collider import BoxCollider
from engine.graphics.camera import Camera


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
        self.cam_obj.transform.position = np.array([0.0, 0.0, 0.0], dtype=np.float32)
        self._add_go(self.cam_obj)
        Camera2D.main = self.camera
        self.spawn_default_scene()
        

    def _layout(self) -> dict:
        return {
            "viewport_x": 0,
            "viewport_y": 0,
            "viewport_w": 800,
            "viewport_h": 600,
        }

    def spawn_default_scene(self) -> None:
        import pygame
        
        floor = GameObject("Chao")
        floor.transform.position = np.array([0.0, 120.0, 0.0], dtype=np.float32)
        floor.transform.scale = np.array([600.0, 32.0, 1.0], dtype=np.float32)
        floor.add_component(BoxCollider(width=600, height=32))
        rb_floor = floor.add_component(RigidBody())
        rb_floor.is_kinematic = True
        surf_floor = pygame.Surface((1, 1))
        surf_floor.fill((100, 200, 100))
        self._add_sprite_renderer(floor, surf_floor)
        floor.mesh_type = "Plataforma"
        self._add_go(floor)
        self.editable_objects.append(floor)

        player = GameObject("Player")
        player.transform.position = np.array([0.0, 0.0, 0.0], dtype=np.float32)
        player.transform.scale = np.array([36.0, 48.0, 1.0], dtype=np.float32)
        player.add_component(BoxCollider(width=36, height=48))
        player.add_component(RigidBody(mass=1.0, gravity_scale=1.0))
        surf_player = pygame.Surface((1, 1))
        surf_player.fill((100, 100, 255))
        self._add_sprite_renderer(player, surf_player)
        player.mesh_type = "Player"
        self._add_go(player)
        self.editable_objects.append(player)

        self.selected_index = 1

    
    def _add_sprite_renderer(self, go: GameObject, surface) -> None:
        from engine.graphics.renderer2d import SpriteRenderer
        try:
            renderer = SpriteRenderer(surface)
        except TypeError:
            renderer = SpriteRenderer()
            if hasattr(renderer, "image"):
                renderer.image = surface
        if not hasattr(renderer, "_started"):
            renderer._started = False
        if not hasattr(renderer, "enabled"):
            renderer.enabled = True
        for method_name in ("start", "update", "draw", "destroy"):
            if not hasattr(renderer, method_name):
                setattr(renderer, method_name, lambda *args, **kwargs: None)
        go.add_component(renderer)



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

    def spawn_object(self, shape: str) -> None:
        """Cria um novo objeto 2D na cena."""

        if self.playing:
            return

        go = GameObject(f"{shape}_{len(self.editable_objects)}")
        
        # Tenta usar a posição da câmera como centro, fallback para 0,0
        from engine.graphics.camera2d import Camera2D
        if Camera2D.main:
            go.transform.position = np.array(Camera2D.main.transform.position, dtype=np.float32)
        else:
            go.transform.position = np.array([0.0, 0.0, 0.0], dtype=np.float32)
        
        import pygame

        if shape == "Quadrado":
            go.transform.scale = np.array([40.0, 40.0, 1.0], dtype=np.float32)
            go.add_component(BoxCollider(width=40, height=40))
            go.add_component(RigidBody(mass=1.0))
            surf = pygame.Surface((1, 1))
            surf.fill((200, 200, 200))
            self._add_sprite_renderer(go, surf)

        elif shape == "Plataforma":
            go.transform.scale = np.array([120.0, 24.0, 1.0], dtype=np.float32)
            go.add_component(BoxCollider(width=120, height=24))
            rb = go.add_component(RigidBody())
            rb.is_kinematic = True
            surf = pygame.Surface((1, 1))
            surf.fill((100, 200, 100))
            self._add_sprite_renderer(go, surf)

        elif shape == "Player":
            go.transform.scale = np.array([36.0, 48.0, 1.0], dtype=np.float32)
            go.add_component(BoxCollider(width=36, height=48))
            go.add_component(RigidBody(mass=1.0, gravity_scale=1.0))
            surf = pygame.Surface((1, 1))
            surf.fill((100, 100, 255))
            self._add_sprite_renderer(go, surf)

        elif shape == "Inimigo":
            go.transform.scale = np.array([36.0, 36.0, 1.0], dtype=np.float32)
            go.add_component(BoxCollider(width=36, height=36))
            go.add_component(RigidBody(mass=1.0, gravity_scale=1.0))
            surf = pygame.Surface((1, 1))
            surf.fill((255, 100, 100))
            self._add_sprite_renderer(go, surf)

        elif shape == "Camera 2D":
            go.name = f"Camera2D_{len(self.editable_objects)}"
            go.transform.scale = np.array([64.0, 40.0, 1.0], dtype=np.float32)

            cam2d = go.add_component(Camera2D(zoom=1.0))
            go.add_component(
                Camera(
                    zoom=1.0,
                    clear_color=(18, 20, 27),
                    priority=10,
                    active=True,
                )
            )
            Camera2D.main = cam2d

        else:
            go.transform.scale = np.array([40.0, 40.0, 1.0], dtype=np.float32)
            surf = pygame.Surface((1, 1))
            surf.fill((200, 200, 200))
            self._add_sprite_renderer(go, surf)

        go.mesh_type = shape

        self._add_go(go)
        self.editable_objects.append(go)
        self.selected_index = len(self.editable_objects) - 1

    def delete_selected(self) -> None:
        if not (0 <= self.selected_index < len(self.editable_objects)):
            return

        obj = self.editable_objects[self.selected_index]

        self._remove_go(obj)

        if self.editable_objects:
            self.selected_index = min(
            self.selected_index,
            len(self.editable_objects) - 1,
        )
        else:
            self.selected_index = -1
            self._remove_go(obj)

    def _draw_object(
        self,
        screen,
        obj,
        idx=None,
        zoom=1.0,
        lay=None,
    ) -> None:
        if getattr(obj, "runtime_hidden", False):
            return

        if hasattr(obj, "draw"):
            obj.draw(screen)

