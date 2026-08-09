"""Phase 8B Checkpoint D: Camera Follow canonical tests."""
import json
from pathlib import Path

import pytest


@pytest.fixture
def canonical_scene_path():
    """Get path to CanonicalGameplayTest scene."""
    return Path("Assets/Scenes/CanonicalGameplayTest.zscene")


def test_scene_file_exists(canonical_scene_path):
    """Verify CanonicalGameplayTest.zscene exists."""
    assert canonical_scene_path.exists(), f"Scene not found: {canonical_scene_path}"


def test_scene_loads_valid_json(canonical_scene_path):
    """Verify scene is valid JSON."""
    with open(canonical_scene_path) as f:
        data = json.load(f)
    assert data is not None
    assert data.get("format_version") == 2
    assert data.get("scene_name") == "CanonicalGameplayTest"


def test_main_camera_exists():
    """Verify MainCamera object exists in scene."""
    with open("Assets/Scenes/CanonicalGameplayTest.zscene") as f:
        data = json.load(f)

    cameras = [obj for obj in data["objects"] if obj.get("name") == "MainCamera"]
    assert len(cameras) == 1, "MainCamera not found"


def test_player_object_exists():
    """Verify Player object exists in scene."""
    with open("Assets/Scenes/CanonicalGameplayTest.zscene") as f:
        data = json.load(f)

    players = [obj for obj in data["objects"] if obj.get("name") == "Player"]
    assert len(players) == 1, "Player not found"


def test_player_has_player_tag():
    """Verify Player object has 'Player' tag."""
    with open("Assets/Scenes/CanonicalGameplayTest.zscene") as f:
        data = json.load(f)

    player = next((obj for obj in data["objects"] if obj.get("name") == "Player"), None)
    assert player is not None, "Player object not found"
    assert player.get("tag") == "Player", f"Player tag is '{player.get('tag')}', expected 'Player'"


def test_main_camera_has_camera_component():
    """Verify MainCamera has Camera component."""
    with open("Assets/Scenes/CanonicalGameplayTest.zscene") as f:
        data = json.load(f)

    camera = next((obj for obj in data["objects"] if obj.get("name") == "MainCamera"), None)
    assert camera is not None, "MainCamera not found"

    components = camera.get("components", {})
    assert "camera" in components, "Camera component not found in MainCamera"


def test_main_camera_has_camera_follow_component():
    """Verify MainCamera has CameraFollow component."""
    with open("Assets/Scenes/CanonicalGameplayTest.zscene") as f:
        data = json.load(f)

    camera = next((obj for obj in data["objects"] if obj.get("name") == "MainCamera"), None)
    assert camera is not None, "MainCamera not found"

    components = camera.get("components", {})
    items = components.get("items", [])

    camera_follow_components = [c for c in items if c.get("type") == "CameraFollow"]
    assert len(camera_follow_components) == 1, "CameraFollow component not found"


def test_camera_follow_targets_player():
    """Verify CameraFollow component targets Player."""
    with open("Assets/Scenes/CanonicalGameplayTest.zscene") as f:
        data = json.load(f)

    camera = next((obj for obj in data["objects"] if obj.get("name") == "MainCamera"), None)
    components = camera.get("components", {})
    items = components.get("items", [])

    camera_follow = next((c for c in items if c.get("type") == "CameraFollow"), None)
    assert camera_follow is not None, "CameraFollow not found"
    assert camera_follow.get("target_tag") == "Player", \
        f"target_tag is '{camera_follow.get('target_tag')}', expected 'Player'"


def test_camera_follow_smoothing_configured():
    """Verify CameraFollow smoothing is set."""
    with open("Assets/Scenes/CanonicalGameplayTest.zscene") as f:
        data = json.load(f)

    camera = next((obj for obj in data["objects"] if obj.get("name") == "MainCamera"), None)
    components = camera.get("components", {})
    items = components.get("items", [])

    camera_follow = next((c for c in items if c.get("type") == "CameraFollow"), None)
    assert camera_follow is not None
    smoothing = camera_follow.get("smoothing", 0)
    assert smoothing > 0, f"Smoothing is {smoothing}, expected > 0"


def test_camera_follow_runtime_loading():
    """Test that scene loads with CameraFollow objects."""
    from engine.scene.scene_serializer import deserialize_scene

    with open("Assets/Scenes/CanonicalGameplayTest.zscene") as f:
        scene_data = json.load(f)

    # Deserialize returns dict with 'objects' key containing GameObject instances
    result = deserialize_scene(scene_data)
    assert result is not None

    # Check for objects key (the actual GameObjects)
    objects = result.get("objects", [])
    assert len(objects) >= 3, f"Expected at least 3 objects, got {len(objects)}"

    # Find camera object
    camera_obj = next((obj for obj in objects if getattr(obj, "name", "") == "MainCamera"), None)
    assert camera_obj is not None, "MainCamera not found in deserialized scene"


def test_camera_follow_component_canonical():
    """Verify CameraFollow component is canonical (registered in engine)."""
    # CameraFollow is registered via @ComponentRegistry.component decorator
    # in Assets/Scripts/camera_follow.py - just verify component definition exists
    camera_follow_path = Path("Assets/Scripts/camera_follow.py")
    assert camera_follow_path.exists(), "CameraFollow script not found"

    with open(camera_follow_path) as f:
        content = f.read()
    assert "ComponentRegistry.component" in content, "CameraFollow not registered as component"
    assert "class CameraFollow" in content, "CameraFollow class not defined"


def test_wall_object_exists():
    """Verify Wall object exists (collision test)."""
    with open("Assets/Scenes/CanonicalGameplayTest.zscene") as f:
        data = json.load(f)

    walls = [obj for obj in data["objects"] if obj.get("name") == "Wall"]
    assert len(walls) == 1, "Wall not found"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
