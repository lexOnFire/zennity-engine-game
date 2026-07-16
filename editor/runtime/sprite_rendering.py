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


def prepare_scrolling_sprite_surface(
    source: Any,
    size: tuple[int, int],
    tint: Any = NEUTRAL_SPRITE_COLOR,
    *,
    offset_x: float = 0.0,
    offset_y: float = 0.0,
    repeat_x: bool = True,
    repeat_y: bool = False,
) -> Any:
    """Cria um plano texturizado repetível sem alterar o Sprite Renderer comum.

    A textura ocupa uma vez o tamanho do plano. Cópias vizinhas entram pelas
    bordas conforme o offset avança, produzindo pista, céu ou parallax contínuo.
    """
    import pygame

    tile = prepare_sprite_surface(source, size, tint)
    width, height = tile.get_size()
    result = pygame.Surface((width, height), pygame.SRCALPHA)
    start_x = -int(float(offset_x) % width) if repeat_x else 0
    start_y = -int(float(offset_y) % height) if repeat_y else 0
    x_positions = range(start_x, width + 1, width) if repeat_x else (0,)
    y_positions = range(start_y, height + 1, height) if repeat_y else (0,)
    for x in x_positions:
        for y in y_positions:
            result.blit(tile, (x, y))
    return result
