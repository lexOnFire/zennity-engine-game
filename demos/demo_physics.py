"""
Demo: física básica com gravidade, colisão e câmera.

Controles:
    WASD / Setas  — move o player
    ESPAÇO        — pula
    ESC           — sair
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pygame
from engine.core import Engine, Scene
from engine.game_object import GameObject
from engine.physics.rigidbody import RigidBody
from engine.physics.collider import BoxCollider
from engine.graphics.camera import Camera
from engine.graphics.renderer import SpriteRenderer
from engine.input import Input


class DemoScene(Scene):
    def start(self) -> None:
        # ---------- Câmera ----------
        cam_obj = GameObject("Camera")
        cam_obj.transform.x = 400
        cam_obj.transform.y = 300
        self.camera = Camera(screen_width=800, screen_height=600, follow_speed=6.0)
        cam_obj.add_component(self.camera)
        cam_obj.scene = self
        self.camera.start()

        # ---------- Chão ----------
        self.ground = GameObject("Ground")
        self.ground.transform.x = 400
        self.ground.transform.y = 560
        self.ground.scene = self

        ground_col = BoxCollider(width=800, height=40, is_trigger=False, debug_draw=True)
        self.ground.add_component(ground_col)
        ground_col.start()

        ground_render = SpriteRenderer(color=(80, 80, 80), width=800, height=40)
        self.ground.add_component(ground_render)

        # ---------- Player ----------
        self.player = GameObject("Player")
        self.player.transform.x = 400
        self.player.transform.y = 200
        self.player.scene = self

        self.rb = RigidBody(mass=1.0, gravity_scale=1.0, drag=0.05, use_gravity=True)
        self.player.add_component(self.rb)

        player_col = BoxCollider(width=32, height=48, debug_draw=True)
        self.player.add_component(player_col)
        player_col.start()

        player_render = SpriteRenderer(color=(70, 130, 180), width=32, height=48)
        self.player.add_component(player_render)

        # Câmera segue o player
        self.camera.set_target(self.player)

        self._on_ground = False

        def on_enter(info):
            self._on_ground = True

        def on_exit(other):
            self._on_ground = False

        player_col.on_collision_enter = on_enter
        player_col.on_collision_exit = on_exit

    def update(self, dt: float) -> None:
        speed = 200.0
        jump_force = -450.0

        # Movimento horizontal
        if Input.is_key_held(pygame.K_a) or Input.is_key_held(pygame.K_LEFT):
            self.rb.set_velocity(-speed, self.rb.velocity[1])
        elif Input.is_key_held(pygame.K_d) or Input.is_key_held(pygame.K_RIGHT):
            self.rb.set_velocity(speed, self.rb.velocity[1])
        else:
            self.rb.set_velocity(0, self.rb.velocity[1])

        # Pulo
        if (Input.is_key_pressed(pygame.K_SPACE) or Input.is_key_pressed(pygame.K_w)) and self._on_ground:
            self.rb.add_impulse(0, jump_force * self.rb.mass)

        # Sair
        if Input.is_key_pressed(pygame.K_ESCAPE):
            self.engine.is_running = False

        # Atualiza objetos
        self.ground.update(dt)
        self.player.update(dt)
        self.camera.update(dt)

        # Verifica colisões
        BoxCollider.check_all()

    def draw(self, screen: pygame.Surface) -> None:
        screen.fill((20, 20, 35))
        self.ground.draw(screen)
        self.player.draw(screen)

        # HUD
        font = pygame.font.SysFont(None, 24)
        hud = font.render("WASD: mover | ESPAÇO: pular | ESC: sair", True, (200, 200, 200))
        screen.blit(hud, (10, 10))


if __name__ == "__main__":
    engine = Engine(width=800, height=600, title="Zennity Engine — Demo Física")
    engine.run(DemoScene())
