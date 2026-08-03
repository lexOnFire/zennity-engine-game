"""
assets/scripts/enemy_ai.py
───────────────────────────────────────────────────────────────
IA básica de perseguição: move-se em direção ao GameObject
do jogador (tag="Player") até uma distância de parada.

Uso:
    from assets.scripts.enemy_ai import EnemyAI

    enemy = GameObject("Enemy", tag="Enemy")
    enemy.add_component(EnemyAI(speed=80, stop_distance=40))
"""
from __future__ import annotations

import math
from typing import Any, Dict, Optional

from engine.core.component import Component
from engine.component_registry import ComponentRegistry


@ComponentRegistry.component
class EnemyAI(Component):
    """Persegue o GameObject com tag='Player' na cena."""

    def __init__(
        self,
        speed: float = 80.0,
        stop_distance: float = 40.0,
        target_tag: str = "Player",
    ) -> None:
        super().__init__()
        self.speed: float = speed
        self.stop_distance: float = stop_distance
        self.target_tag: str = target_tag
        self._target = None  # GameObject alvo

    # ------------------------------------------------------------------ #
    # Ciclo de vida
    # ------------------------------------------------------------------ #

    def start(self) -> None:
        self._find_target()

    def update(self, dt: float) -> None:
        if self._target is None:
            self._find_target()
            return

        ex, ey = self.transform.x, self.transform.y
        tx, ty = self._target.transform.x, self._target.transform.y

        dx, dy = tx - ex, ty - ey
        dist = math.hypot(dx, dy)

        if dist <= max(0.0001, self.stop_distance):
            return

        # Normaliza e aplica velocidade
        nx, ny = dx / dist, dy / dist
        self.transform.translate(nx * self.speed * dt, ny * self.speed * dt)

    def draw(self, screen) -> None:
        pass

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #

    def _find_target(self) -> None:
        scene = self.scene
        if scene is None:
            return
        # Procura por tag na cena
        for go in getattr(scene, "game_objects", []):
            if getattr(go, "tag", "") == self.target_tag:
                self._target = go
                return

    # ------------------------------------------------------------------ #
    # Serialização
    # ------------------------------------------------------------------ #

    def serialize(self) -> Dict[str, Any]:
        data = super().serialize()
        data["speed"] = self.speed
        data["stop_distance"] = self.stop_distance
        data["target_tag"] = self.target_tag
        return data

    def deserialize(self, data: Dict[str, Any]) -> None:
        super().deserialize(data)
        self.speed = float(data.get("speed", 80.0))
        self.stop_distance = float(data.get("stop_distance", 40.0))
        self.target_tag = data.get("target_tag", "Player")
