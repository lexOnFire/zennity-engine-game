"""
assets/scripts/health.py
───────────────────────────────────────────────────────────────
Sistema de vida genérico.

Funcionalidades:
    - take_damage(amount)   → reduz HP; dispara on_death se <= 0
    - heal(amount)          → restaura HP até max_hp
    - is_alive              → property booleana
    - on_death callback     → função chamada quando HP chega a 0

Uso:
    health = Health(max_hp=100)
    health.on_death = lambda: print("morreu!")
    go.add_component(health)
"""
from __future__ import annotations

from typing import Any, Callable, Dict, Optional

from engine.core.component import Component
from engine.component_registry import ComponentRegistry


@ComponentRegistry.component
class Health(Component):
    """Gerencia pontos de vida de um GameObject."""

    def __init__(self, max_hp: int = 100) -> None:
        super().__init__()
        self.max_hp: int = max_hp
        self.hp: int = max_hp
        self.on_death: Optional[Callable[[], None]] = None
        self.on_damaged: Optional[Callable[[int], None]] = None
        self._dead: bool = False

    # ------------------------------------------------------------------ #
    # API pública
    # ------------------------------------------------------------------ #

    @property
    def is_alive(self) -> bool:
        return self.hp > 0

    def take_damage(self, amount: int) -> None:
        if self._dead:
            return
        self.hp = max(0, self.hp - amount)
        if self.on_damaged:
            self.on_damaged(amount)
        if self.hp <= 0:
            self._dead = True
            if self.on_death:
                self.on_death()
            else:
                self.game_object.destroy()

    def heal(self, amount: int) -> None:
        self.hp = min(self.max_hp, self.hp + amount)
        if self.hp > 0:
            self._dead = False

    def reset(self) -> None:
        """Restaura HP máximo e limpa estado de morte."""
        self.hp = self.max_hp
        self._dead = False

    # ------------------------------------------------------------------ #
    # Ciclo de vida
    # ------------------------------------------------------------------ #

    def start(self) -> None:
        pass

    def update(self, dt: float) -> None:
        pass

    def draw(self, screen) -> None:
        pass

    # ------------------------------------------------------------------ #
    # Serialização
    # ------------------------------------------------------------------ #

    def serialize(self) -> Dict[str, Any]:
        data = super().serialize()
        data["max_hp"] = self.max_hp
        data["hp"] = self.hp
        data["dead"] = self._dead
        return data

    def deserialize(self, data: Dict[str, Any]) -> None:
        super().deserialize(data)
        self.max_hp = int(data.get("max_hp", 100))
        self.hp = int(data.get("hp", self.max_hp))
        self._dead = bool(data.get("dead", False))
