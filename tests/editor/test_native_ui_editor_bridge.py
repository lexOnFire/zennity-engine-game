from __future__ import annotations

import pygame

from editor.runtime.native_ui import NativeUIRenderer, scene_item_to_ui, ui_to_scene_item


def _objects():
    return {
        "Canvas": {"name": "Canvas", "active": True, "ui": {"type": "canvas"}},
        "Title": {"name": "Title", "active": True, "ui": {"type": "text", "text": "Zennity", "x": 8, "y": 8}},
        "Play": {"name": "Play", "active": True, "ui": {"type": "button", "text": "Play", "x": 10, "y": 40, "width": 100, "height": 32, "target": "Player", "event": "start"}},
    }


def test_native_ui_scene_item_round_trip() -> None:
    source = {"type": "text", "text": "Vida", "x": 12, "y": 18, "font_size": 25}

    restored = scene_item_to_ui(ui_to_scene_item(source))

    assert restored is not None
    assert restored["type"] == "text"
    assert restored["text"] == "Vida"
    assert restored["x"] == 12
    assert restored["font_size"] == 25


def test_native_ui_draws_only_when_canvas_exists() -> None:
    renderer = NativeUIRenderer()
    surface = pygame.Surface((180, 90), pygame.SRCALPHA)
    before = pygame.image.tostring(surface, "RGBA")

    renderer.draw(_objects(), surface)

    assert pygame.image.tostring(surface, "RGBA") != before
    without_canvas = {key: value for key, value in _objects().items() if key != "Canvas"}
    assert renderer.components(without_canvas) == []


def test_native_ui_button_hit_test_keeps_script_event() -> None:
    renderer = NativeUIRenderer()

    clicked = renderer.button_at(_objects(), (30, 55))

    assert clicked is not None
    owner, button = clicked
    assert owner["name"] == "Play"
    assert button["target"] == "Player"
    assert button["event"] == "start"
