from __future__ import annotations

import math
from typing import Any, Dict

from engine.core.component import Component
from engine.component_registry import ComponentRegistry


@ComponentRegistry.component
class EnemyAI(Component):
    """Persegue o GameObject com tag='Player' na cena."""

    def __init__(self, speed: float = 80.0, stop_distance: float = 40.0, target_tag: str = "Player") -> None:
        super().__init__()
        self.speed = float(speed)
        self.stop_distance = float(stop_distance)
        self.target_tag = str(target_tag)
        self._target = None

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
        if dist <= self.stop_distance or dist <= 0.001:
            return
        self.transform.translate((dx / dist) * self.speed * dt, (dy / dist) * self.speed * dt)

    def draw(self, screen) -> None:
        pass

    def _find_target(self) -> None:
        scene = self.scene
        if scene is None:
            return
        for go in getattr(scene, "game_objects", []):
            if getattr(go, "tag", "") == self.target_tag:
                self._target = go
                return

    def serialize(self) -> Dict[str, Any]:
        data = super().serialize()
        data.update({"speed": self.speed, "stop_distance": self.stop_distance, "target_tag": self.target_tag})
        return data

    def deserialize(self, data: Dict[str, Any]) -> None:
        super().deserialize(data)
        self.speed = float(data.get("speed", 80.0))
        self.stop_distance = float(data.get("stop_distance", 40.0))
        self.target_tag = str(data.get("target_tag", "Player"))
