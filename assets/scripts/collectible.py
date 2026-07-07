from __future__ import annotations

import math
from typing import Any, Callable, Dict, Optional

from engine.core.component import Component
from engine.component_registry import ComponentRegistry


@ComponentRegistry.component
class Collectible(Component):
    """Detecta sobreposição com o player e executa on_collect."""

    def __init__(self, collect_radius: float = 24.0, target_tag: str = "Player", destroy_on_collect: bool = True) -> None:
        super().__init__()
        self.collect_radius = float(collect_radius)
        self.target_tag = str(target_tag)
        self.destroy_on_collect = bool(destroy_on_collect)
        self.on_collect: Optional[Callable] = None
        self._collected = False

    def update(self, dt: float) -> None:
        if self._collected or self.scene is None:
            return
        for go in getattr(self.scene, "game_objects", []):
            if getattr(go, "tag", "") != self.target_tag:
                continue
            dist = math.hypot(go.transform.x - self.transform.x, go.transform.y - self.transform.y)
            if dist <= self.collect_radius:
                self._collected = True
                if self.on_collect:
                    self.on_collect(go)
                if self.destroy_on_collect and self.game_object is not None:
                    self.game_object.destroy()
                return

    def draw(self, screen) -> None:
        pass

    def serialize(self) -> Dict[str, Any]:
        data = super().serialize()
        data.update({"collect_radius": self.collect_radius, "target_tag": self.target_tag, "destroy_on_collect": self.destroy_on_collect, "collected": self._collected})
        return data

    def deserialize(self, data: Dict[str, Any]) -> None:
        super().deserialize(data)
        self.collect_radius = float(data.get("collect_radius", 24.0))
        self.target_tag = str(data.get("target_tag", "Player"))
        self.destroy_on_collect = bool(data.get("destroy_on_collect", True))
        self._collected = bool(data.get("collected", False))
