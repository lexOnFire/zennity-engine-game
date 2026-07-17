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
