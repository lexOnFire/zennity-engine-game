"""Compatibilidade pública do Tilemap legado durante o sunset para v2.0."""

import pytest
import pygame
from engine.graphics.tilemap import Tileset, Tilemap, TilemapRenderer
from engine.core.game_object import GameObject

@pytest.fixture
def dummy_surface():
    surf = pygame.Surface((128, 128))
    surf.fill((255, 0, 0))
    yield surf

def test_tileset_initialization(dummy_surface):
    tileset = Tileset(dummy_surface, tile_size=32)
    assert tileset.tile_size == 32
    # 128/32 = 4 cols, 128/32 = 4 rows -> 16 tiles
    # IDs 1 to 16
    assert tileset.get_tile(1) is not None
    assert tileset.get_tile(16) is not None
    assert tileset.get_tile(17) is None
    assert tileset.get_tile(0) is None

def test_tilemap_component():
    tm = Tilemap(width=5, height=5, tile_size=16)
    
    assert tm.width == 5
    assert tm.height == 5
    assert tm.tile_size == 16
    
    # Check default layer
    assert len(tm.layers) == 1
    
    # Set tile
    tm.set_tile(0, 2, 2, 1)
    assert tm.get_tile(0, 2, 2) == 1
    
    # Set out of bounds
    tm.set_tile(0, 10, 10, 2)
    assert tm.get_tile(0, 10, 10) == 0
    
    # Add layer
    tm.add_layer()
    assert len(tm.layers) == 2
    tm.set_tile(1, 1, 1, 3)
    assert tm.get_tile(1, 1, 1) == 3
    
    # Remove tile
    tm.set_tile(1, 1, 1, 0)
    assert tm.get_tile(1, 1, 1) == 0

def test_tilemap_serialization():
    tm = Tilemap(width=10, height=10, tile_size=32)
    tm.set_tile(0, 1, 1, 5)
    
    data = tm.serialize()
    assert data["width"] == 10
    assert data["height"] == 10
    assert data["tile_size"] == 32
    assert len(data["layers"]) == 1
    assert data["layers"][0]["1,1"] == 5
    
    tm2 = Tilemap()
    tm2.deserialize(data)
    assert tm2.width == 10
    assert tm2.height == 10
    assert tm2.tile_size == 32
    assert tm2.get_tile(0, 1, 1) == 5

def test_tilemap_renderer():
    obj = GameObject("TilemapObj")
    tm = Tilemap(width=2, height=2, tile_size=32)
    tm.set_tile(0, 0, 0, 1)
    obj.add_component(tm)
    
    tr = TilemapRenderer(tileset=None)
    obj.add_component(tr)
    
    assert tr.game_object == obj
    assert obj.get_component(Tilemap) == tm


def test_tilemap_renderer_round_trips_tileset_through_scene_serialization():
    """BUG FIX: o Tileset é um objeto e Component.serialize() só reflete
    primitivos, então um TilemapRenderer salvo em .zscene perdia a textura e
    voltava invisível ao recarregar -- silenciosamente, sem erro."""
    from engine.core.component_registry import component_registry

    renderer = TilemapRenderer(
        texture_path="Assets/Sprites/MyPlatformer/tile_ground.png", tile_size=32
    )
    assert renderer.tileset is not None, "tileset deve ser carregado a partir do path"

    data = renderer.serialize()
    assert data["properties"]["texture_path"].endswith("tile_ground.png")
    assert data["properties"]["tile_size"] == 32

    restored = component_registry.create(data)
    assert restored.texture_path == renderer.texture_path
    assert restored.tileset is not None, "tileset deve ser reconstruído no load"


def test_tilemap_renderer_survives_missing_texture():
    """Textura ausente não pode derrubar o carregamento da cena inteira."""
    from engine.core.component_registry import component_registry

    restored = component_registry.create({
        "type": "TilemapRenderer",
        "enabled": True,
        "properties": {"texture_path": "Assets/inexistente.png", "tile_size": 32},
    })
    assert restored.tileset is None
