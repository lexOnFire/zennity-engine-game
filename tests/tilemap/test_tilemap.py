"""
tests/tilemap/test_tilemap.py
────────────────────────────────────────────────────────────────
Testes unitários de engine/tilemap/tilemap.py.

Estratégia de isolamento:
  - pygame é stubado via sys.modules (Surface, Rect, draw.rect,
    SRCALPHA). Nenhuma janela, nenhum init real.
  - Tileset é um MagicMock com first_gid, get_surface e is_solid
    controláveis por teste.
  - Camera2D é stubado em engine.graphics.camera2d para os testes
    de TilemapRenderer sem importar o módulo real.
  - TileLayer e TileMap são testados de forma unitária pura.
"""
from __future__ import annotations

import sys
from types import ModuleType
from unittest.mock import MagicMock, patch

import pytest

# ── stub pygame ──────────────────────────────────────────────────────────────

class _FakeSurface:
    SRCALPHA = 0x00010000
    def __init__(self, size=(32, 32), flags=0):
        self._size = tuple(size)
        self.blit      = MagicMock()
        self.fill      = MagicMock()
        self.set_alpha = MagicMock()
        self.copy      = MagicMock(return_value=self)
        self.get_size  = MagicMock(return_value=self._size)


class _FakeRect:
    def __init__(self, x, y, w, h):
        self.x, self.y, self.w, self.h = x, y, w, h
    def __eq__(self, other):
        return (self.x, self.y, self.w, self.h) == (other.x, other.y, other.w, other.h)


if "pygame" not in sys.modules:
    _pg             = ModuleType("pygame")
    _pg.Surface     = _FakeSurface
    _pg.Rect        = _FakeRect
    _pg.SRCALPHA    = _FakeSurface.SRCALPHA
    _draw           = ModuleType("pygame.draw")
    _draw.rect      = MagicMock()
    _pg.draw        = _draw
    sys.modules["pygame"]      = _pg
    sys.modules["pygame.draw"] = _draw
else:
    _pg   = sys.modules["pygame"]
    _draw = sys.modules.get("pygame.draw", _pg.draw)

# stub tileset para não precisar de arquivos de imagem
class _StubTileset:
    def __init__(self, first_gid=1, solid_gids=None, surfaces=None):
        self.first_gid  = first_gid
        self._solid     = set(solid_gids or [])
        self._surfaces  = surfaces or {}
    def is_solid(self, gid): return gid in self._solid
    def get_surface(self, gid): return self._surfaces.get(gid)

if "engine.tilemap.tileset" not in sys.modules:
    _ts_mod = ModuleType("engine.tilemap.tileset")
    _ts_mod.Tileset = _StubTileset
    _ts_mod.TileData = object
    sys.modules["engine.tilemap.tileset"] = _ts_mod

from engine.tilemap.tilemap import TileLayer, TileMap, TilemapRenderer  # noqa: E402


# ── helpers ────────────────────────────────────────────────────────────────

def _layer(w=4, h=4, data=None, name="ground", z=0, visible=True, opacity=1.0):
    d = data if data is not None else [0] * (w * h)
    return TileLayer(name=name, width=w, height=h, data=d, visible=visible, opacity=opacity, z_index=z)


def _map(tw=16, th=16, mw=4, mh=4):
    return TileMap(tile_width=tw, tile_height=th, map_width=mw, map_height=mh)


def _tileset(first_gid=1, solid_gids=None, surfaces=None):
    return _StubTileset(first_gid=first_gid, solid_gids=solid_gids, surfaces=surfaces)


# ────────────────────────────────────────────────────────────────────────────
class TestTileLayerInit:
    def test_name_stored(self):
        l = _layer(name="bg")
        assert l.name == "bg"

    def test_dimensions(self):
        l = _layer(w=8, h=6)
        assert l.width == 8 and l.height == 6

    def test_data_stored(self):
        data = [1, 0, 2, 0]
        l = _layer(w=2, h=2, data=data)
        assert l.data == data

    def test_visible_default_true(self):
        assert _layer().visible is True

    def test_opacity_clamped_above_one(self):
        l = TileLayer("x", 1, 1, [0], opacity=5.0)
        assert l.opacity == pytest.approx(1.0)

    def test_opacity_clamped_below_zero(self):
        l = TileLayer("x", 1, 1, [0], opacity=-1.0)
        assert l.opacity == pytest.approx(0.0)

    def test_z_index_stored(self):
        l = _layer(z=3)
        assert l.z_index == 3


