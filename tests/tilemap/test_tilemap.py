"""
tests/tilemap/test_tilemap.py
=================================================================
Testes para engine/tilemap/ (tileset.py + tilemap.py).

Estrategia:
  - pygame headless (SDL_VIDEODRIVER=dummy) via conftest.py
  - Tileset testado sem arquivo real: tiles injetados em _tiles/_meta
  - TileMap testado com Tileset stub (sem imagem)
  - draw() e bake() testados com pygame.Surface reais
  - TilemapRenderer testado com Camera2D.main = None

Nota sobre get_solid_rects_in_region:
  O algoritmo usa range(col_start, col_end+1) com col_end=ceil((x+w)/tw),
  portanto e CONSERVADOR: inclui tiles na borda da regiao. Os testes
  verificam que os rects esperados ESTAO presentes, sem exigir contagem
  exata quando a borda e ambigua.
"""
from __future__ import annotations

import pygame
import pytest
from unittest.mock import MagicMock


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


def rect_positions(rects):
    return {(r.x, r.y) for r in rects}


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
        assert "Tileset" in repr(ts)


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
    """
    Mapa 4x4 tiles de 16x16px.
    Tiles solidos: (col=0,row=0)->world(0,0)  e  (col=1,row=1)->world(16,16).
    Resto vazio (GID 0).

    IMPORTANTE: get_solid_rects_in_region e conservador — usa
    range(start, ceil(end)+1), portanto uma regiao de exatamente 1 tile
    pode incluir o tile vizinho. Os testes verificam PRESENCA dos rects
    esperados (in) e ausencia de rects fora da area esperada, sem exigir
    contagem exata em bordas ambiguas.
    """

    def _make_solid_map(self):
        tm = make_tilemap(tw=16, th=16, mw=4, mh=4)
        ts = make_tileset(first_gid=1, n_tiles=4, solid_gids=[1])
        tm.add_tileset(ts)
        data = [0] * 16
        data[0]     = 1   # col=0, row=0  -> world (0,0)
        data[1*4+1] = 1   # col=1, row=1  -> world (16,16)
        from engine.tilemap.tilemap import TileLayer
        tm.add_layer(TileLayer("collision", 4, 4, data))
        return tm

    def test_is_solid_at_solid_tile(self):
        assert self._make_solid_map().is_solid_at(0, 0) is True

    def test_is_solid_at_center_of_solid_tile(self):
        assert self._make_solid_map().is_solid_at(8, 8) is True

    def test_is_solid_at_empty_tile(self):
        assert self._make_solid_map().is_solid_at(32, 0) is False

    def test_is_solid_at_missing_layer(self):
        assert make_tilemap().is_solid_at(0, 0, layer_name="nope") is False

    def test_get_solid_rects_full_map_has_both(self):
        """Varrer o mapa inteiro devolve exatamente os 2 tiles solidos."""
        rects = self._make_solid_map().get_solid_rects_in_region(0, 0, 64, 64)
        pos = rect_positions(rects)
        assert (0, 0)   in pos
        assert (16, 16) in pos
        assert len(rects) == 2

    def test_get_solid_rects_top_left_tile_present(self):
        """Regiao centrada no tile (0,0) contem o rect (0,0)."""
        rects = self._make_solid_map().get_solid_rects_in_region(0, 0, 16, 16)
        assert (0, 0) in rect_positions(rects)

    def test_get_solid_rects_second_tile_present(self):
        """Regiao centrada no tile (1,1) contem o rect (16,16)."""
        rects = self._make_solid_map().get_solid_rects_in_region(16, 16, 16, 16)
        assert (16, 16) in rect_positions(rects)

    def test_get_solid_rects_empty_column(self):
        """Coluna 2 (world x=32) nao tem tiles solidos — lista vazia."""
        rects = self._make_solid_map().get_solid_rects_in_region(32, 0, 15, 64)
        assert rect_positions(rects) == set()

    def test_get_solid_rects_missing_layer(self):
        assert make_tilemap().get_solid_rects_in_region(
            0, 0, 64, 64, layer_name="nope"
        ) == []

    def test_solid_rect_dimensions(self):
        """Todos os rects devem ter exatamente 16x16px."""
        rects = self._make_solid_map().get_solid_rects_in_region(0, 0, 64, 64)
        for r in rects:
            assert r.width == 16 and r.height == 16

    def test_no_duplicate_rects(self):
        """Sem rects duplicados para o mesmo tile."""
        rects = self._make_solid_map().get_solid_rects_in_region(0, 0, 64, 64)
        assert len(rects) == len(set((r.x, r.y) for r in rects))


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
        tm.draw(pygame.Surface((64, 64)))

    def test_draw_no_crash_unbaked(self):
        self._make_drawable_map().draw(pygame.Surface((64, 64)))

    def test_draw_with_camera_offset(self):
        self._make_drawable_map().draw(pygame.Surface((64, 64)), cam_x=8.0, cam_y=8.0)

    def test_draw_invisible_layer_skipped(self):
        from engine.tilemap.tilemap import TileLayer
        tm = make_tilemap(tw=16, th=16, mw=2, mh=2)
        ts = make_tileset(first_gid=1, n_tiles=2)
        tm.add_tileset(ts)
        tm.add_layer(TileLayer("hidden", 2, 2, [1, 1, 1, 1], visible=False))
        screen = pygame.Surface((32, 32))
        screen.fill((0, 0, 0))
        tm.draw(screen)
        assert screen.get_at((0, 0))[:3] == (0, 0, 0)

    def test_draw_debug_no_crash(self):
        from engine.tilemap.tilemap import TileLayer
        tm = make_tilemap(tw=16, th=16, mw=4, mh=4)
        ts = make_tileset(first_gid=1, n_tiles=4, solid_gids=[1])
        tm.add_tileset(ts)
        tm.add_layer(TileLayer("collision", 4, 4, [1] * 16))
        tm.draw_debug(pygame.Surface((64, 64)))

    def test_draw_debug_missing_layer_no_crash(self):
        make_tilemap().draw_debug(pygame.Surface((64, 64)), layer_name="nope")


# ==========================================================================
# TilemapRenderer
# ==========================================================================

class TestTilemapRenderer:
    def test_init_stores_tilemap(self):
        from engine.tilemap.tilemap import TilemapRenderer
        tm = make_tilemap()
        assert TilemapRenderer(tm).tilemap is tm

    def test_draw_no_crash_no_camera(self):
        from engine.tilemap.tilemap import TilemapRenderer
        from engine.graphics.camera2d import Camera2D
        tm = make_tilemap(tw=16, th=16, mw=2, mh=2)
        ts = make_tileset(first_gid=1, n_tiles=2)
        tm.add_tileset(ts)
        tm.add_layer(make_layer("ground", width=2, height=2, data=[1, 2, 1, 2]))
        tr = TilemapRenderer(tm)
        tr.game_object = MagicMock()
        original = Camera2D.main
        Camera2D.main = None
        try:
            tr.draw(pygame.Surface((32, 32)))
        finally:
            Camera2D.main = original

    def test_draw_no_game_object_no_crash(self):
        from engine.tilemap.tilemap import TilemapRenderer
        tr = TilemapRenderer(make_tilemap())
        tr.game_object = None
        tr.draw(pygame.Surface((32, 32)))
