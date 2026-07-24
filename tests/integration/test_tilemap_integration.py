import pytest
import pygame
from engine.graphics.tilemap import Tileset, Tilemap, TilemapRenderer
from engine.core.game_object import GameObject
from engine.runtime.runtime_scene import RuntimeScene

@pytest.fixture
def runtime_scene():
    from engine.core.scene import Scene
    dummy_scene = Scene("TestEditorScene")
    scene = RuntimeScene(dummy_scene)
    yield scene

def test_tilemap_integration(runtime_scene):
    # Create Tilemap object
    obj = GameObject("Map")
    tm = Tilemap(width=5, height=5, tile_size=32)
    tm.set_tile(0, 2, 2, 1)
    obj.add_component(tm)
    
    # Create Tileset and Renderer
    surf = pygame.Surface((64, 64))
    tileset = Tileset(surf, 32)
    renderer = TilemapRenderer(tileset=tileset)
    obj.add_component(renderer)
    
    # Add to scene
    runtime_scene.add_game_object(obj)
    
    # Start runtime
    runtime_scene.start_runtime()
    
    # Simulate an update
    runtime_scene.update(0.016)
    
    # Fake draw (requires a screen surface)
    screen = pygame.Surface((800, 600))
    # We just want to ensure it doesn't crash on drawing
    renderer.draw(screen)
    
    runtime_scene.stop_runtime()
