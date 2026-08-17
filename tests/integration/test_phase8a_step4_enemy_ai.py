"""
Phase 8A Step 4: Enemy AI + Player Damage Tests

Validates:
- Enemy prefab and components
- Enemy animation controller
- Enemy AI logic graph (detection, chase, attack)
- Player damage system
- Player health UI
- Game Over scene
- Multiple independent enemies
- Zero Python gameplay scripts
"""

import pytest
import sys
from pathlib import Path
import json

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


class TestEnemyPrefab:
    """Test Enemy.zprfb structure and configuration."""

    def test_enemy_prefab_exists(self):
        """Verify Enemy.zprfb exists."""
        prefab_path = project_root / "Assets" / "Prefabs" / "Enemy.zprfb"
        assert prefab_path.exists(), "Enemy.zprfb not found"

    def test_enemy_prefab_valid_json(self):
        """Verify Enemy prefab is valid JSON."""
        prefab_path = project_root / "Assets" / "Prefabs" / "Enemy.zprfb"
        data = json.loads(prefab_path.read_text(encoding="utf-8"))
        assert data.get("format") == "zennity.prefab"
        assert data.get("name") == "Enemy"

    def test_enemy_has_required_components(self):
        """Verify Enemy has Transform, Sprite, Collider, RigidBody, Animator."""
        prefab_path = project_root / "Assets" / "Prefabs" / "Enemy.zprfb"
        data = json.loads(prefab_path.read_text(encoding="utf-8"))

        components = data.get("root", {}).get("components", [])
        comp_types = {c.get("type") for c in components}

        assert "Transform" in comp_types
        assert "SpriteRenderer" in comp_types
        assert "BoxCollider2D" in comp_types
        assert "RigidBody2D" in comp_types
        assert "Animator" in comp_types

    def test_enemy_has_ai_logic_graphs(self):
        """Verify Enemy has EnemyAILogic and EnemyAttackLogic."""
        prefab_path = project_root / "Assets" / "Prefabs" / "Enemy.zprfb"
        data = json.loads(prefab_path.read_text(encoding="utf-8"))

        graphs = data.get("root", {}).get("logic_graphs", [])
        graph_paths = {g.get("path") for g in graphs}

        assert "Assets/Logic/EnemyAILogic.zlogic" in graph_paths
        assert "Assets/Logic/EnemyAttackLogic.zlogic" in graph_paths

    def test_enemy_has_health_variables(self):
        """Verify Enemy has health variables."""
        prefab_path = project_root / "Assets" / "Prefabs" / "Enemy.zprfb"
        data = json.loads(prefab_path.read_text(encoding="utf-8"))

        variables = data.get("root", {}).get("variables", {})
        assert "health" in variables
        assert "max_health" in variables
        assert variables["health"] == 100
        assert variables["max_health"] == 100

    def test_enemy_has_movement_variables(self):
        """Verify Enemy has move_speed variable."""
        prefab_path = project_root / "Assets" / "Prefabs" / "Enemy.zprfb"
        data = json.loads(prefab_path.read_text(encoding="utf-8"))

        variables = data.get("root", {}).get("variables", {})
        assert "move_speed" in variables
        assert variables["move_speed"] == 100

    def test_enemy_has_attack_variables(self):
        """Verify Enemy has attack variables."""
        prefab_path = project_root / "Assets" / "Prefabs" / "Enemy.zprfb"
        data = json.loads(prefab_path.read_text(encoding="utf-8"))

        variables = data.get("root", {}).get("variables", {})
        assert "attack_damage" in variables
        assert "attack_range" in variables
        assert "attack_cooldown" in variables
        assert variables["attack_damage"] == 10
        assert variables["attack_range"] == 48
        assert variables["attack_cooldown"] == 1.0

    def test_enemy_has_detection_range(self):
        """Verify Enemy has detection_range variable."""
        prefab_path = project_root / "Assets" / "Prefabs" / "Enemy.zprfb"
        data = json.loads(prefab_path.read_text(encoding="utf-8"))

        variables = data.get("root", {}).get("variables", {})
        assert "detection_range" in variables
        assert variables["detection_range"] == 300

    def test_enemy_collider_on_enemy_layer(self):
        """Verify Enemy collider is on ENEMY layer."""
        prefab_path = project_root / "Assets" / "Prefabs" / "Enemy.zprfb"
        data = json.loads(prefab_path.read_text(encoding="utf-8"))

        components = data.get("root", {}).get("components", [])
        collider = next((c for c in components if c.get("type") == "BoxCollider2D"), None)
        assert collider is not None
        assert collider.get("layer") == "ENEMY"


