from __future__ import annotations

from typing import Any, Dict

import pygame

from engine.core.component import Component
from engine.component_registry import ComponentRegistry


@ComponentRegistry.component
class PlayerController(Component):
    """Movimenta o jogador com teclado e aplica pulo via Rigidbody."""

    def __init__(self, speed: float = 200.0, jump_force: float = 400.0) -> None:
        super().__init__()
        self.speed = float(speed)
        self.jump_force = float(jump_force)
        self._grounded = False
        self._rb = None

    def start(self) -> None:
        try:
            from engine.physics.rigidbody import Rigidbody
            self._rb = self.game_object.get_component(Rigidbody) if self.game_object else None
        except Exception:
            self._rb = None

    def update(self, dt: float) -> None:
        keys = pygame.key.get_pressed()
        dx = 0.0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            dx -= self.speed * dt
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            dx += self.speed * dt
        self.transform.translate(dx, 0.0)
        if (keys[pygame.K_SPACE] or keys[pygame.K_UP] or keys[pygame.K_w]) and self._grounded:
            if self._rb is not None:
                self._rb.velocity[1] = -self.jump_force
            else:
                self.transform.translate(0.0, -self.jump_force * dt)
            self._grounded = False

    def draw(self, screen) -> None:
        pass

    def serialize(self) -> Dict[str, Any]:
        data = super().serialize()
        data["speed"] = self.speed
        data["jump_force"] = self.jump_force
        return data

    def deserialize(self, data: Dict[str, Any]) -> None:
        super().deserialize(data)
        self.speed = float(data.get("speed", 200.0))
        self.jump_force = float(data.get("jump_force", 400.0))
