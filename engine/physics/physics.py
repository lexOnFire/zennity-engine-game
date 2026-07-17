from __future__ import annotations

from typing import Any


class Physics:
    """Public runtime physics query facade for scripts and gameplay code."""

    _world: Any | None = None

    @classmethod
    def bind_world(cls, world: Any) -> None:
        cls._world = world

    @classmethod
    def unbind_world(cls, world: Any | None = None) -> None:
        if world is None or cls._world is world:
            cls._world = None

    @classmethod
    def contacts(cls) -> list[Any]:
        if cls._world is None:
            return []
        return list(getattr(cls._world, "detected_contacts", []))

    @classmethod
    def is_colliding(cls, collider: Any) -> bool:
        return any(contact.a is collider or contact.b is collider for contact in cls.contacts())
