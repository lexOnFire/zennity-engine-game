"""
assets/scripts/camera_follow.py
───────────────────────────────────────────────────────────────
Câmera suave (lerp) que segue um GameObject alvo.

Anexe este script ao GameObject que representa a câmera,
ou a um GO vazio usado como âncora de câmera.

Uso:
    cam_go = GameObject("Camera")
    cf = CameraFollow(smoothing=5.0)
    cf.target = player  # atribua o alvo após criar o player
    cam_go.add_component(cf)
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from engine.core.component import Component
from engine.component_registry import ComponentRegistry


@ComponentRegistry.component
class CameraFollow(Component):
    """Segue um alvo com interpolação linear (lerp)."""

    def __init__(
        self,
        smoothing: float = 5.0,
        offset_x: float = 0.0,
        offset_y: float = 0.0,
        target_tag: str = "Player",
    ) -> None:
        super().__init__()
        self.smoothing: float = smoothing
        self.offset_x: float = offset_x
        self.offset_y: float = offset_y
        self.target_tag: str = target_tag
        self.target = None  # GameObject alvo (pode ser setado diretamente)

    # ------------------------------------------------------------------ #
    # Ciclo de vida
    # ------------------------------------------------------------------ #

    def start(self) -> None:
        if self.target is None:
            self._find_target()

    def update(self, dt: float) -> None:
        if self.target is None:
            self._find_target()
            return

        tx = self.target.transform.x + self.offset_x
        ty = self.target.transform.y + self.offset_y

        # Lerp suave
        t = min(1.0, self.smoothing * dt)
        self.transform.x += (tx - self.transform.x) * t
        self.transform.y += (ty - self.transform.y) * t

    def draw(self, screen) -> None:
        pass

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #

    def _find_target(self) -> None:
        scene = self.scene
        if scene is None:
            return
        for go in getattr(scene, "game_objects", []):
            if getattr(go, "tag", "") == self.target_tag:
                self.target = go
                return

    # ------------------------------------------------------------------ #
    # Serialização
    # ------------------------------------------------------------------ #

    def serialize(self) -> Dict[str, Any]:
        data = super().serialize()
        data["smoothing"] = self.smoothing
        data["offset_x"] = self.offset_x
        data["offset_y"] = self.offset_y
        data["target_tag"] = self.target_tag
        return data

    def deserialize(self, data: Dict[str, Any]) -> None:
        super().deserialize(data)
        self.smoothing = float(data.get("smoothing", 5.0))
        self.offset_x = float(data.get("offset_x", 0.0))
        self.offset_y = float(data.get("offset_y", 0.0))
        self.target_tag = data.get("target_tag", "Player")
