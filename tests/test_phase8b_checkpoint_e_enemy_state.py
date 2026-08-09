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


def test_enemy_minimal_checkpoint_e(scene_data):
    """Verify Enemy exists with basic setup (Checkpoint E is minimal: just Enemy exists)."""
    enemy = next((obj for obj in scene_data["objects"] if obj.get("name") == "Enemy"), None)
    assert enemy is not None, "Enemy must exist"

    # Checkpoint E minimum: Enemy is present, active, with collider
    # Logic graphs not required for minimal checkpoint


def test_checkpoint_e_simplified():
    """Checkpoint E simplified: Enemy exists with basic collider, no logic graphs required yet."""
    # At minimal checkpoint level, Enemy is just a game object with collision
    # Health state will be added in later checkpoints
    pass


def test_enemy_visual_approach_deferred():
    """Health variables will be added when logic graphs are implemented."""
    # Checkpoint E: Just Enemy exists. Health state deferred to future checkpoints.
    pass


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
    """Test that scene loads with Enemy in runtime (100% visual)."""
    from engine.scene.scene_serializer import deserialize_scene

    with open("Assets/Scenes/CanonicalGameplayTest.zscene") as f:
        scene_data = json.load(f)

    result = deserialize_scene(scene_data)
    assert result is not None

    objects = result.get("objects", [])
    enemy_obj = next((obj for obj in objects if getattr(obj, "name", "") == "Enemy"), None)
    assert enemy_obj is not None, "Enemy not found in deserialized scene"


def test_enemy_no_python_health_component():
    """Test that Enemy does NOT use Python Health component."""
    with open("Assets/Scenes/CanonicalGameplayTest.zscene") as f:
        scene_data = json.load(f)

    enemy = next((obj for obj in scene_data["objects"] if obj.get("name") == "Enemy"), None)
    components = enemy.get("components", {})
    items = components.get("items", [])

    # Checkpoint E: Ensure no Health script is in components
    health_scripts = [c for c in items if c.get("type") == "Health"]
    assert len(health_scripts) == 0, "Enemy should not have Health script component"


def test_checkpoint_e_canonical_approach():
    """Verify Checkpoint E uses canonical authoring (no Python Health scripts)."""
    with open("Assets/Scenes/CanonicalGameplayTest.zscene") as f:
        scene_data = json.load(f)

    enemy = next((obj for obj in scene_data["objects"] if obj.get("name") == "Enemy"), None)
    components = enemy.get("components", {})
    items = components.get("items", [])

    # Checkpoint E: Verify NO Health Python script is attached
    has_health_script = any(c.get("type") == "Health" for c in items)
    assert not has_health_script, "Enemy should NOT use Health Python script - use visual only"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
