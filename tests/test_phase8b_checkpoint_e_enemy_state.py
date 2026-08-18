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


def test_enemy_health_variables_in_graph(scene_data):
    """Verify EnemyHealth.zlogic defines health variables (100% visual state)."""
    logic_graph_path = Path("Assets/Logic/EnemyHealth.zlogic")
    with open(logic_graph_path) as f:
        graph_data = json.load(f)

    variables = graph_data.get("variables", {})
    assert "health" in variables, "health variable not defined"
    assert "max_health" in variables, "max_health variable not defined"

    # Verify defaults (100% visual, no scripts)
    assert variables["health"].get("default") == 100
    assert variables["max_health"].get("default") == 100


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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