class TestEnemyAnimations:
    """Test enemy animation clips."""

    def test_enemy_idle_clip_exists(self):
        """Verify EnemyIdle.zanim exists."""
        clip_path = project_root / "Assets" / "Animations" / "Clips" / "EnemyIdle.zanim"
        assert clip_path.exists(), "EnemyIdle.zanim not found"

    def test_enemy_run_clip_exists(self):
        """Verify EnemyRun.zanim exists."""
        clip_path = project_root / "Assets" / "Animations" / "Clips" / "EnemyRun.zanim"
        assert clip_path.exists(), "EnemyRun.zanim not found"

    def test_enemy_attack_clip_exists(self):
        """Verify EnemyAttack.zanim exists."""
        clip_path = project_root / "Assets" / "Animations" / "Clips" / "EnemyAttack.zanim"
        assert clip_path.exists(), "EnemyAttack.zanim not found"

    def test_enemy_attack_clip_has_hit_event(self):
        """Verify EnemyAttack animation has hit event."""
        clip_path = project_root / "Assets" / "Animations" / "Clips" / "EnemyAttack.zanim"
        data = json.loads(clip_path.read_text(encoding="utf-8"))

        frames = data.get("frames", [])
        hit_event_found = any(
            f.get("event", {}).get("name") == "hit"
            for f in frames
        )
        assert hit_event_found, "EnemyAttack should have hit event"

    def test_enemy_death_clip_exists(self):
        """Verify EnemyDeath.zanim exists."""
        clip_path = project_root / "Assets" / "Animations" / "Clips" / "EnemyDeath.zanim"
        assert clip_path.exists(), "EnemyDeath.zanim not found"


class TestEnemyAnimationController:
    """Test EnemyAnimationController configuration."""

    def test_controller_exists(self):
        """Verify EnemyAnimationController.zcontroller exists."""
        controller_path = project_root / "Assets" / "Animations" / "EnemyAnimationController.zcontroller"
        assert controller_path.exists()

    def test_controller_valid_json(self):
        """Verify controller is valid JSON."""
        controller_path = project_root / "Assets" / "Animations" / "EnemyAnimationController.zcontroller"
        data = json.loads(controller_path.read_text(encoding="utf-8"))
        assert data.get("format") == "zennity.animation_controller"

    def test_controller_has_states(self):
        """Verify controller has Idle, Run, Attack, Death states."""
        controller_path = project_root / "Assets" / "Animations" / "EnemyAnimationController.zcontroller"
        data = json.loads(controller_path.read_text(encoding="utf-8"))

        states = [s.get("name") for s in data["layers"][0].get("states", [])]
        assert "Idle" in states
        assert "Run" in states
        assert "Attack" in states
        assert "Death" in states

    def test_controller_has_attack_trigger(self):
        """Verify controller has attack trigger parameter."""
        controller_path = project_root / "Assets" / "Animations" / "EnemyAnimationController.zcontroller"
        data = json.loads(controller_path.read_text(encoding="utf-8"))

        parameters = data.get("parameters", [])
        attack_param = next((p for p in parameters if p.get("name") == "attack"), None)
        assert attack_param is not None
        assert attack_param.get("type") == "trigger"

    def test_controller_has_dead_trigger(self):
        """Verify controller has dead trigger parameter."""
        controller_path = project_root / "Assets" / "Animations" / "EnemyAnimationController.zcontroller"
        data = json.loads(controller_path.read_text(encoding="utf-8"))

        parameters = data.get("parameters", [])
        dead_param = next((p for p in parameters if p.get("name") == "dead"), None)
        assert dead_param is not None
        assert dead_param.get("type") == "trigger"


