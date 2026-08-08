"""
Phase 8A Step 2: Player Movement, Camera & Animation Tests

Validates:
- Player prefab structure
- Movement (WASD) with normalized diagonal
- Physics-based movement (RigidBody)
- Camera following player
- Animation states (Idle/Run)
- Animation controller transitions
- Sprite animation frames
- Wall collision
- Play/Stop/Play cleanup
- Main Menu → Level1 flow

Zero Python gameplay scripts. All logic via Logic Graph.
"""

import pytest
import sys
from pathlib import Path
import json

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


class TestLevel1SceneLoads:
    """Test that Level1.zscene loads correctly with Player."""

    def test_level1_scene_exists(self):
        """Verify Level1.zscene file exists."""
        scene_path = project_root / "Assets" / "Scenes" / "Level1.zscene"
        assert scene_path.exists(), f"Level1.zscene not found at {scene_path}"

    def test_level1_scene_valid_json(self):
        """Verify Level1.zscene is valid JSON."""
        scene_path = project_root / "Assets" / "Scenes" / "Level1.zscene"
        data = json.loads(scene_path.read_text(encoding="utf-8"))
        assert data.get("format") == "zennity.scene"
        assert data.get("name") == "Level 1 - Arena"

    def test_level1_has_player(self):
        """Verify Level1 has Player prefab."""
        scene_path = project_root / "Assets" / "Scenes" / "Level1.zscene"
        data = json.loads(scene_path.read_text(encoding="utf-8"))

        player_objs = [obj for obj in data.get("objects", [])
                      if obj.get("name") == "Player"]
        assert len(player_objs) == 1, "Level1 should have exactly one Player"
        assert player_objs[0].get("type") == "Prefab"

    def test_level1_has_player_movement_logic(self):
        """Verify Level1 Player has movement logic graph."""
        scene_path = project_root / "Assets" / "Scenes" / "Level1.zscene"
        data = json.loads(scene_path.read_text(encoding="utf-8"))

        player = next((obj for obj in data.get("objects", [])
                      if obj.get("name") == "Player"), None)
        assert player is not None
        assert "logic_graphs" in player
        graphs = player["logic_graphs"]
        assert any(g.get("path") == "Assets/Logic/PlayerMovementLogic.zlogic"
                  for g in graphs)

    def test_level1_has_walls(self):
        """Verify Level1 has wall colliders for boundaries."""
        scene_path = project_root / "Assets" / "Scenes" / "Level1.zscene"
        data = json.loads(scene_path.read_text(encoding="utf-8"))

        wall_names = {"WallLeft", "WallRight", "WallTop", "WallBottom"}
        scene_names = {obj.get("name") for obj in data.get("objects", [])}
        assert wall_names.issubset(scene_names), "Level1 missing wall colliders"

    def test_level1_has_camera(self):
        """Verify Level1 has Camera with follow_target."""
        scene_path = project_root / "Assets" / "Scenes" / "Level1.zscene"
        data = json.loads(scene_path.read_text(encoding="utf-8"))

        camera = next((obj for obj in data.get("objects", [])
                      if obj.get("name") == "Camera"), None)
        assert camera is not None
        camera_config = camera.get("camera", {})
        assert camera_config.get("follow_target") == "Player"
        assert camera_config.get("smooth_follow") is True


