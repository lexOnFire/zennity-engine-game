import pytest
import pygame
from engine.assets.runtime_asset_manager import RuntimeAssetManager
from engine.core.services import EngineServices
from engine.core.lifecycle import ServiceScope, ServiceState


@pytest.fixture(autouse=True)
def init_pygame():
    pygame.init()
    yield
    pygame.quit()


def test_runtime_asset_manager_ref_counting():
    mgr = RuntimeAssetManager()
    assert mgr.scope == ServiceScope.ENGINE
    
    # Acquire & Release
    key = "image:Assets/Textures/player.png"
    mgr.acquire(key)
    assert mgr.get_ref_count(key) == 1
    
    mgr.acquire(key)
    assert mgr.get_ref_count(key) == 2
    
    current = mgr.release(key)
    assert current == 1
    assert mgr.get_ref_count(key) == 1
    
    mgr.release(key)
    assert mgr.get_ref_count(key) == 0


def test_runtime_asset_manager_unloading():
    mgr = RuntimeAssetManager()
    
    # Load image (acquire count = 1)
    img = mgr.get_image("non_existent_image.png")
    assert isinstance(img, pygame.Surface)
    key = "image:non_existent_image.png"
    assert mgr.get_ref_count(key) == 1
    
    # Unload unused should NOT unload while ref_count > 0
    unloaded = mgr.unload_unused_assets()
    assert unloaded == 0
    
    # Release reference
    mgr.release(key)
    assert mgr.get_ref_count(key) == 0
    
    # Unload unused should now clean it up
    unloaded = mgr.unload_unused_assets()
    assert unloaded == 1