class TestEnemyAILogic:
    """Test EnemyAILogic.zlogic structure."""

    def test_logic_exists(self):
        """Verify EnemyAILogic.zlogic exists."""
        logic_path = project_root / "Assets" / "Logic" / "EnemyAILogic.zlogic"
        assert logic_path.exists()

    def test_logic_valid_json(self):
        """Verify logic is valid JSON."""
        logic_path = project_root / "Assets" / "Logic" / "EnemyAILogic.zlogic"
        data = json.loads(logic_path.read_text(encoding="utf-8"))
        assert data.get("format") == "zennity.generic_graph"

    def test_logic_has_find_player_node(self):
        """Verify logic has find_player node."""
        logic_path = project_root / "Assets" / "Logic" / "EnemyAILogic.zlogic"
        data = json.loads(logic_path.read_text(encoding="utf-8"))

        node_ids = [n.get("id") for n in data.get("nodes", [])]
        assert "find_player" in node_ids

    def test_logic_has_distance_nodes(self):
        """Verify logic calculates distance to player."""
        logic_path = project_root / "Assets" / "Logic" / "EnemyAILogic.zlogic"
        data = json.loads(logic_path.read_text(encoding="utf-8"))

        node_ids = [n.get("id") for n in data.get("nodes", [])]
        assert "calculate_distance" in node_ids
        assert "check_detected" in node_ids

    def test_logic_has_chase_nodes(self):
        """Verify logic has chase/movement nodes.

        This used to name ``calculate_direction`` and ``normalize_direction``.
        Those were a ``vector2`` and a ``normalize_vector`` node -- types this
        engine never implemented -- so the test was pinning an authored shape
        that could not run, not a contract anyone could rely on.

        PHASE 9 recovery item 14E replaced that pair with the scalar
        normalization proven in item 14D.2: two subtractions for the component
        deltas and two divisions by the measured distance. The intent of the
        test is unchanged -- the graph must still contain a chase -- so it now
        names the nodes that actually perform one.
        """
        logic_path = project_root / "Assets" / "Logic" / "EnemyAILogic.zlogic"
        data = json.loads(logic_path.read_text(encoding="utf-8"))

        node_ids = [n.get("id") for n in data.get("nodes", [])]
        node_types = {n.get("type") for n in data.get("nodes", [])}

        for chase_node in ("enemy_dx", "enemy_dy", "enemy_nx", "enemy_ny"):
            assert chase_node in node_ids, chase_node
        assert "set_enemy_velocity" in node_ids
        assert "calculate_distance" in node_ids

        assert not node_types & {"math.vector2_create", "math.vector2_normalize"}

    def test_logic_has_attack_range_check(self):
        """Verify logic checks attack range."""
        logic_path = project_root / "Assets" / "Logic" / "EnemyAILogic.zlogic"
        data = json.loads(logic_path.read_text(encoding="utf-8"))

        node_ids = [n.get("id") for n in data.get("nodes", [])]
        assert "check_in_attack_range" in node_ids
        assert "stop_enemy" in node_ids

    def test_attack_cooldown_lives_in_the_attack_graph_not_this_one(self):
        """Inverted by hotfix H1: the cooldown moved out of the AI graph.

        This used to require ``check_can_attack`` / ``set_attack_trigger`` /
        ``reset_cooldown_timer`` inside ``EnemyAILogic``. Item 19 gave
        ``EnemyAttackLogic`` the damage pipeline and the ownership of
        ``cooldown_timer``; the copy left here kept resetting that timer one
        graph earlier in the frame, and the enemy dealt no damage at all in
        Level2. So the mechanics are asserted where they now live, and their
        absence is asserted where they used to be.
        """
        ai = json.loads((project_root / "Assets" / "Logic" / "EnemyAILogic.zlogic").read_text(encoding="utf-8"))
        attack = json.loads((project_root / "Assets" / "Logic" / "EnemyAttackLogic.zlogic").read_text(encoding="utf-8"))

        ai_ids = {n.get("id") for n in ai.get("nodes", [])}
        attack_ids = {n.get("id") for n in attack.get("nodes", [])}

        for node_id in ("check_can_attack", "set_attack_trigger", "reset_cooldown_timer"):
            assert node_id in attack_ids, f"{node_id} must live in EnemyAttackLogic"
            assert node_id not in ai_ids, f"{node_id} came back to EnemyAILogic"

    def test_logic_node_count(self):
        """Record AI logic node count."""
        logic_path = project_root / "Assets" / "Logic" / "EnemyAILogic.zlogic"
        data = json.loads(logic_path.read_text(encoding="utf-8"))

        nodes = data.get("nodes", [])
        edges = data.get("edges", [])
        print(f"\nEnemyAILogic Stats:")
        print(f"  Nodes: {len(nodes)}")
        print(f"  Edges: {len(edges)}")

        assert len(nodes) >= 20, "AI logic should have comprehensive nodes"


