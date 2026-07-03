"""
tests/tilemap/test_tilemap.py
=================================================================
Testes para engine/tilemap/ (tileset.py + tilemap.py).

Estrategia:
  - pygame headless (SDL_VIDEODRIVER=dummy) via conftest.py
  - Tileset testado sem arquivo real: metodos de slice ignorados;
    tiles injetados diretamente em _tiles/_meta para testar API
  - TileMap testado com Tileset stub (sem imagem)
  - draw() e bake() testados com pygame.Surface reais
  - TilemapRenderer testado com Camera2D.main = None
"""
from __future__ import annotations

import pygame
import pytest
from unittest.mock import MagicMock, patch


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def make_surface(w=16, h=16, color=(100, 200, 50)):
    s = pygame.Surface((w, h))
    s.fill(color)
    return s


def make_tileset(first_gid=1, n_tiles=4, solid_gids=()):
    """Tileset stub sem arquivo — tiles injetados diretamente."""
    from engine.tilemap.tileset import Tileset, TileData
    ts = Tileset.__new__(Tileset)
    ts.image_path  = "fake.png"
    ts.tile_width  = 16
    ts.tile_height = 16
    ts.spacing     = 0
    ts.margin      = 0
    ts.first_gid   = first_gid
    ts._sheet  = None
    ts._tiles  = {first_gid + i: make_surface() for i in range(n_tiles)}
    ts._meta   = {}
    ts._loaded = True
    for gid in solid_gids:
        ts._meta[gid] = TileData(tile_id=gid, solid=True)
    return ts


def make_layer(name="ground", width=4, height=4, data=None, z_index=0):
    from engine.tilemap.tilemap import TileLayer
    if data is None:
        data = [1] * (width * height)
    return TileLayer(name, width, height, data, z_index=z_index)


def make_tilemap(tw=16, th=16, mw=4, mh=4):
    from engine.tilemap.tilemap import TileMap
    return TileMap(tw, th, mw, mh)


# ==========================================================================
# TileData
# ==========================================================================

class TestTileData:
    def test_defaults(self):
        from engine.tilemap.tileset import TileData
        td = TileData(tile_id=5)
        assert td.solid is False
        assert td.one_way is False
        assert td.damage == 0
        assert td.custom == {}

    def test_solid_flag(self):
        from engine.tilemap.tileset import TileData
        assert TileData(tile_id=1, solid=True).solid is True

    def test_one_way_flag(self):
        from engine.tilemap.tileset import TileData
        assert TileData(tile_id=2, one_way=True).one_way is True

    def test_damage(self):
        from engine.tilemap.tileset import TileData
        assert TileData(tile_id=3, damage=10).damage == 10

    def test_custom_dict(self):
        from engine.tilemap.tileset import TileData
        td = TileData(tile_id=4, custom={"type": "lava"})
        assert td.custom["type"] == "lava"


# ==========================================================================
# Tileset (sem arquivo)
# ==========================================================================

class TestTileset:
    def test_get_surface_known_gid(self):
        ts = make_tileset(first_gid=1, n_tiles=3)
        assert ts.get_surface(1) is not None
        assert ts.get_surface(3) is not None

    def test_get_surface_unknown_gid(self):
        ts = make_tileset(first_gid=1, n_tiles=2)
        assert ts.get_surface(99) is None

    def test_get_surface_gid_zero(self):
        ts = make_tileset()
        assert ts.get_surface(0) is None

    def test_tile_count(self):
        ts = make_tileset(n_tiles=6)
        assert ts.tile_count == 6

    def test_tile_size(self):
        ts = make_tileset()
        assert ts.tile_size == (16, 16)

    def test_is_solid_true(self):
        ts = make_tileset(solid_gids=[2])
        assert ts.is_solid(2) is True

    def test_is_solid_false_unregistered(self):
        ts = make_tileset()
        assert ts.is_solid(1) is False

    def test_is_solid_false_explicit(self):
        from engine.tilemap.tileset import TileData
        ts = make_tileset()
        ts.set_tile_data(1, TileData(tile_id=1, solid=False))
        assert ts.is_solid(1) is False

    def test_is_one_way(self):
        from engine.tilemap.tileset import TileData
        ts = make_tileset()
        ts.set_tile_data(1, TileData(tile_id=1, one_way=True))
        assert ts.is_one_way(1) is True

    def test_is_one_way_false_unregistered(self):
        ts = make_tileset()
        assert ts.is_one_way(99) is False

    def test_set_and_get_tile_data(self):
        from engine.tilemap.tileset import TileData
        ts = make_tileset()
        td = TileData(tile_id=2, damage=5)
        ts.set_tile_data(2, td)
        assert ts.get_tile_data(2) is td

    def test_get_tile_data_missing(self):
        ts = make_tileset()
        assert ts.get_tile_data(99) is None

    def test_repr(self):
        ts = make_tileset()
        r = repr(ts)
        assert "Tileset" in r


