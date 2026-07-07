from __future__ import annotations

import math
from typing import Any, Dict, Tuple

from engine.core.component import Component
from engine.component_registry import ComponentRegistry


@ComponentRegistry.component
class Projectile(Component):
    """Move-se em linha reta e se destrói após lifetime segundos."""

    def __init__(self, speed: float = 400.0, direction: Tuple[float, float] = (1.0, 0.0), lifetime: float = 2.0, damage: int = 10, hit_tag: str = "Enemy") -> None:
        super().__init__()
        self.speed = float(speed)
        self.damage = int(damage)
        self.lifetime = float(lifetime)
        self.hit_tag = str(hit_tag)
        self._elapsed = 0.0
        self._dead = False
        dx, dy = direction
        length = math.hypot(dx, dy) or 1.0
        self._dir_x = float(dx) / length
        self._dir_y = float(dy) / length

    def update(self, dt: float) -> None:
        if self._dead:
            return
        self.transform.translate(self._dir_x * self.speed * dt, self._dir_y * self.speed * dt)
        self._elapsed += dt
        if self._elapsed >= self.lifetime:
            self._dead = True
            if self.game_object is not None:
                self.game_object.destroy()
            return
        self._check_hit()

    def draw(self, screen) -> None:
        pass

    def _check_hit(self) -> None:
        scene = self.scene
        if scene is None:
            return
        for go in getattr(scene, "game_objects", []):
            if getattr(go, "tag", "") != self.hit_tag:
                continue
            dist = math.hypot(go.transform.x - self.transform.x, go.transform.y - self.transform.y)
            if dist < 16.0:
                try:
                    from assets.scripts.health import Health
                    health = go.get_component(Health)
                    if health:
                        health.take_damage(self.damage)
                except Exception:
                    pass
                self._dead = True
                if self.game_object is not None:
                    self.game_object.destroy()
                return

    def serialize(self) -> Dict[str, Any]:
        data = super().serialize()
        data.update({"speed": self.speed, "damage": self.damage, "lifetime": self.lifetime, "hit_tag": self.hit_tag, "elapsed": self._elapsed, "dir_x": self._dir_x, "dir_y": self._dir_y})
        return data

    def deserialize(self, data: Dict[str, Any]) -> None:
        super().deserialize(data)
        self.speed = float(data.get("speed", 400.0))
        self.damage = int(data.get("damage", 10))
        self.lifetime = float(data.get("lifetime", 2.0))
        self.hit_tag = str(data.get("hit_tag", "Enemy"))
        self._elapsed = float(data.get("elapsed", 0.0))
        self._dir_x = float(data.get("dir_x", 1.0))
        self._dir_y = float(data.get("dir_y", 0.0))
