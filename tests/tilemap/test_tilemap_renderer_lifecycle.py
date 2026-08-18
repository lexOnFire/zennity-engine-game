"""Testes de ciclo de vida e instanciação de TilemapRenderer pelo ComponentRegistry (Pre-Phase 13 Sprint R1)."""
from __future__ import annotations

from unittest.mock import MagicMock
import pygame
import pytest

from engine.core.component_registry import component_registry
from engine.core.game_object import GameObject
from engine.tilemap.tilemap import TileLayer, TileMap, TilemapRenderer


def test_tilemap_renderer_instantiation_via_registry():
    """Valida que ComponentRegistry instancia TilemapRenderer sem argumentos obrigatórios."""
    comp = component_registry.create({"type": "TilemapRenderer"})

    assert isinstance(comp, TilemapRenderer)
    assert comp.tilemap is None


def test_tilemap_renderer_lifecycle_and_draw():
    """Valida que TilemapRenderer instanciado vazio pode receber um TileMap e executar draw()."""
    pygame.init()
    surface = pygame.Surface((320, 240))

    comp = component_registry.create({"type": "TilemapRenderer"})
    assert isinstance(comp, TilemapRenderer)

    # Associa a GameObject e TileMap posteriormente
    go = GameObject("MapEntity")
    go.add_component(comp)

    mock_tileset = MagicMock()
    mock_tileset.first_gid = 1
    mock_tileset.get_surface = MagicMock(return_value=pygame.Surface((16, 16)))

    tilemap = TileMap(tile_width=16, tile_height=16, map_width=5, map_height=5)
    tilemap.add_tileset(mock_tileset)
    layer = TileLayer(name="ground", width=5, height=5, data=[1] * 25)
    tilemap.add_layer(layer)

    comp.tilemap = tilemap

    # Desenha sem erros
    comp.draw(surface)