class TestEnemyAttackLogic:
    """Test EnemyAttackLogic.zlogic."""

    def test_attack_logic_exists(self):
        """Verify EnemyAttackLogic.zlogic exists."""
        logic_path = project_root / "Assets" / "Logic" / "EnemyAttackLogic.zlogic"
        assert logic_path.exists()

    def test_attack_logic_has_hit_event_listener(self):
        """Verify attack logic listens for hit event."""
        logic_path = project_root / "Assets" / "Logic" / "EnemyAttackLogic.zlogic"
        data = json.loads(logic_path.read_text(encoding="utf-8"))

        node_ids = [n.get("id") for n in data.get("nodes", [])]
        assert "animation_hit_event" in node_ids

    def test_attack_logic_has_raycast_nodes(self):
        """Verify attack logic raycasts for player."""
        logic_path = project_root / "Assets" / "Logic" / "EnemyAttackLogic.zlogic"
        data = json.loads(logic_path.read_text(encoding="utf-8"))

        node_ids = [n.get("id") for n in data.get("nodes", [])]
        assert "raycast_for_player" in node_ids

    def test_attack_logic_applies_damage(self):
        """Verify attack logic applies damage to player."""
        logic_path = project_root / "Assets" / "Logic" / "EnemyAttackLogic.zlogic"
        data = json.loads(logic_path.read_text(encoding="utf-8"))

        node_ids = [n.get("id") for n in data.get("nodes", [])]
        assert "get_player_health" in node_ids
        assert "subtract_damage" in node_ids
        assert "set_player_health" in node_ids


class TestPlayerHealthLogic:
    """Test PlayerHealthLogic.zlogic."""

    def test_health_logic_exists(self):
        """Verify PlayerHealthLogic.zlogic exists."""
        logic_path = project_root / "Assets" / "Logic" / "PlayerHealthLogic.zlogic"
        assert logic_path.exists()

    def test_health_logic_updates_ui(self):
        """Verify health logic updates UI."""
        logic_path = project_root / "Assets" / "Logic" / "PlayerHealthLogic.zlogic"
        data = json.loads(logic_path.read_text(encoding="utf-8"))

        node_ids = [n.get("id") for n in data.get("nodes", [])]
        assert "update_ui_health_bar" in node_ids

    def test_health_logic_checks_death(self):
        """Verify health logic checks for death."""
        logic_path = project_root / "Assets" / "Logic" / "PlayerHealthLogic.zlogic"
        data = json.loads(logic_path.read_text(encoding="utf-8"))

        node_ids = [n.get("id") for n in data.get("nodes", [])]
        assert "check_dead" in node_ids
        assert "load_gameover_scene" in node_ids


class TestGameOverScene:
    """Test GameOver.zscene and UI."""

    def test_gameover_scene_exists(self):
        """Verify GameOver.zscene exists."""
        scene_path = project_root / "Assets" / "Scenes" / "GameOver.zscene"
        assert scene_path.exists()

    def test_gameover_scene_valid_json(self):
        """Verify GameOver scene is valid JSON."""
        scene_path = project_root / "Assets" / "Scenes" / "GameOver.zscene"
        data = json.loads(scene_path.read_text(encoding="utf-8"))
        assert data.get("format") == "zennity.scene"
        assert data.get("name") == "Game Over"

    def test_gameover_ui_exists(self):
        """Verify GameOver.zui exists."""
        ui_path = project_root / "Assets" / "UI" / "GameOver.zui"
        assert ui_path.exists()

    def test_gameover_ui_has_retry_button(self):
        """Verify GameOver UI has Retry button."""
        ui_path = project_root / "Assets" / "UI" / "GameOver.zui"
        data = json.loads(ui_path.read_text(encoding="utf-8"))

        widgets = [w.get("name") for w in data.get("widgets", [])]
        assert "RetryButton" in widgets

    def test_gameover_ui_has_main_menu_button(self):
        """Verify GameOver UI has Main Menu button."""
        ui_path = project_root / "Assets" / "UI" / "GameOver.zui"
        data = json.loads(ui_path.read_text(encoding="utf-8"))

        widgets = [w.get("name") for w in data.get("widgets", [])]
        assert "MainMenuButton" in widgets

    def test_gameover_logic_exists(self):
        """Verify GameOverLogic.zlogic exists."""
        logic_path = project_root / "Assets" / "Logic" / "GameOverLogic.zlogic"
        assert logic_path.exists()