# ==========================================================================
# TileLayer
# ==========================================================================

class TestTileLayer:
    def test_get_gid_valid(self):
        layer = make_layer(width=3, height=3, data=list(range(1, 10)))
        assert layer.get_gid(0, 0) == 1
        assert layer.get_gid(2, 2) == 9

    def test_get_gid_out_of_bounds(self):
        layer = make_layer()
        assert layer.get_gid(-1, 0) == 0
        assert layer.get_gid(0, -1) == 0
        assert layer.get_gid(100, 0) == 0
        assert layer.get_gid(0, 100) == 0

    def test_set_gid(self):
        layer = make_layer(width=2, height=2, data=[0, 0, 0, 0])
        layer.set_gid(1, 1, 7)
        assert layer.get_gid(1, 1) == 7

    def test_set_gid_out_of_bounds_no_crash(self):
        layer = make_layer()
        layer.set_gid(100, 100, 5)

    def test_opacity_clamped_low(self):
        from engine.tilemap.tilemap import TileLayer
        assert TileLayer("l", 1, 1, [0], opacity=-1.0).opacity == 0.0

    def test_opacity_clamped_high(self):
        from engine.tilemap.tilemap import TileLayer
        assert TileLayer("l", 1, 1, [0], opacity=2.0).opacity == 1.0

    def test_visible_default(self):
        assert make_layer().visible is True

    def test_z_index_stored(self):
        assert make_layer(z_index=5).z_index == 5


# ==========================================================================
# TileMap — estrutura
# ==========================================================================

class TestTileMapStructure:
    def test_pixel_dimensions(self):
        tm = make_tilemap(tw=16, th=16, mw=10, mh=8)
        assert tm.pixel_width  == 160
        assert tm.pixel_height == 128

    def test_world_to_tile(self):
        tm = make_tilemap()
        assert tm.world_to_tile(0, 0)   == (0, 0)
        assert tm.world_to_tile(16, 32) == (1, 2)
        assert tm.world_to_tile(31, 31) == (1, 1)

    def test_tile_to_world(self):
        tm = make_tilemap()
        assert tm.tile_to_world(0, 0) == (0.0, 0.0)
        assert tm.tile_to_world(2, 3) == (32.0, 48.0)

    def test_add_and_get_layer(self):
        tm = make_tilemap()
        tm.add_layer(make_layer("ground"))
        assert tm.get_layer("ground") is not None

    def test_get_layer_missing(self):
        tm = make_tilemap()
        assert tm.get_layer("nope") is None

    def test_remove_layer(self):
        tm = make_tilemap()
        tm.add_layer(make_layer("ground"))
        tm.remove_layer("ground")
        assert tm.get_layer("ground") is None

    def test_layers_sorted_by_z_index(self):
        tm = make_tilemap()
        tm.add_layer(make_layer("top",    z_index=10))
        tm.add_layer(make_layer("bottom", z_index=0))
        tm.add_layer(make_layer("mid",    z_index=5))
        names = [l.name for l in tm._layers]
        assert names == ["bottom", "mid", "top"]

    def test_add_tileset_and_resolve(self):
        tm = make_tilemap()
        ts = make_tileset(first_gid=1)
        tm.add_tileset(ts)
        assert tm._resolve_tileset(1) is ts
        assert tm._resolve_tileset(4) is ts

    def test_resolve_tileset_none_for_zero(self):
        tm = make_tilemap()
        assert tm._resolve_tileset(0) is None

    def test_resolve_tileset_multiple(self):
        """GID 10 deve resolver para o tileset com first_gid=9, nao o de first_gid=1."""
        tm = make_tilemap()
        ts1 = make_tileset(first_gid=1)
        ts2 = make_tileset(first_gid=9)
        tm.add_tileset(ts1)
        tm.add_tileset(ts2)
        assert tm._resolve_tileset(10) is ts2

    def test_get_tile_surface_valid(self):
        tm = make_tilemap()
        ts = make_tileset(first_gid=1, n_tiles=4)
        tm.add_tileset(ts)
        assert tm.get_tile_surface(1) is not None

    def test_get_tile_surface_zero(self):
        tm = make_tilemap()
        assert tm.get_tile_surface(0) is None

    def test_repr(self):
        tm = make_tilemap(mw=10, mh=8)
        assert "10x8" in repr(tm)


