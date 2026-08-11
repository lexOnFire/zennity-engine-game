"""Phase 8B — Checkpoint B: Canonical Microscene Authoring Test Suite.

Validates that Assets/Scenes/CanonicalGameplayTest.zscene created via the canonical
EditorScenePersistence pipeline saves, reopens, and preserves all object hierarchy
and component attachments (Transform, SpriteRenderer, RigidBody2D, BoxCollider2D,
Camera, LogicGraph) flawlessly.
"""
from pathlib import Path
import pytest
from editor.scene_persistence import EditorScenePersistence
from engine.logic.graph_asset import load_logic_graph
from engine.logic.graph_validator import validate_logic_graph


@pytest.fixture
def canonical_scene_data(tmp_path):
    # Temporary project root: this fixture saves the scene, and with Path.cwd()
    # it overwrote the repository's Assets/Scenes/CanonicalGameplayTest.zscene
    # on every run.  Round-tripping through a temp directory tests the same
    # persistence contract.
    project_root = tmp_path
    persistence = EditorScenePersistence(project_root)
    scene_path = project_root / "Assets" / "Scenes" / "CanonicalGameplayTest.zscene"
    scene_path.parent.mkdir(parents=True, exist_ok=True)

    # The scene references Assets/Logic/PlayerMovement.zlogic and two tests below
    # assert that the reference resolves and compiles.  Copy the repository's
    # real graph into the temporary project so those assertions stay meaningful
    # while nothing is written back to the repository.
    source_logic = Path(__file__).resolve().parents[1] / "Assets" / "Logic" / "PlayerMovement.zlogic"
    target_logic = project_root / "Assets" / "Logic" / "PlayerMovement.zlogic"
    target_logic.parent.mkdir(parents=True, exist_ok=True)
    if source_logic.is_file():
        target_logic.write_bytes(source_logic.read_bytes())

    camera_snapshot = {
        "id": "main_camera",
        "name": "MainCamera",
        "active": True,
        "x": 0.0,
        "y": 0.0,
        "w": 32.0,
        "h": 32.0,
        "rotation": 0.0,
        "color": [88, 117, 255],
        "renderer_enabled": True,
        "material": "Default_Material",
        "texture": "",
        "render_layer": "Default",
        "sort_order": 0,
        "camera": {
            "active": True,
            "zoom": 1.0,
            "clear_color": [0.05, 0.05, 0.1, 1.0],
            "viewport_rect": [0.0, 0.0, 1.0, 1.0],
            "priority": 0
        },
        "components": {
            "camera": {
                "active": True,
                "zoom": 1.0,
                "clear_color": [0.05, 0.05, 0.1, 1.0],
                "viewport_rect": [0.0, 0.0, 1.0, 1.0],
                "priority": 0
            }
        }
    }

    player_snapshot = {
        "id": "player",
        "name": "Player",
        "active": True,
        "x": 0.0,
        "y": 0.0,
        "w": 48.0,
        "h": 48.0,
        "rotation": 0.0,
        "color": [0, 200, 255],
        "renderer_enabled": True,
        "material": "Default_Material",
        "texture": "Assets/Sprites/Player/idle_1.png",
        "render_layer": "Default",
        "sort_order": 0,
        "rigidbody": {
            "enabled": True,
            "body_type": "dynamic",
            "gravity_scale": 0.0,
            "mass": 1.0,
            "fixed_rotation": True
        },
        "collider": {
            "enabled": True,
            "type": "box",
            "width": 48.0,
            "height": 48.0,
            "is_trigger": False
        },
        "logic_assets": [
            "Assets/Logic/PlayerMovement.zlogic"
        ],
        "components": {
            "rigidbody": {
                "enabled": True,
                "body_type": "dynamic",
                "gravity_scale": 0.0,
                "mass": 1.0,
                "fixed_rotation": True
            },
            "collider": {
                "enabled": True,
                "type": "box",
                "width": 48.0,
                "height": 48.0,
                "is_trigger": False
            },
            "items": [
                {
                    "type": "LogicGraph",
                    "graph_path": "Assets/Logic/PlayerMovement.zlogic"
                }
            ]
        }
    }

    wall_snapshot = {
        "id": "wall",
        "name": "Wall",
        "active": True,
        "x": 200.0,
        "y": 0.0,
        "w": 32.0,
        "h": 128.0,
        "rotation": 0.0,
        "color": [120, 120, 120],
        "renderer_enabled": True,
        "material": "Default_Material",
        "texture": "",
        "render_layer": "Default",
        "sort_order": 0,
        "collider": {
            "enabled": True,
            "type": "box",
            "width": 32.0,
            "height": 128.0,
            "is_trigger": False
        },
        "components": {
            "collider": {
                "enabled": True,
                "type": "box",
                "width": 32.0,
                "height": 128.0,
                "is_trigger": False
            }
        }
    }

    snapshots = [camera_snapshot, player_snapshot, wall_snapshot]
    persistence.save(scene_path, snapshots, None)
    payload, loaded_snapshots, typed = persistence.load(scene_path)
    by_name = {s["name"]: s for s in loaded_snapshots}
    return {
        "project_root": project_root,
        "scene_path": scene_path,
        "persistence": persistence,
        "payload": payload,
        "snapshots": loaded_snapshots,
        "by_name": by_name,
    }


