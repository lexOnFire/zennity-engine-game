from __future__ import annotations

import pygame

from editor.runtime.sprite_rendering import (
    assign_sprite_texture,
    prepare_scrolling_sprite_surface,
    prepare_sprite_surface,
)


def test_assigning_texture_resets_placeholder_tint_to_white() -> None:
    obj = {"name": "Player", "color": (88, 117, 255)}

    assign_sprite_texture(obj, "Assets/Textures/player.png")

    assert obj["texture"] == "Assets/Textures/player.png"
    assert obj["color"] == (255, 255, 255)


def test_pixel_art_scaling_keeps_exact_colors_with_neutral_tint() -> None:
    source = pygame.Surface((2, 1), pygame.SRCALPHA)
    source.set_at((0, 0), (240, 30, 20, 255))
    source.set_at((1, 0), (10, 220, 80, 255))

    result = prepare_sprite_surface(source, (4, 2))

    assert result.get_at((0, 0)) == pygame.Color(240, 30, 20, 255)
    assert result.get_at((1, 1)) == pygame.Color(240, 30, 20, 255)
    assert result.get_at((2, 0)) == pygame.Color(10, 220, 80, 255)
    assert result.get_at((3, 1)) == pygame.Color(10, 220, 80, 255)


def test_manual_sprite_tint_remains_available() -> None:
    source = pygame.Surface((1, 1), pygame.SRCALPHA)
    source.fill((255, 255, 255, 255))

    result = prepare_sprite_surface(source, (1, 1), (80, 120, 200))

    assert result.get_at((0, 0)) == pygame.Color(80, 120, 200, 255)


def test_scrolling_sprite_wraps_image_inside_plane() -> None:
    source = pygame.Surface((2, 1), pygame.SRCALPHA)
    source.set_at((0, 0), (255, 0, 0, 255))
    source.set_at((1, 0), (0, 0, 255, 255))

    result = prepare_scrolling_sprite_surface(
        source, (2, 1), offset_x=1, repeat_x=True, repeat_y=False
    )

    assert result.get_at((0, 0)) == pygame.Color(0, 0, 255, 255)
    assert result.get_at((1, 0)) == pygame.Color(255, 0, 0, 255)
