from __future__ import annotations

from typing import Any, Dict

from engine.core.component import Component
from engine.component_registry import ComponentRegistry


@ComponentRegistry.component
class CameraFollow(Component):
    """Segue um alvo com interpolação linear."""

    def __init__(self, smoothing: float = 5.0, offset_x: float = 0.0, offset_y: float = 0.0, target_tag: str = "Player") -> None:
        super().__init__()
        self.smoothing = float(smoothing)
        self.offset_x = float(offset_x)
        self.offset_y = float(offset_y)
        self.target_tag = str(target_tag)
        self.target = None

    def start(self) -> None:
        if self.target is None:
            self._find_target()

    def update(self, dt: float) -> None:
        if self.target is None:
            self._find_target()
            return
        tx = self.target.transform.x + self.offset_x
        ty = self.target.transform.y + self.offset_y
        t = min(1.0, self.smoothing * dt)
        self.transform.x += (tx - self.transform.x) * t
        self.transform.y += (ty - self.transform.y) * t

    def draw(self, screen) -> None:
        pass

    def _find_target(self) -> None:
        scene = self.scene
        if scene is None:
            return
        for go in getattr(scene, "game_objects", []):
            if getattr(go, "tag", "") == self.target_tag:
                self.target = go
                return

    def serialize(self) -> Dict[str, Any]:
        data = super().serialize()
        data.update({"smoothing": self.smoothing, "offset_x": self.offset_x, "offset_y": self.offset_y, "target_tag": self.target_tag})
        return data

    def deserialize(self, data: Dict[str, Any]) -> None:
        super().deserialize(data)
        self.smoothing = float(data.get("smoothing", 5.0))
        self.offset_x = float(data.get("offset_x", 0.0))
        self.offset_y = float(data.get("offset_y", 0.0))
        self.target_tag = str(data.get("target_tag", "Player"))
