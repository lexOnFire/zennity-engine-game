from __future__ import annotations

from typing import Any, Callable, Dict, Optional

from engine.core.component import Component
from engine.component_registry import ComponentRegistry


@ComponentRegistry.component
class Health(Component):
    """Gerencia pontos de vida de um GameObject."""

    def __init__(self, max_hp: int = 100) -> None:
        super().__init__()
        self.max_hp = int(max_hp)
        self.hp = int(max_hp)
        self.on_death: Optional[Callable[[], None]] = None
        self.on_damaged: Optional[Callable[[int], None]] = None
        self._dead = False

    @property
    def is_alive(self) -> bool:
        return self.hp > 0

    def take_damage(self, amount: int) -> None:
        if self._dead:
            return
        self.hp = max(0, self.hp - int(amount))
        if self.on_damaged:
            self.on_damaged(int(amount))
        if self.hp <= 0:
            self._dead = True
            if self.on_death:
                self.on_death()
            elif self.game_object is not None:
                self.game_object.destroy()

    def heal(self, amount: int) -> None:
        self.hp = min(self.max_hp, self.hp + int(amount))
        if self.hp > 0:
            self._dead = False

    def reset(self) -> None:
        self.hp = self.max_hp
        self._dead = False

    def update(self, dt: float) -> None:
        pass

    def draw(self, screen) -> None:
        pass

    def serialize(self) -> Dict[str, Any]:
        data = super().serialize()
        data.update({"max_hp": self.max_hp, "hp": self.hp, "dead": self._dead})
        return data

    def deserialize(self, data: Dict[str, Any]) -> None:
        super().deserialize(data)
        self.max_hp = int(data.get("max_hp", 100))
        self.hp = int(data.get("hp", self.max_hp))
        self._dead = bool(data.get("dead", False))
