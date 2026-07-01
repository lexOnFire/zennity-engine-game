from __future__ import annotations
"""
engine/graphics/particles.py
────────────────────────────
Sistema de Partículas 2D integrado ao padrão ECS.
"""

import math
import random
import pygame
import numpy as np
from typing import List, Tuple, Optional, Any
from engine.component import Component
from engine.graphics.camera2d import Camera2D


class Particle:
    """Dados compactos de uma partícula individual."""
    __slots__ = ("position", "velocity", "color", "start_size", "end_size", "life", "max_life")

    def __init__(
        self,
        x: float,
        y: float,
        vx: float,
        vy: float,
        color: pygame.Color,
        start_size: float,
        end_size: float,
        lifetime: float,
    ) -> None:
        self.position = np.array([x, y], dtype=np.float32)
        self.velocity = np.array([vx, vy], dtype=np.float32)
        self.color = color
        self.start_size = start_size
        self.end_size = end_size
        self.life = lifetime
        self.max_life = lifetime


class ParticleSystem(Component):
    """
    Componente emissor de partículas simples em 2D.
    Pode ser configurado para emitir em rajadas (burst) ou continuamente.
    """

    def __init__(
        self,
        emission_rate: float = 20.0,       # Partículas geradas por segundo (0 para apenas bursts manuais)
        lifetime: float = 1.0,            # Ciclo de vida médio de cada partícula em segundos
        speed: float = 80.0,              # Velocidade inicial
        spread: float = 360.0,             # Leque de dispersão em graus
        start_size: float = 6.0,          # Tamanho inicial
        end_size: float = 1.0,            # Tamanho final
        start_color: Tuple[int, int, int] = (255, 180, 50),
        end_color: Tuple[int, int, int] = (255, 30, 0),
        gravity: float = 0.0,             # Aceleração vertical aplicada ao longo do tempo
    ) -> None:
        super().__init__()
        self.emission_rate = emission_rate
        self.lifetime = lifetime
        self.speed = speed
        self.spread = spread
        self.start_size = start_size
        self.end_size = end_size
        self.start_color = pygame.Color(*start_color)
        self.end_color = pygame.Color(*end_color)
        self.gravity = gravity

        self.particles: List[Particle] = []
        self._emit_timer: float = 0.0

    def emit(self, count: int = 1) -> None:
        """Dispara um burst imediato de N partículas a partir da posição do GameObject."""
        if self.game_object is None:
            return

        pos = self.game_object.transform.get_world_position()
        base_angle = self.game_object.transform.rotation[2] if len(self.game_object.transform.rotation) > 2 else 0.0

        for _ in range(count):
            # Calcula ângulo aleatório dentro do spread
            angle = random.uniform(base_angle - self.spread / 2, base_angle + self.spread / 2)
            rad = math.radians(angle)

            # Velocidade aleatória sutil
            sp = self.speed * random.uniform(0.5, 1.3)
            vx = math.cos(rad) * sp
            vy = math.sin(rad) * sp

            p = Particle(
                float(pos[0]),
                float(pos[1]),
                vx,
                vy,
                pygame.Color(self.start_color),
                self.start_size,
                self.end_size,
                self.lifetime * random.uniform(0.6, 1.4),
            )
            self.particles.append(p)

    def update(self, dt: float) -> None:
        # Emissão contínua baseada no timer
        if self.emission_rate > 0.0:
            self._emit_timer += dt
            interval = 1.0 / self.emission_rate
            while self._emit_timer >= interval:
                self.emit(1)
                self._emit_timer -= interval

        # Atualização física e ciclo de vida
        dead_list = []
        for p in self.particles:
            p.life -= dt
            if p.life <= 0.0:
                dead_list.append(p)
                continue

            # Aplica gravidade
            p.velocity[1] += self.gravity * dt
            p.position += p.velocity * dt

        # Purga de partículas encerradas
        for p in dead_list:
            self.particles.remove(p)

    def draw(self, screen: pygame.Surface) -> None:
        cam = Camera2D.main
        cx, cy = (cam.game_object.transform.position[0], cam.game_object.transform.position[1]) if cam and cam.game_object else (0.0, 0.0)
        sw, sh = screen.get_size()

        for p in self.particles:
            pct = max(0.0, min(1.0, p.life / p.max_life))

            # Interpolação linear de cor
            r = int(self.end_color.r + (self.start_color.r - self.end_color.r) * pct)
            g = int(self.end_color.g + (self.start_color.g - self.end_color.g) * pct)
            b = int(self.end_color.b + (self.start_color.b - self.end_color.b) * pct)
            a = int(255 * pct)

            # Interpolação de tamanho
            size = p.end_size + (p.start_size - p.end_size) * pct
            if size <= 0.5:
                continue

            # Conversão para o viewport offset de câmera
            px = p.position[0] - size / 2.0
            py = p.position[1] - size / 2.0
            if cam:
                px = px - cx + sw / 2.0
                py = py - cy + sh / 2.0

            # Frustum culling básico
            if -size <= px <= sw + size and -size <= py <= sh + size:
                if a < 230:
                    # Desenha com transparência
                    surf = pygame.Surface((int(size * 2), int(size * 2)), pygame.SRCALPHA)
                    pygame.draw.circle(surf, (r, g, b, a), (int(size), int(size)), int(size))
                    screen.blit(surf, (int(px - size/2), int(py - size/2)))
                else:
                    pygame.draw.circle(screen, (r, g, b), (int(px), int(py)), int(size))