class TestHUDHealthBar:
    """Test HUD has HealthBar."""

    def test_hud_has_health_bar(self):
        """Verify HUD.zui has HealthBar widget."""
        ui_path = project_root / "Assets" / "UI" / "HUD.zui"
        data = json.loads(ui_path.read_text(encoding="utf-8"))

        widgets = [w.get("name") for w in data.get("widgets", [])]
        assert "HealthBar" in widgets

    def test_health_bar_is_progress_bar(self):
        """Verify HealthBar is ProgressBar type."""
        ui_path = project_root / "Assets" / "UI" / "HUD.zui"
        data = json.loads(ui_path.read_text(encoding="utf-8"))

        health_bar = next((w for w in data.get("widgets", [])
                          if w.get("name") == "HealthBar"), None)
        assert health_bar is not None
        assert health_bar.get("type") == "ProgressBar"

    def test_health_bar_default_value(self):
        """Verify HealthBar starts at 100."""
        ui_path = project_root / "Assets" / "UI" / "HUD.zui"
        data = json.loads(ui_path.read_text(encoding="utf-8"))

        health_bar = next((w for w in data.get("widgets", [])
                          if w.get("name") == "HealthBar"), None)
        assert health_bar is not None
        assert health_bar.get("current_value") == 100


class TestLevel1Setup:
    """Test Level1 has Player and Enemies configured."""

    def test_level1_has_three_enemies(self):
        """Verify Level1 has at least 3 Enemy prefabs."""
        scene_path = project_root / "Assets" / "Scenes" / "Level1.zscene"
        data = json.loads(scene_path.read_text(encoding="utf-8"))

        enemies = [obj for obj in data.get("objects", [])
                  if obj.get("type") == "Prefab" and "Enemy" in obj.get("prefab", "")]
        assert len(enemies) >= 3, "Level1 should have at least 3 enemies"

    def test_player_has_health_logic(self):
        """Verify Player in Level1 has PlayerHealthLogic."""
        scene_path = project_root / "Assets" / "Scenes" / "Level1.zscene"
        data = json.loads(scene_path.read_text(encoding="utf-8"))

        player = next((obj for obj in data.get("objects", [])
                      if obj.get("name") == "Player"), None)
        assert player is not None

        graphs = player.get("logic_graphs", [])
        has_health = any(g.get("path") == "Assets/Logic/PlayerHealthLogic.zlogic"
                        for g in graphs)
        assert has_health, "Player should have PlayerHealthLogic"


class TestZeroPythonEnemyAI:
    """Verify Step 4 uses ONLY visual systems, no Python gameplay."""

    def test_no_python_enemy_ai_scripts(self):
        """Verify no enemy_ai.py references."""
        enemy_path = project_root / "Assets" / "Prefabs" / "Enemy.zprfb"
        content = enemy_path.read_text(encoding="utf-8")

        assert "enemy_ai.py" not in content.lower()
        assert "ai.py" not in content.lower()

    def test_no_python_health_scripts(self):
        """Verify no player_health.py references."""
        player_path = project_root / "Assets" / "Prefabs" / "Player.zprfb"
        content = player_path.read_text(encoding="utf-8")

        assert "player_health.py" not in content.lower()
        assert "health.py" not in content.lower()

    def test_no_python_in_gameover(self):
        """Verify no Python scripts in GameOver."""
        scene_path = project_root / "Assets" / "Scenes" / "GameOver.zscene"
        content = scene_path.read_text(encoding="utf-8")

        assert ".py" not in content.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