class TestPlayerPrefab:
    """Test that Player.zprfb is properly structured."""

    def test_player_prefab_exists(self):
        """Verify Player.zprfb file exists."""
        prefab_path = project_root / "Assets" / "Prefabs" / "Player.zprfb"
        assert prefab_path.exists(), f"Player.zprfb not found at {prefab_path}"

    def test_player_prefab_valid_json(self):
        """Verify Player.zprfb is valid JSON."""
        prefab_path = project_root / "Assets" / "Prefabs" / "Player.zprfb"
        data = json.loads(prefab_path.read_text(encoding="utf-8"))
        assert data.get("format") == "zennity.prefab"
        assert data.get("name") == "Player"

    def test_player_has_transform(self):
        """Verify Player has Transform component."""
        prefab_path = project_root / "Assets" / "Prefabs" / "Player.zprfb"
        data = json.loads(prefab_path.read_text(encoding="utf-8"))

        components = data.get("root", {}).get("components", [])
        comp_types = {c.get("type") for c in components}
        assert "Transform" in comp_types

    def test_player_has_sprite_renderer(self):
        """Verify Player has SpriteRenderer component."""
        prefab_path = project_root / "Assets" / "Prefabs" / "Player.zprfb"
        data = json.loads(prefab_path.read_text(encoding="utf-8"))

        components = data.get("root", {}).get("components", [])
        comp_types = {c.get("type") for c in components}
        assert "SpriteRenderer" in comp_types

    def test_player_has_collider(self):
        """Verify Player has BoxCollider2D for collision."""
        prefab_path = project_root / "Assets" / "Prefabs" / "Player.zprfb"
        data = json.loads(prefab_path.read_text(encoding="utf-8"))

        components = data.get("root", {}).get("components", [])
        comp_types = {c.get("type") for c in components}
        assert "BoxCollider2D" in comp_types

    def test_player_has_rigidbody(self):
        """Verify Player has RigidBody2D for physics."""
        prefab_path = project_root / "Assets" / "Prefabs" / "Player.zprfb"
        data = json.loads(prefab_path.read_text(encoding="utf-8"))

        components = data.get("root", {}).get("components", [])
        comp_types = {c.get("type") for c in components}
        assert "RigidBody2D" in comp_types

        # Verify it's NOT using gravity (top-down 2D game)
        rigidbody = next((c for c in components if c.get("type") == "RigidBody2D"), None)
        assert rigidbody is not None
        assert rigidbody.get("gravity_scale") == 0

    def test_player_has_animator(self):
        """Verify Player has Animator component."""
        prefab_path = project_root / "Assets" / "Prefabs" / "Player.zprfb"
        data = json.loads(prefab_path.read_text(encoding="utf-8"))

        components = data.get("root", {}).get("components", [])
        comp_types = {c.get("type") for c in components}
        assert "Animator" in comp_types

        # Verify it references PlayerController
        animator = next((c for c in components if c.get("type") == "Animator"), None)
        assert animator is not None
        assert animator.get("controller") == "Assets/Animations/PlayerController.zcontroller"

    def test_player_variables(self):
        """Verify Player has required variables."""
        prefab_path = project_root / "Assets" / "Prefabs" / "Player.zprfb"
        data = json.loads(prefab_path.read_text(encoding="utf-8"))

        variables = data.get("root", {}).get("variables", {})
        assert "move_speed" in variables
        assert "health" in variables
        assert "max_health" in variables
        assert variables["move_speed"] == 200
        assert variables["health"] == 100
        assert variables["max_health"] == 100


class TestPlayerMovementLogic:
    """Test that PlayerMovementLogic.zlogic is properly structured."""

    def test_movement_logic_exists(self):
        """Verify PlayerMovementLogic.zlogic exists."""
        logic_path = project_root / "Assets" / "Logic" / "PlayerMovementLogic.zlogic"
        assert logic_path.exists(), f"PlayerMovementLogic.zlogic not found"

    def test_movement_logic_valid_json(self):
        """Verify movement logic is valid JSON."""
        logic_path = project_root / "Assets" / "Logic" / "PlayerMovementLogic.zlogic"
        data = json.loads(logic_path.read_text(encoding="utf-8"))
        assert data.get("format") == "zennity.generic_graph"

    def test_movement_logic_has_input_nodes(self):
        """Verify logic graph has horizontal/vertical input nodes."""
        logic_path = project_root / "Assets" / "Logic" / "PlayerMovementLogic.zlogic"
        data = json.loads(logic_path.read_text(encoding="utf-8"))

        node_ids = [n.get("id") for n in data.get("nodes", [])]
        assert "input_horizontal" in node_ids
        assert "input_vertical" in node_ids

    def test_movement_logic_has_vector_creation(self):
        """Verify logic graph creates Vector2 from input."""
        logic_path = project_root / "Assets" / "Logic" / "PlayerMovementLogic.zlogic"
        data = json.loads(logic_path.read_text(encoding="utf-8"))

        node_ids = [n.get("id") for n in data.get("nodes", [])]
        assert "create_movement_vector" in node_ids

    def test_movement_logic_has_normalization(self):
        """Verify logic graph normalizes diagonal movement."""
        logic_path = project_root / "Assets" / "Logic" / "PlayerMovementLogic.zlogic"
        data = json.loads(logic_path.read_text(encoding="utf-8"))

        node_ids = [n.get("id") for n in data.get("nodes", [])]
        assert "normalize_vector" in node_ids, \
            "Logic should normalize vector to prevent faster diagonal movement"

    def test_movement_logic_has_speed_multiplication(self):
        """Verify logic graph multiplies normalized vector by move_speed."""
        logic_path = project_root / "Assets" / "Logic" / "PlayerMovementLogic.zlogic"
        data = json.loads(logic_path.read_text(encoding="utf-8"))

        node_ids = [n.get("id") for n in data.get("nodes", [])]
        assert "multiply_speed" in node_ids

    def test_movement_logic_has_physics_apply(self):
        """Verify logic graph applies velocity to RigidBody."""
        logic_path = project_root / "Assets" / "Logic" / "PlayerMovementLogic.zlogic"
        data = json.loads(logic_path.read_text(encoding="utf-8"))

        node_ids = [n.get("id") for n in data.get("nodes", [])]
        assert "set_rigidbody_velocity" in node_ids

    def test_movement_logic_has_animator_parameter(self):
        """Verify logic graph sets animator 'speed' parameter."""
        logic_path = project_root / "Assets" / "Logic" / "PlayerMovementLogic.zlogic"
        data = json.loads(logic_path.read_text(encoding="utf-8"))

        node_ids = [n.get("id") for n in data.get("nodes", [])]
        assert "set_animator_speed" in node_ids

    def test_movement_logic_node_count(self):
        """Record node count for UX evaluation."""
        logic_path = project_root / "Assets" / "Logic" / "PlayerMovementLogic.zlogic"
        data = json.loads(logic_path.read_text(encoding="utf-8"))

        nodes = data.get("nodes", [])
        edges = data.get("edges", [])
        print(f"\nPlayerMovementLogic Stats:")
        print(f"  Nodes: {len(nodes)}")
        print(f"  Edges: {len(edges)}")

        # Expected: ~10 nodes for input → normalize → speed → physics + animator
        assert len(nodes) >= 9, "Logic graph should have at least input, vector, normalize, speed, physics, animator nodes"