# ==========================================================================
# TileMap — colisao
# ==========================================================================

class TestTileMapCollision:
    def _make_solid_map(self):
        """4x4 mapa, layer 'collision', tiles 1-4 (GID 1 = solid).
        Tiles solidos:
          (col=0, row=0) -> world (0,0)
          (col=1, row=1) -> world (16,16)
        """
        tm = make_tilemap(tw=16, th=16, mw=4, mh=4)
        ts = make_tileset(first_gid=1, n_tiles=4, solid_gids=[1])
        tm.add_tileset(ts)
        data = [0] * 16
        data[0]     = 1   # col=0, row=0
        data[1*4+1] = 1   # col=1, row=1
        from engine.tilemap.tilemap import TileLayer
        tm.add_layer(TileLayer("collision", 4, 4, data))
        return tm

    def test_is_solid_at_solid_tile(self):
        tm = self._make_solid_map()
        assert tm.is_solid_at(0, 0) is True

    def test_is_solid_at_empty_tile(self):
        tm = self._make_solid_map()
        assert tm.is_solid_at(32, 0) is False

    def test_is_solid_at_missing_layer(self):
        tm = make_tilemap()
        assert tm.is_solid_at(0, 0, layer_name="nope") is False

    def test_get_solid_rects_finds_both_tiles(self):
        """Regiao que cobre o mapa inteiro retorna os 2 tiles solidos."""
        tm = self._make_solid_map()
        rects = tm.get_solid_rects_in_region(0, 0, 64, 64)
        assert len(rects) == 2

    def test_get_solid_rects_empty_region(self):
        """Regiao sem tiles solidos retorna lista vazia."""
        tm = self._make_solid_map()
        # col=2, row=0 -> world x=32, sem tile solido ali
        rects = tm.get_solid_rects_in_region(32, 0, 16, 16)
        assert rects == []

    def test_get_solid_rects_missing_layer(self):
        tm = make_tilemap()
        assert tm.get_solid_rects_in_region(0, 0, 64, 64, layer_name="nope") == []

    def test_solid_rect_correct_position(self):
        """Regiao (0,0,15,15) cobre apenas o tile (col=0,row=0) — 1 rect com pos (0,0)."""
        tm = self._make_solid_map()
        # Usar w=15/h=15 garante que math.ceil(15/16)=1 — apenas col/row 0
        rects = tm.get_solid_rects_in_region(0, 0, 15, 15)
        assert len(rects) == 1
        assert rects[0].x == 0 and rects[0].y == 0
        assert rects[0].width == 16 and rects[0].height == 16

    def test_solid_rect_second_tile_position(self):
        """Regiao (16,16,15,15) cobre apenas o tile (col=1,row=1) — pos (16,16)."""
        tm = self._make_solid_map()
        rects = tm.get_solid_rects_in_region(16, 16, 15, 15)
        assert len(rects) == 1
        assert rects[0].x == 16 and rects[0].y == 16


# ==========================================================================
# TileMap — bake e draw
# ==========================================================================

