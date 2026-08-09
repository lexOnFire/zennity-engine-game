"""Phase 8B Checkpoint E: Canonical Enemy + Health State tests."""
import json
from pathlib import Path

import pytest


@pytest.fixture
def scene_path():
    return Path("Assets/Scenes/CanonicalGameplayTest.zscene")


@pytest.fixture
def scene_data(scene_path):
    with open(scene_path) as f:
        return json.load(f)


def test_scene_loads(scene_path):
    """Verify scene file exists and is valid JSON."""
    assert scene_path.exists()
    with open(scene_path) as f:
        data = json.load(f)
    assert data.get("scene_name") == "CanonicalGameplayTest"


def test_enemy_created_canonically(scene_data):
    """Verify Enemy object exists in scene."""
    enemies = [obj for obj in scene_data["objects"] if obj.get("name") == "Enemy"]
    assert len(enemies) == 1, "Enemy object not found"
    enemy = enemies[0]
    assert enemy.get("id") == "enemy_01"
    assert enemy.get("active") is True


def test_enemy_has_correct_tag(scene_data):
    """Verify Enemy has 'Enemy' tag."""
    enemy = next((obj for obj in scene_data["objects"] if obj.get("name") == "Enemy"), None)
    assert enemy is not None
    assert enemy.get("tag") == "Enemy", f"Enemy tag is '{enemy.get('tag')}', expected 'Enemy'"


def test_enemy_has_sprite_renderer(scene_data):
    """Verify Enemy has visual rendering properties."""
    enemy = next((obj for obj in scene_data["objects"] if obj.get("name") == "Enemy"), None)
    assert enemy is not None
    visual = enemy.get("visual", {})
    assert visual.get("color") == [255, 0, 0], "Enemy color should be red"


def test_enemy_has_collider(scene_data):
    """Verify Enemy has BoxCollider component."""
    enemy = next((obj for obj in scene_data["objects"] if obj.get("name") == "Enemy"), None)
    assert enemy is not None
    components = enemy.get("components", {})
    collider = components.get("collider")
    assert collider is not None
    assert collider.get("type") == "box"
    assert collider.get("width") == 36.0
    assert collider.get("height") == 36.0


def test_enemy_has_health_component(scene_data):
    """Verify Enemy has Health component."""
    enemy = next((obj for obj in scene_data["objects"] if obj.get("name") == "Enemy"), None)
    assert enemy is not None
    components = enemy.get("components", {})
    items = components.get("items", [])
    health_components = [c for c in items if c.get("type") == "Health"]
    assert len(health_components) == 1, "Health component not found"


def test_enemy_health_default_100(scene_data):
    """Verify Enemy health defaults to 100."""
    enemy = next((obj for obj in scene_data["objects"] if obj.get("name") == "Enemy"), None)
    components = enemy.get("components", {})
    items = components.get("items", [])
    health = next((c for c in items if c.get("type") == "Health"), None)
    assert health is not None
    assert health.get("hp") == 100, f"Enemy HP is {health.get('hp')}, expected 100"


def test_enemy_max_health_100(scene_data):
    """Verify Enemy max_health is 100."""
    enemy = next((obj for obj in scene_data["objects"] if obj.get("name") == "Enemy"), None)
    components = enemy.get("components", {})
    items = components.get("items", [])
    health = next((c for c in items if c.get("type") == "Health"), None)
    assert health is not None
    assert health.get("max_hp") == 100, f"Enemy max_hp is {health.get('max_hp')}, expected 100"


def test_enemy_not_dead_initially(scene_data):
    """Verify Enemy is not marked as dead initially."""
    enemy = next((obj for obj in scene_data["objects"] if obj.get("name") == "Enemy"), None)
    components = enemy.get("components", {})
    items = components.get("items", [])
    health = next((c for c in items if c.get("type") == "Health"), None)
    assert health is not None
    assert health.get("dead") is False, "Enemy should not be marked dead initially"


def test_all_required_objects_present(scene_data):
    """Verify scene has all required objects: MainCamera, Player, Wall, Enemy."""
    names = [obj.get("name") for obj in scene_data["objects"]]
    assert "MainCamera" in names
    assert "Player" in names
    assert "Wall" in names
    assert "Enemy" in names
    assert len(names) == 4, f"Expected 4 objects, got {len(names)}: {names}"


@pytest.mark.runtime
def test_enemy_runtime_loading():
    """Test that scene loads with Enemy in runtime."""
    from engine.scene.scene_serializer import deserialize_scene

    with open("Assets/Scenes/CanonicalGameplayTest.zscene") as f:
        scene_data = json.load(f)

    result = deserialize_scene(scene_data)
    assert result is not None

    objects = result.get("objects", [])
    enemy_obj = next((obj for obj in objects if getattr(obj, "name", "") == "Enemy"), None)
    assert enemy_obj is not None, "Enemy not found in deserialized scene"


def test_enemy_health_component_accessible():
    """Test that Health component data is correct in scene."""
    with open("Assets/Scenes/CanonicalGameplayTest.zscene") as f:
        scene_data = json.load(f)

    enemy = next((obj for obj in scene_data["objects"] if obj.get("name") == "Enemy"), None)
    components = enemy.get("components", {})
    items = components.get("items", [])
    health = next((c for c in items if c.get("type") == "Health"), None)

    assert health is not None, "Health component not found"
    assert health.get("hp") == 100, "Health component hp incorrect"
    assert health.get("max_hp") == 100, "Health component max_hp incorrect"


def test_health_component_canonical():
    """Verify Health is a canonical registered component."""
    health_path = Path("Assets/Scripts/health.py")
    assert health_path.exists(), "Health component not found"

    with open(health_path) as f:
        content = f.read()
    assert "ComponentRegistry.component" in content
    assert "class Health" in content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
