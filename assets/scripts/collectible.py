"""
assets/scripts/collectible.py
───────────────────────────────────────────────────────────────
Item coletável: detecta overlap com o jogador e dispara callback.

Uso:
    coin = GameObject("Coin", tag="Collectible")
    c = Collectible(collect_radius=20)
    c.on_collect = lambda player: print("coletado!")
    coin.add_component(c)
"""
from __future__ import annotations

import math
from typing import Any, Callable, Dict, Optional

from engine.core.component import Component
from engine.component_registry import ComponentRegistry


@ComponentRegistry.component
class Collectible(Component):
    """Detecta sobreposição com o player e executa on_collect."""

    def __init__(
        self,
        collect_radius: float = 24.0,
        target_tag: str = "Player",
        destroy_on_collect: bool = True,
    ) -> None:
        super().__init__()
        self.collect_radius: float = collect_radius
        self.target_tag: str = target_tag
        self.destroy_on_collect: bool = destroy_on_collect
        self.on_collect: Optional[Callable] = None
        self._collected: bool = False

    # ------------------------------------------------------------------ #
    # Ciclo de vida
    # ------------------------------------------------------------------ #

    def start(self) -> None:
        pass

    def update(self, dt: float) -> None:
        if self._collected:
            return

        scene = self.scene
        if scene is None:
            return

        for go in getattr(scene, "game_objects", []):
            if go.tag != self.target_tag:
                continue
            dist = math.hypot(
                go.transform.x - self.transform.x,
                go.transform.y - self.transform.y,
            )
            if dist <= self.collect_radius:
                self._collected = True
                if self.on_collect:
                    self.on_collect(go)
                if self.destroy_on_collect:
                    self.game_object.destroy()
                return

    def draw(self, screen) -> None:
        pass

    # ------------------------------------------------------------------ #
    # Serialização
    # ------------------------------------------------------------------ #

    def serialize(self) -> Dict[str, Any]:
        data = super().serialize()
        data["collect_radius"] = self.collect_radius
        data["target_tag"] = self.target_tag
        data["destroy_on_collect"] = self.destroy_on_collect
        data["collected"] = self._collected
        return data

    def deserialize(self, data: Dict[str, Any]) -> None:
        super().deserialize(data)
        self.collect_radius = float(data.get("collect_radius", 24.0))
        self.target_tag = data.get("target_tag", "Player")
        self.destroy_on_collect = bool(data.get("destroy_on_collect", True))
        self._collected = bool(data.get("collected", False))