class TestTileMapDraw:
    def _make_drawable_map(self):
        tm = make_tilemap(tw=16, th=16, mw=4, mh=4)
        ts = make_tileset(first_gid=1, n_tiles=4)
        tm.add_tileset(ts)
        tm.add_layer(make_layer("ground", width=4, height=4,
                                data=[1, 2, 3, 4] * 4))
        return tm

    def test_bake_creates_surface(self):
        tm = self._make_drawable_map()
        tm.bake()
        assert tm._baked is not None
        assert isinstance(tm._baked, pygame.Surface)

    def test_bake_clears_dirty(self):
        tm = self._make_drawable_map()
        tm.bake()
        assert tm._bake_dirty is False

    def test_invalidate_bake(self):
        tm = self._make_drawable_map()
        tm.bake()
        tm.invalidate_bake()
        assert tm._baked is None
        assert tm._bake_dirty is True

    def test_draw_no_crash_baked(self):
        tm = self._make_drawable_map()
        tm.bake()
        screen = pygame.Surface((64, 64))
        tm.draw(screen)

    def test_draw_no_crash_unbaked(self):
        tm = self._make_drawable_map()
        screen = pygame.Surface((64, 64))
        tm.draw(screen)

    def test_draw_with_camera_offset(self):
        tm = self._make_drawable_map()
        screen = pygame.Surface((64, 64))
        tm.draw(screen, cam_x=8.0, cam_y=8.0)

    def test_draw_invisible_layer_skipped(self):
        from engine.tilemap.tilemap import TileLayer
        tm = make_tilemap(tw=16, th=16, mw=2, mh=2)
        ts = make_tileset(first_gid=1, n_tiles=2)
        tm.add_tileset(ts)
        layer = TileLayer("hidden", 2, 2, [1, 1, 1, 1], visible=False)
        tm.add_layer(layer)
        screen = pygame.Surface((32, 32))
        screen.fill((0, 0, 0))
        tm.draw(screen)
        assert screen.get_at((0, 0))[:3] == (0, 0, 0)

    def test_draw_debug_no_crash(self):
        tm = make_tilemap(tw=16, th=16, mw=4, mh=4)
        ts = make_tileset(first_gid=1, n_tiles=4, solid_gids=[1])
        tm.add_tileset(ts)
        from engine.tilemap.tilemap import TileLayer
        tm.add_layer(TileLayer("collision", 4, 4, [1] * 16))
        screen = pygame.Surface((64, 64))
        tm.draw_debug(screen)

    def test_draw_debug_missing_layer_no_crash(self):
        tm = make_tilemap()
        screen = pygame.Surface((64, 64))
        tm.draw_debug(screen, layer_name="nope")


# ==========================================================================
# TilemapRenderer
# ==========================================================================

class TestTilemapRenderer:
    def test_init_stores_tilemap(self):
        from engine.tilemap.tilemap import TilemapRenderer, TileMap
        tm = make_tilemap()
        tr = TilemapRenderer(tm)
        assert tr.tilemap is tm

    def test_draw_no_crash_no_camera(self):
        """Com Camera2D.main = None, draw() nao deve crashar."""
        from engine.tilemap.tilemap import TilemapRenderer
        from engine.graphics.camera2d import Camera2D

        tm = make_tilemap(tw=16, th=16, mw=2, mh=2)
        ts = make_tileset(first_gid=1, n_tiles=2)
        tm.add_tileset(ts)
        tm.add_layer(make_layer("ground", width=2, height=2, data=[1, 2, 1, 2]))

        tr = TilemapRenderer(tm)
        go = MagicMock()
        tr.game_object = go

        original = Camera2D.main
        Camera2D.main = None
        try:
            screen = pygame.Surface((32, 32))
            tr.draw(screen)
        finally:
            Camera2D.main = original

    def test_draw_no_game_object_no_crash(self):
        """game_object=None nao deve crashar."""
        from engine.tilemap.tilemap import TilemapRenderer
        tm = make_tilemap()
        tr = TilemapRenderer(tm)
        tr.game_object = None
        screen = pygame.Surface((32, 32))
        tr.draw(screen)
