"""
tests/graphics/test_renderer.py
────────────────────────────────────────────────────────────────
Testes unitários de engine/graphics/renderer.py (SpriteRenderer).

Estratégia de isolamento:
  - pygame, pygame.transform e engine.graphics.camera são preparados
    antes do import.
  - pygame.transform.flip/scale são mockados apenas durante cada teste,
    evitando vazamento para outros testes.
  - _FakeSurface rastreia blit, fill, get_width/height para verificar
    chamadas sem renderização real.
"""
from __future__ import annotations

import sys
from types import ModuleType
from unittest.mock import MagicMock

import numpy as np
import pytest

# ── stub pygame ──────────────────────────────────────────────────────────────

class _FakeSurface:
    SRCALPHA = 0x00010000
    def __init__(self, size=(32, 32), flags=0):
        self._w, self._h = size
        self.blit           = MagicMock()
        self.fill           = MagicMock()
        self.get_width      = MagicMock(return_value=self._w)
        self.get_height     = MagicMock(return_value=self._h)
        self.convert_alpha  = MagicMock(return_value=self)
        self.convert        = MagicMock(return_value=self)


def _make_surface(w=32, h=32):
    s = _FakeSurface((w, h))
    s.get_width  = MagicMock(return_value=w)
    s.get_height = MagicMock(return_value=h)
    return s


if "pygame" not in sys.modules:
    _pg              = ModuleType("pygame")
    _pg.Surface      = _FakeSurface
    _pg.SRCALPHA     = _FakeSurface.SRCALPHA
    _transform       = ModuleType("pygame.transform")
    _pg.transform    = _transform
    sys.modules["pygame"]           = _pg
    sys.modules["pygame.transform"] = _transform
else:
    _pg        = sys.modules["pygame"]
    _transform = sys.modules.get("pygame.transform", getattr(_pg, "transform", None))
    if _transform is None:
        _transform = ModuleType("pygame.transform")
        _pg.transform = _transform
        sys.modules["pygame.transform"] = _transform

# stub Camera para não depender do módulo real
if "engine.graphics.camera" not in sys.modules:
    _cam_mod = ModuleType("engine.graphics.camera")
    class _StubCamera:
        _active = None
    _cam_mod.Camera = _StubCamera
    sys.modules["engine.graphics.camera"] = _cam_mod
else:
    _cam_mod = sys.modules["engine.graphics.camera"]
    _StubCamera = _cam_mod.Camera

from engine.graphics.renderer import SpriteRenderer  # noqa: E402


# ── helpers ────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def reset_camera(monkeypatch):
    flip_mock = MagicMock(side_effect=lambda s, fx, fy: s)
    scale_mock = MagicMock(side_effect=lambda s, size: s)
    monkeypatch.setattr(_transform, "flip", flip_mock, raising=False)
    monkeypatch.setattr(_transform, "scale", scale_mock, raising=False)
    monkeypatch.setattr(_pg, "transform", _transform, raising=False)

    _StubCamera._active = None
    yield
    _StubCamera._active = None


def _make_go(x=0.0, y=0.0):
    go = MagicMock()
    go.transform.get_world_position = MagicMock(return_value=np.array([x, y]))
    return go


def _renderer(surface=None, w=32, h=32, **kw):
    surf = surface or _make_surface(w, h)
    r = SpriteRenderer(surface=surf, **kw)
    return r


class TestInit:
    def test_defaults_visible(self):
        r = _renderer()
        assert r.visible is True

    def test_defaults_layer_zero(self):
        r = _renderer()
        assert r.layer == 0

    def test_defaults_flip_x_false(self):
        r = _renderer()
        assert r.flip_x is False

    def test_defaults_flip_y_false(self):
        r = _renderer()
        assert r.flip_y is False

    def test_surface_provided_is_stored(self):
        surf = _make_surface(64, 64)
        r = SpriteRenderer(surface=surf)
        assert r.surface is surf

    def test_no_surface_creates_placeholder(self):
        r = SpriteRenderer(width=48, height=48, color=(255, 0, 0))
        assert r._surface is not None

    def test_width_and_height_from_surface(self):
        surf = _make_surface(64, 32)
        r = SpriteRenderer(surface=surf)
        assert r._width == 64
        assert r._height == 32

    def test_custom_layer(self):
        r = _renderer(layer=5)
        assert r.layer == 5


class TestSurfaceProperty:
    def test_surface_getter(self):
        surf = _make_surface()
        r = SpriteRenderer(surface=surf)
        assert r.surface is surf

    def test_surface_setter_updates_surface(self):
        r = _renderer()
        new_surf = _make_surface(64, 64)
        r.surface = new_surf
        assert r.surface is new_surf

    def test_surface_setter_updates_width(self):
        r = _renderer(w=32)
        new_surf = _make_surface(128, 64)
        r.surface = new_surf
        assert r._width == 128

    def test_surface_setter_updates_height(self):
        r = _renderer(h=32)
        new_surf = _make_surface(64, 96)
        r.surface = new_surf
        assert r._height == 96

    def test_set_color_calls_fill(self):
        surf = _make_surface()
        r = SpriteRenderer(surface=surf)
        r.set_color((0, 255, 0))
        surf.fill.assert_called_once_with((0, 255, 0))