class TestTileLayerGetSetGid:
    def test_get_gid_center(self):
        data = [0, 0, 0, 5]
        l = _layer(w=2, h=2, data=data)
        assert l.get_gid(1, 1) == 5

    def test_get_gid_out_of_bounds_returns_zero(self):
        l = _layer(w=2, h=2)
        assert l.get_gid(10, 10) == 0

    def test_get_gid_negative_returns_zero(self):
        l = _layer(w=2, h=2)
        assert l.get_gid(-1, 0) == 0

    def test_set_gid_updates_data(self):
        l = _layer(w=2, h=2)
        l.set_gid(1, 0, 7)
        assert l.get_gid(1, 0) == 7

    def test_set_gid_out_of_bounds_no_crash(self):
        l = _layer(w=2, h=2)
        l.set_gid(99, 99, 1)   # não deve lançar

    def test_set_gid_row_major_order(self):
        l = _layer(w=3, h=2)
        l.set_gid(2, 1, 99)   # linha 1, coluna 2 → índice 5
        assert l.data[5] == 99


# ────────────────────────────────────────────────────────────────────────────
class TestTileMapInit:
    def test_tile_dimensions(self):
        m = _map(tw=32, th=32)
        assert m.tile_width == 32 and m.tile_height == 32

    def test_map_dimensions(self):
        m = _map(mw=10, mh=8)
        assert m.map_width == 10 and m.map_height == 8

    def test_pixel_width(self):
        m = _map(tw=16, mw=10)
        assert m.pixel_width == 160

    def test_pixel_height(self):
        m = _map(th=16, mh=8)
        assert m.pixel_height == 128

    def test_bake_dirty_on_init(self):
        assert _map()._bake_dirty is True

    def test_no_layers_on_init(self):
        assert _map()._layers == []


class TestTileMapTilesets:
    def test_add_tileset_registers(self):
        m = _map()
        ts = _tileset(first_gid=1)
        m.add_tileset(ts)
        assert 1 in m._tilesets

    def test_resolve_tileset_exact(self):
        m = _map()
        ts = _tileset(first_gid=1)
        m.add_tileset(ts)
        assert m._resolve_tileset(1) is ts

    def test_resolve_tileset_best_fit(self):
        """GID 5 pertence ao tileset com first_gid=4 (mais próximo abaixo)."""
        m = _map()
        ts1 = _tileset(first_gid=1)
        ts2 = _tileset(first_gid=4)
        m.add_tileset(ts1)
        m.add_tileset(ts2)
        assert m._resolve_tileset(5) is ts2

    def test_resolve_tileset_none_when_no_match(self):
        m = _map()
        assert m._resolve_tileset(5) is None

    def test_get_tile_surface_zero_returns_none(self):
        m = _map()
        assert m.get_tile_surface(0) is None

    def test_get_tile_surface_returns_surface(self):
        surf = _FakeSurface()
        ts = _tileset(first_gid=1, surfaces={1: surf})
        m = _map()
        m.add_tileset(ts)
        assert m.get_tile_surface(1) is surf

    def test_add_tileset_marks_bake_dirty(self):
        m = _map()
        m._bake_dirty = False
        m.add_tileset(_tileset())
        assert m._bake_dirty is True


class TestTileMapLayers:
    def test_add_layer_stored(self):
        m = _map()
        l = _layer(name="bg")
        m.add_layer(l)
        assert l in m._layers

    def test_layers_sorted_by_z_index(self):
        m = _map()
        l1 = _layer(name="a", z=2)
        l2 = _layer(name="b", z=0)
        l3 = _layer(name="c", z=1)
        m.add_layer(l1); m.add_layer(l2); m.add_layer(l3)
        assert [l.name for l in m._layers] == ["b", "c", "a"]

    def test_get_layer_by_name(self):
        m = _map()
        l = _layer(name="fg")
        m.add_layer(l)
        assert m.get_layer("fg") is l

    def test_get_layer_missing_returns_none(self):
        m = _map()
        assert m.get_layer("nope") is None

    def test_remove_layer(self):
        m = _map()
        m.add_layer(_layer(name="x"))
        m.remove_layer("x")
        assert m.get_layer("x") is None

    def test_remove_layer_marks_dirty(self):
        m = _map()
        m.add_layer(_layer(name="x"))
        m._bake_dirty = False
        m.remove_layer("x")
        assert m._bake_dirty is True


class TestCoordinates:
    def test_world_to_tile_origin(self):
        m = _map(tw=16, th=16)
        assert m.world_to_tile(0, 0) == (0, 0)

    def test_world_to_tile_second_tile(self):
        m = _map(tw=16, th=16)
        assert m.world_to_tile(16, 0) == (1, 0)

    def test_world_to_tile_partial(self):
        """15.9 px ainda é tile 0."""
        m = _map(tw=16, th=16)
        assert m.world_to_tile(15.9, 0) == (0, 0)

    def test_tile_to_world(self):
        m = _map(tw=16, th=16)
        assert m.tile_to_world(2, 3) == (32.0, 48.0)

    def test_tile_to_world_origin(self):
        m = _map(tw=16, th=16)
        assert m.tile_to_world(0, 0) == (0.0, 0.0)

    def test_roundtrip_tile_world_tile(self):
        m = _map(tw=32, th=32)
        col, row = 3, 5
        wx, wy = m.tile_to_world(col, row)
        assert m.world_to_tile(wx, wy) == (col, row)