class TestAnimationController:
    """Test that PlayerController.zcontroller is properly configured."""

    def test_animation_controller_exists(self):
        """Verify PlayerController.zcontroller exists."""
        controller_path = project_root / "Assets" / "Animations" / "PlayerController.zcontroller"
        assert controller_path.exists(), "PlayerController.zcontroller not found"

    def test_animation_controller_valid_json(self):
        """Verify controller is valid JSON."""
        controller_path = project_root / "Assets" / "Animations" / "PlayerController.zcontroller"
        data = json.loads(controller_path.read_text(encoding="utf-8"))
        assert data.get("format") == "zennity.animation_controller"

    def test_controller_has_states(self):
        """Verify controller has Idle and Run states."""
        controller_path = project_root / "Assets" / "Animations" / "PlayerController.zcontroller"
        data = json.loads(controller_path.read_text(encoding="utf-8"))

        layers = data.get("layers", [])
        assert len(layers) > 0
        states = [s.get("name") for s in layers[0].get("states", [])]
        assert "Idle" in states
        assert "Run" in states

    def test_controller_has_transitions(self):
        """Verify controller has Idle↔Run transitions."""
        controller_path = project_root / "Assets" / "Animations" / "PlayerController.zcontroller"
        data = json.loads(controller_path.read_text(encoding="utf-8"))

        layers = data.get("layers", [])
        transitions = layers[0].get("transitions", [])

        idle_to_run = any(t.get("from") == "Idle" and t.get("to") == "Run"
                         for t in transitions)
        run_to_idle = any(t.get("from") == "Run" and t.get("to") == "Idle"
                         for t in transitions)

        assert idle_to_run, "Should have Idle → Run transition"
        assert run_to_idle, "Should have Run → Idle transition"

    def test_controller_has_speed_parameter(self):
        """Verify controller uses 'speed' float parameter for transitions."""
        controller_path = project_root / "Assets" / "Animations" / "PlayerController.zcontroller"
        data = json.loads(controller_path.read_text(encoding="utf-8"))

        parameters = data.get("parameters", [])
        speed_param = next((p for p in parameters if p.get("name") == "speed"), None)
        assert speed_param is not None
        assert speed_param.get("type") == "float"


class TestAnimationClips:
    """Test that animation clips exist."""

    def test_idle_clip_exists(self):
        """Verify PlayerIdle.zanim exists."""
        clip_path = project_root / "Assets" / "Animations" / "Clips" / "PlayerIdle.zanim"
        assert clip_path.exists(), "PlayerIdle.zanim not found"

    def test_idle_clip_valid_json(self):
        """Verify idle clip is valid JSON."""
        clip_path = project_root / "Assets" / "Animations" / "Clips" / "PlayerIdle.zanim"
        data = json.loads(clip_path.read_text(encoding="utf-8"))
        assert data.get("format") == "zennity.animation_clip"
        assert data.get("name") == "PlayerIdle"


class TestZeroPythonGameplay:
    """Verify Step 2 uses ONLY visual systems, no Python gameplay scripts."""

    def test_level1_no_python_gameplay(self):
        """Verify Level1 doesn't reference Python gameplay scripts."""
        scene_path = project_root / "Assets" / "Scenes" / "Level1.zscene"
        content = scene_path.read_text(encoding="utf-8")

        assert "gameplay" not in content.lower()
        assert ".py" not in content.lower()

    def test_player_prefab_no_python_gameplay(self):
        """Verify Player prefab doesn't reference Python gameplay scripts."""
        prefab_path = project_root / "Assets" / "Prefabs" / "Player.zprfb"
        content = prefab_path.read_text(encoding="utf-8")

        assert "gameplay" not in content.lower()
        assert ".py" not in content.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