class TestDrawNoCam:
    """draw() sem câmera ativa: coordenadas de mundo direto."""

    def test_draw_calls_screen_blit(self):
        r = _renderer()
        r.game_object = _make_go(50.0, 50.0)
        screen = _make_surface(640, 480)
        r.draw(screen)
        screen.blit.assert_called_once()

    def test_draw_invisible_no_blit(self):
        r = _renderer(visible=False)
        r.game_object = _make_go()
        screen = _make_surface()
        r.draw(screen)
        screen.blit.assert_not_called()

    def test_draw_no_game_object_no_blit(self):
        r = _renderer()
        r.game_object = None
        screen = _make_surface()
        r.draw(screen)
        screen.blit.assert_not_called()

    def test_draw_position_centered_on_world(self):
        r = _renderer(w=32, h=32)
        r.game_object = _make_go(100.0, 80.0)
        screen = _make_surface(640, 480)
        r.draw(screen)
        args = screen.blit.call_args[0]
        _, pos = args
        assert pos == (100 - 16, 80 - 16)

    def test_draw_no_flip_not_called_when_both_false(self):
        r = _renderer(flip_x=False, flip_y=False)
        r.game_object = _make_go()
        r.draw(_make_surface())
        _transform.flip.assert_not_called()

    def test_draw_flip_x_calls_transform(self):
        r = _renderer(flip_x=True)
        r.game_object = _make_go()
        r.draw(_make_surface())
        _transform.flip.assert_called_once()
        args = _transform.flip.call_args[0]
        assert args[1] is True
        assert args[2] is False

    def test_draw_flip_y_calls_transform(self):
        r = _renderer(flip_y=True)
        r.game_object = _make_go()
        r.draw(_make_surface())
        _transform.flip.assert_called_once()
        args = _transform.flip.call_args[0]
        assert args[2] is True


class TestDrawWithCam:
    """draw() com câmera ativa: usa world_to_screen e zoom."""

    def _active_cam(self, sx=100.0, sy=80.0, zoom=1.0):
        cam = MagicMock()
        cam.world_to_screen = MagicMock(return_value=(sx, sy))
        cam.zoom = zoom
        _StubCamera._active = cam
        return cam

    def test_draw_uses_camera_world_to_screen(self):
        cam = self._active_cam(sx=200.0, sy=150.0)
        r = _renderer()
        r.game_object = _make_go(50.0, 30.0)
        screen = _make_surface(640, 480)
        r.draw(screen)
        cam.world_to_screen.assert_called_once_with(50.0, 30.0)

    def test_draw_position_centered_on_screen(self):
        self._active_cam(sx=300.0, sy=200.0, zoom=1.0)
        r = _renderer(w=32, h=32)
        r.game_object = _make_go()
        screen = _make_surface(640, 480)
        r.draw(screen)
        args = screen.blit.call_args[0]
        _, pos = args
        assert pos == (300 - 16, 200 - 16)

    def test_draw_zoom_calls_scale(self):
        self._active_cam(zoom=2.0)
        r = _renderer(w=32, h=32)
        r.game_object = _make_go()
        r.draw(_make_surface(640, 480))
        _transform.scale.assert_called_once()

    def test_draw_zoom_one_no_scale(self):
        self._active_cam(zoom=1.0)
        r = _renderer()
        r.game_object = _make_go()
        r.draw(_make_surface(640, 480))
        _transform.scale.assert_not_called()

    def test_draw_zoom_scales_dimensions(self):
        zoom = 3.0
        self._active_cam(zoom=zoom)
        r = _renderer(w=32, h=32)
        r.game_object = _make_go()
        r.draw(_make_surface(640, 480))
        call_args = _transform.scale.call_args[0]
        new_size = call_args[1]
        assert new_size == (32 * 3, 32 * 3)

    def test_draw_invisible_with_cam_no_blit(self):
        self._active_cam()
        r = _renderer(visible=False)
        r.game_object = _make_go()
        screen = _make_surface(640, 480)
        r.draw(screen)
        screen.blit.assert_not_called()

    def test_draw_flip_with_cam_calls_transform(self):
        self._active_cam()
        r = _renderer(flip_x=True)
        r.game_object = _make_go()
        r.draw(_make_surface(640, 480))
        _transform.flip.assert_called_once()

    def test_draw_zoom_minimum_one_pixel(self):
        self._active_cam(zoom=0.001)
        r = _renderer(w=32, h=32)
        r.game_object = _make_go()
        r.draw(_make_surface(640, 480))
        call_args = _transform.scale.call_args[0]
        new_size = call_args[1]
        assert new_size[0] >= 1
        assert new_size[1] >= 1
