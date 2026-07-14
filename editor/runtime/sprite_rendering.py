"""Contrato de textura do Sprite Renderer usado pelo viewport isolado."""
from __future__ import annotations

from typing import Any, MutableMapping


NEUTRAL_SPRITE_COLOR = (255, 255, 255)


def assign_sprite_texture(obj: MutableMapping[str, Any], texture: str) -> None:
    """Associa uma textura sem herdar a cor visual do placeholder do objeto."""
    obj["texture"] = str(texture)
    obj["color"] = NEUTRAL_SPRITE_COLOR


def prepare_sprite_surface(source: Any, size: tuple[int, int], tint: Any = NEUTRAL_SPRITE_COLOR) -> Any:
    """Redimensiona com pixel perfeito e aplica apenas o tint configurado."""
    import pygame

    target_size = (max(1, int(size[0])), max(1, int(size[1])))
    surface = source.copy() if source.get_size() == target_size else pygame.transform.scale(source, target_size)
    try:
        from engine.graphics.tint import apply_pygame_tint
    except ModuleNotFoundError:  # Runtime autocontido criado pelo exportador.
        from .tint import apply_pygame_tint

    return apply_pygame_tint(surface, tint)