class TestIsSolidAt:
    def _setup(self):
        m = _map(tw=16, th=16, mw=4, mh=4)
        data = [0] * 16
        data[0] = 1   # tile (0,0) é solid
        layer = _layer(w=4, h=4, data=data, name="collision")
        ts = _tileset(first_gid=1, solid_gids={1})
        m.add_tileset(ts)
        m.add_layer(layer)
        return m

    def test_solid_tile_returns_true(self):
        m = self._setup()
        assert m.is_solid_at(0.0, 0.0) is True

    def test_empty_tile_returns_false(self):
        m = self._setup()
        assert m.is_solid_at(16.0, 0.0) is False

    def test_no_collision_layer_returns_false(self):
        m = _map()
        assert m.is_solid_at(0.0, 0.0) is False

    def test_custom_layer_name(self):
        m = _map(tw=16, th=16, mw=2, mh=2)
        data = [1, 0, 0, 0]
        layer = _layer(w=2, h=2, data=data, name="walls")
        ts = _tileset(first_gid=1, solid_gids={1})
        m.add_tileset(ts)
        m.add_layer(layer)
        assert m.is_solid_at(0.0, 0.0, layer_name="walls") is True


class TestGetSolidRectsInRegion:
    def _setup(self):
        m = _map(tw=16, th=16, mw=4, mh=4)
        data = [0] * 16
        data[0] = 1    # (0,0)
        data[1] = 1    # (1,0)
        layer = _layer(w=4, h=4, data=data, name="collision")
        ts = _tileset(first_gid=1, solid_gids={1})
        m.add_tileset(ts)
        m.add_layer(layer)
        return m

    def test_returns_rects_for_solid_tiles(self):
        m = self._setup()
        rects = m.get_solid_rects_in_region(0, 0, 32, 16)
        assert len(rects) == 2

    def test_no_layer_returns_empty(self):
        m = _map()
        assert m.get_solid_rects_in_region(0, 0, 100, 100) == []

    def test_region_outside_solid_returns_empty(self):
        m = self._setup()
        rects = m.get_solid_rects_in_region(48, 48, 16, 16)
        assert len(rects) == 0

    def test_rect_position_correct(self):
        m = self._setup()
        rects = m.get_solid_rects_in_region(0, 0, 16, 16)
        assert len(rects) == 1
        assert rects[0].x == 0 and rects[0].y == 0


class TestBakeAndInvalidate:
    def test_bake_clears_dirty_flag(self):
        m = _map(tw=16, th=16, mw=2, mh=2)
        m.bake()
        assert m._bake_dirty is False

    def test_bake_stores_surface(self):
        m = _map(tw=16, th=16, mw=2, mh=2)
        m.bake()
        assert m._baked is not None

    def test_invalidate_sets_dirty(self):
        m = _map()
        m.bake()
        m.invalidate_bake()
        assert m._bake_dirty is True

    def test_invalidate_clears_baked(self):
        m = _map()
        m.bake()
        m.invalidate_bake()
        assert m._baked is None


class TestDraw:
    def test_draw_uses_baked_when_available(self):
        m = _map(tw=16, th=16, mw=2, mh=2)
        fake_baked = _FakeSurface((32, 32))
        m._baked = fake_baked
        m._bake_dirty = False
        screen = _FakeSurface((640, 480))
        m.draw(screen)
        screen.blit.assert_called_once()

    def test_draw_fallback_when_dirty(self):
        """Sem bake, draw deve tentar chamar _draw_layer (sem crash)."""
        m = _map(tw=16, th=16, mw=2, mh=2)
        m._bake_dirty = True
        screen = _FakeSurface((640, 480))
        # sem camadas, nenhum blit é esperado
        m.draw(screen)
        screen.blit.assert_not_called()

    def test_repr_contains_dimensions(self):
        m = _map(mw=10, mh=8, tw=16, th=16)
        r = repr(m)
        assert "10x8" in r


class TestTilemapRenderer:
    def test_draw_calls_tilemap_draw(self):
        tilemap = MagicMock()
        renderer = TilemapRenderer(tilemap)
        go = MagicMock()
        renderer.game_object = go
        screen = _FakeSurface((640, 480))
        screen.get_width  = MagicMock(return_value=640)
        screen.get_height = MagicMock(return_value=480)

        with patch("engine.graphics.camera2d.Camera2D") as MockCam:
            MockCam.main = None
            renderer.draw(screen)

        tilemap.draw.assert_called_once()

    def test_draw_no_game_object_no_crash(self):
        tilemap = MagicMock()
        renderer = TilemapRenderer(tilemap)
        renderer.game_object = None
        screen = _FakeSurface((640, 480))
        renderer.draw(screen)   # não deve lançar
        tilemap.draw.assert_not_called()
