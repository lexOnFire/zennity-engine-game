"""
assets/scripts/player_controller.py
───────────────────────────────────────────────────────────────
Controle de personagem do jogador (WASD / setas + pulo).

Dependências esperadas no GameObject:
    - Transform   (adicionado automaticamente)
    - Rigidbody   (engine.physics)

Uso:
    from assets.scripts.player_controller import PlayerController

    player = GameObject("Player", tag="Player")
    player.add_component(Rigidbody())
    player.add_component(PlayerController(speed=200, jump_force=400))
"""
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
        self.speed: float = speed
        self.jump_force: float = jump_force
        self._grounded: bool = False
        self._rb = None  # cache do Rigidbody

    # ------------------------------------------------------------------ #
    # Ciclo de vida
    # ------------------------------------------------------------------ #

    def start(self) -> None:
        # Tenta obter o Rigidbody do mesmo GameObject
        try:
            from engine.physics.rigidbody import Rigidbody
            self._rb = self.game_object.get_component(Rigidbody)
        except ImportError:
            self._rb = None

    def update(self, dt: float) -> None:
        keys = pygame.key.get_pressed()

        dx = 0.0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            dx -= self.speed * dt
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            dx += self.speed * dt

        self.transform.translate(dx, 0.0)

        # Pulo
        if (keys[pygame.K_SPACE] or keys[pygame.K_UP] or keys[pygame.K_w]) and self._grounded:
            if self._rb is not None:
                self._rb.velocity[1] = -self.jump_force
            else:
                self.transform.translate(0.0, -self.jump_force * dt)
            self._grounded = False

    def draw(self, screen) -> None:
        pass  # renderização feita pelo SpriteRenderer

    # ------------------------------------------------------------------ #
    # Serialização
    # ------------------------------------------------------------------ #

    def serialize(self) -> Dict[str, Any]:
        data = super().serialize()
        data["speed"] = self.speed
        data["jump_force"] = self.jump_force
        return data

    def deserialize(self, data: Dict[str, Any]) -> None:
        super().deserialize(data)
        self.speed = float(data.get("speed", 200.0))
        self.jump_force = float(data.get("jump_force", 400.0))
