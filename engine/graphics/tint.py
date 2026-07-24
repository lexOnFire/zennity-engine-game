"""Contrato compartilhado de tint RGBA para renderizadores 2D."""
from __future__ import annotations

from typing import Any


def normalize_tint(value: Any) -> tuple[int, int, int, int]:
    if not isinstance(value, (tuple, list)):
        return (255, 255, 255, 255)
    channels = list(value[:4]) + [255] * max(0, 4 - len(value))
    return tuple(max(0, min(255, int(channel))) for channel in channels[:4])


def combined_alpha(alpha: Any, tint: Any) -> int:
    base = max(0, min(255, int(alpha)))
    return round(base * normalize_tint(tint)[3] / 255.0)


def apply_pygame_tint(surface: Any, tint: Any, alpha: Any = 255) -> Any:
    """Aplica multiplicação RGB e alpha uniforme sem modificar a Surface fonte."""
    rgba = normalize_tint(tint)
    effective_alpha = combined_alpha(alpha, rgba)
    if rgba[:3] == (255, 255, 255) and effective_alpha == 255:
        return surface
    import pygame
    result = surface.copy()
    if rgba[:3] != (255, 255, 255):
        result.fill((*rgba[:3], 255), special_flags=pygame.BLEND_RGBA_MULT)
    if effective_alpha < 255:
        result.set_alpha(effective_alpha)
    return result

