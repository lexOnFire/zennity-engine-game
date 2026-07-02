"""
Time — controle de tempo e delta-time do loop principal.

Responsabilidades:
  - Manter o clock do Pygame
  - Calcular delta-time (dt) com cap configurável
  - Expor dt, elapsed (tempo total) e fps_actual

Não tem conhecimento de cenas, janela ou física.
"""
from __future__ import annotations
import pygame


class Time:
    """Serviço de tempo gerenciado pela Application."""

    def __init__(self, target_fps: int = 60, dt_cap: float = 0.1) -> None:
        self._clock     = pygame.time.Clock()
        self.target_fps = target_fps
        self.dt_cap     = dt_cap

        self.dt:          float = 0.0   # delta-time do frame atual (segundos)
        self.elapsed:     float = 0.0   # tempo total acumulado desde o início
        self.fps_actual:  float = 0.0   # fps medido pelo clock

    def tick(self) -> float:
        """Avança o clock um frame. Retorna dt (segundos)."""
        raw_ms       = self._clock.tick(self.target_fps)
        self.dt      = min(raw_ms / 1000.0, self.dt_cap)
        self.elapsed += self.dt
        self.fps_actual = self._clock.get_fps()
        return self.dt