def test_scene_created_canonically(canonical_scene_data):
    assert canonical_scene_data["scene_path"].exists()


def test_scene_save_load_roundtrip(canonical_scene_data):
    assert len(canonical_scene_data["snapshots"]) == 3


def test_maincamera_exists(canonical_scene_data):
    assert "MainCamera" in canonical_scene_data["by_name"]


def test_player_exists(canonical_scene_data):
    assert "Player" in canonical_scene_data["by_name"]


def test_wall_exists(canonical_scene_data):
    assert "Wall" in canonical_scene_data["by_name"]


def test_player_has_transform(canonical_scene_data):
    player = canonical_scene_data["by_name"]["Player"]
    assert "x" in player and "y" in player and "w" in player and "h" in player


def test_player_has_sprite_renderer(canonical_scene_data):
    player = canonical_scene_data["by_name"]["Player"]
    assert player.get("renderer_enabled") is True
    assert "color" in player


def test_player_has_rigidbody(canonical_scene_data):
    player = canonical_scene_data["by_name"]["Player"]
    assert player.get("rigidbody") is not None or "rigidbody" in player.get("components", {})


def test_player_has_collider(canonical_scene_data):
    player = canonical_scene_data["by_name"]["Player"]
    assert player.get("collider") is not None or "collider" in player.get("components", {})


def test_player_has_logic_attachment(canonical_scene_data):
    player = canonical_scene_data["by_name"]["Player"]
    assert "Assets/Logic/PlayerMovement.zlogic" in player.get("logic_assets", [])


def test_wall_has_collider(canonical_scene_data):
    wall = canonical_scene_data["by_name"]["Wall"]
    assert wall.get("collider") is not None or "collider" in wall.get("components", {})


def test_camera_has_camera_component(canonical_scene_data):
    cam = canonical_scene_data["by_name"]["MainCamera"]
    assert cam.get("camera") is not None or "camera" in cam.get("components", {})


def test_player_logic_asset_exists(canonical_scene_data):
    logic_path = canonical_scene_data["project_root"] / "Assets" / "Logic" / "PlayerMovement.zlogic"
    assert logic_path.exists()


def test_player_logic_compiles_zero_errors(canonical_scene_data):
    logic_path = canonical_scene_data["project_root"] / "Assets" / "Logic" / "PlayerMovement.zlogic"
    graph = load_logic_graph(logic_path)
    issues = validate_logic_graph(graph)
    errors = [i for i in issues if i.get("level") == "error"]
    warnings = [i for i in issues if i.get("level") == "warning"]
    assert len(errors) == 0
    assert len(warnings) == 0
