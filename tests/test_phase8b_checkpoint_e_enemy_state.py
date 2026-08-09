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


def test_enemy_has_logic_graph(scene_data):
    """Verify Enemy has Logic Graph component (100% visual state management)."""
    enemy = next((obj for obj in scene_data["objects"] if obj.get("name") == "Enemy"), None)
    assert enemy is not None
    components = enemy.get("components", {})
    items = components.get("items", [])
    logic_graphs = [c for c in items if c.get("type") == "LogicGraph"]
    assert len(logic_graphs) == 1, "Logic Graph component not found"

    logic_graph = logic_graphs[0]
    assert logic_graph.get("graph_path") == "Assets/Logic/EnemyHealth.zlogic", \
        "Logic Graph path incorrect"


def test_enemy_health_logic_graph_exists():
    """Verify EnemyHealth.zlogic exists (100% visual, no Python scripts)."""
    logic_graph_path = Path("Assets/Logic/EnemyHealth.zlogic")
    assert logic_graph_path.exists(), "EnemyHealth.zlogic not found"

    with open(logic_graph_path) as f:
        data = json.load(f)

    assert data.get("graph_name") == "EnemyHealth"
    assert "variables" in data


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


def test_enemy_logic_graph_accessible():
    """Test that Logic Graph (visual state) is accessible on Enemy."""
    with open("Assets/Scenes/CanonicalGameplayTest.zscene") as f:
        scene_data = json.load(f)

    enemy = next((obj for obj in scene_data["objects"] if obj.get("name") == "Enemy"), None)
    components = enemy.get("components", {})
    items = components.get("items", [])
    logic_graph = next((c for c in items if c.get("type") == "LogicGraph"), None)

    assert logic_graph is not None, "LogicGraph component not found"
    assert logic_graph.get("graph_path") == "Assets/Logic/EnemyHealth.zlogic"


def test_checkpoint_e_visual_approach():
    """Verify Checkpoint E uses 100% visual approach (no Python state scripts)."""
    # 1. Scene uses LogicGraph, not Health component script
    with open("Assets/Scenes/CanonicalGameplayTest.zscene") as f:
        scene_data = json.load(f)

    enemy = next((obj for obj in scene_data["objects"] if obj.get("name") == "Enemy"), None)
    components = enemy.get("components", {})
    items = components.get("items", [])

    has_logic_graph = any(c.get("type") == "LogicGraph" for c in items)
    has_health_script = any(c.get("type") == "Health" for c in items)

    assert has_logic_graph, "Enemy should use LogicGraph for state"
    assert not has_health_script, "Enemy should NOT use Health script component"

    # 2. EnemyHealth.zlogic defines state variables
    logic_graph_path = Path("Assets/Logic/EnemyHealth.zlogic")
    with open(logic_graph_path) as f:
        graph_data = json.load(f)

    variables = graph_data.get("variables", {})
    assert "health" in variables
    assert "max_health" in variables


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
