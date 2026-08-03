from __future__ import annotations

import ast
from pathlib import Path

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
    from unittest.mock import MagicMock
    from conftest import SurfaceProxy
    renderer = NativeUIRenderer()
    surface = SurfaceProxy()
    surface.blit = MagicMock()

    renderer.draw(_objects(), surface)

    assert surface.blit.call_count > 0
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


def test_delete_object_does_not_access_removed_script_ui() -> None:
    source = Path("editor/scene_object_controller.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    delete_method = next(
        node for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == "delete"
    )
    attributes = {
        node.attr for node in ast.walk(delete_method)
        if isinstance(node, ast.Attribute)
    }

    assert "script_selector" not in attributes
    assert "create_script_button" not in attributes
    assert "edit_script_button" not in attributes
    assert "script_containers" not in attributes


def test_native_ui_clear_caches_releases_fonts_and_surfaces() -> None:
    renderer = NativeUIRenderer()
    renderer._fonts[(12, False)] = object()
    renderer._images["sprite.png"] = object()

    renderer.clear_caches()

    assert renderer._fonts == {}
    assert renderer._images == {}


def test_native_ui_anchors_hud_inside_resized_viewport() -> None:
    renderer = NativeUIRenderer()
    screen = pygame.Surface((800, 450))

    wave = renderer._rect({
        "width": 180, "height": 40, "anchor": "top_right",
        "margin_x": 40, "margin_y": 30,
    }, screen)
    health = renderer._rect({
        "width": 220, "height": 20, "anchor": "bottom_left",
        "margin_x": 40, "margin_y": 60,
    }, screen)

    assert wave.topleft == (580, 30)
    assert health.topleft == (40, 370)
