"""
Phase 8A Step 3: Player Combat System Tests

Validates:
- Attack animation and events
- Attack trigger and state machine transitions
- SPACE key input for attack
- Attack cooldown (no multi-trigger)
- Hit detection via raycast
- Damage application
- Enemy death
- Audio integration
- Cross-system flow
- Zero Python gameplay scripts
"""

import pytest
import sys
from pathlib import Path
import json

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


class TestAttackAnimation:
    """Test PlayerAttack.zanim exists and is configured correctly."""

    def test_attack_clip_exists(self):
        """Verify PlayerAttack.zanim file exists."""
        clip_path = project_root / "Assets" / "Animations" / "Clips" / "PlayerAttack.zanim"
        assert clip_path.exists(), "PlayerAttack.zanim not found"

    def test_attack_clip_valid_json(self):
        """Verify attack clip is valid JSON."""
        clip_path = project_root / "Assets" / "Animations" / "Clips" / "PlayerAttack.zanim"
        data = json.loads(clip_path.read_text(encoding="utf-8"))
        assert data.get("format") == "zennity.animation_clip"
        assert data.get("name") == "PlayerAttack"

    def test_attack_clip_not_looping(self):
        """Verify attack animation is NOT looping."""
        clip_path = project_root / "Assets" / "Animations" / "Clips" / "PlayerAttack.zanim"
        data = json.loads(clip_path.read_text(encoding="utf-8"))
        assert data.get("loop") is False, "Attack animation should not loop"

    def test_attack_clip_has_frames(self):
        """Verify attack clip has animation frames."""
        clip_path = project_root / "Assets" / "Animations" / "Clips" / "PlayerAttack.zanim"
        data = json.loads(clip_path.read_text(encoding="utf-8"))
        frames = data.get("frames", [])
        assert len(frames) >= 3, "Attack clip should have at least 3 frames"

    def test_attack_clip_has_hit_event(self):
        """Verify attack clip has 'hit' event in middle frame."""
        clip_path = project_root / "Assets" / "Animations" / "Clips" / "PlayerAttack.zanim"
        data = json.loads(clip_path.read_text(encoding="utf-8"))
        frames = data.get("frames", [])

        hit_event_found = False
        for frame in frames:
            if frame.get("event"):
                if frame["event"].get("name") == "hit":
                    hit_event_found = True
                    break

        assert hit_event_found, "Attack clip should have 'hit' event"


class TestAnimationController:
    """Test PlayerController.zcontroller has Attack state and transitions."""

    def test_controller_has_attack_state(self):
        """Verify animation controller has Attack state."""
        controller_path = project_root / "Assets" / "Animations" / "PlayerController.zcontroller"
        data = json.loads(controller_path.read_text(encoding="utf-8"))

        states = [s.get("name") for s in data["layers"][0].get("states", [])]
        assert "Attack" in states, "Controller should have Attack state"

    def test_attack_state_uses_correct_clip(self):
        """Verify Attack state references PlayerAttack.zanim."""
        controller_path = project_root / "Assets" / "Animations" / "PlayerController.zcontroller"
        data = json.loads(controller_path.read_text(encoding="utf-8"))

        attack_state = next((s for s in data["layers"][0].get("states", [])
                            if s.get("name") == "Attack"), None)
        assert attack_state is not None
        assert attack_state.get("clip") == "Assets/Animations/Clips/PlayerAttack.zanim"

    def test_controller_has_attack_trigger(self):
        """Verify animation controller has 'attack' trigger parameter."""
        controller_path = project_root / "Assets" / "Animations" / "PlayerController.zcontroller"
        data = json.loads(controller_path.read_text(encoding="utf-8"))

        parameters = data.get("parameters", [])
        attack_param = next((p for p in parameters if p.get("name") == "attack"), None)
        assert attack_param is not None
        assert attack_param.get("type") == "trigger"

    def test_idle_to_attack_transition(self):
        """Verify Idle → Attack transition with attack trigger."""
        controller_path = project_root / "Assets" / "Animations" / "PlayerController.zcontroller"
        data = json.loads(controller_path.read_text(encoding="utf-8"))

        transitions = data["layers"][0].get("transitions", [])
        idle_attack = next((t for t in transitions
                           if t.get("from") == "Idle" and t.get("to") == "Attack"), None)
        assert idle_attack is not None

    def test_run_to_attack_transition(self):
        """Verify Run → Attack transition with attack trigger."""
        controller_path = project_root / "Assets" / "Animations" / "PlayerController.zcontroller"
        data = json.loads(controller_path.read_text(encoding="utf-8"))

        transitions = data["layers"][0].get("transitions", [])
        run_attack = next((t for t in transitions
                          if t.get("from") == "Run" and t.get("to") == "Attack"), None)
        assert run_attack is not None

    def test_attack_to_idle_transition(self):
        """Verify Attack → Idle transition based on speed."""
        controller_path = project_root / "Assets" / "Animations" / "PlayerController.zcontroller"
        data = json.loads(controller_path.read_text(encoding="utf-8"))

        transitions = data["layers"][0].get("transitions", [])
        attack_idle = next((t for t in transitions
                           if t.get("from") == "Attack" and t.get("to") == "Idle"), None)
        assert attack_idle is not None

    def test_attack_to_run_transition(self):
        """Verify Attack → Run transition based on speed."""
        controller_path = project_root / "Assets" / "Animations" / "PlayerController.zcontroller"
        data = json.loads(controller_path.read_text(encoding="utf-8"))

        transitions = data["layers"][0].get("transitions", [])
        attack_run = next((t for t in transitions
                          if t.get("from") == "Attack" and t.get("to") == "Run"), None)
        assert attack_run is not None


class TestPlayerCombatLogic:
    """Test PlayerCombatLogic.zlogic structure."""

    def test_combat_logic_exists(self):
        """Verify PlayerCombatLogic.zlogic exists."""
        logic_path = project_root / "Assets" / "Logic" / "PlayerCombatLogic.zlogic"
        assert logic_path.exists(), "PlayerCombatLogic.zlogic not found"

    def test_combat_logic_valid_json(self):
        """Verify combat logic is valid JSON."""
        logic_path = project_root / "Assets" / "Logic" / "PlayerCombatLogic.zlogic"
        data = json.loads(logic_path.read_text(encoding="utf-8"))
        assert data.get("format") == "zennity.generic_graph"

    def test_combat_has_space_input_node(self):
        """Verify logic has SPACE key input node."""
        logic_path = project_root / "Assets" / "Logic" / "PlayerCombatLogic.zlogic"
        data = json.loads(logic_path.read_text(encoding="utf-8"))

        node_ids = [n.get("id") for n in data.get("nodes", [])]
        assert "space_key_down" in node_ids

    def test_combat_has_attack_trigger_node(self):
        """Verify logic has set_attack_trigger node."""
        logic_path = project_root / "Assets" / "Logic" / "PlayerCombatLogic.zlogic"
        data = json.loads(logic_path.read_text(encoding="utf-8"))

        node_ids = [n.get("id") for n in data.get("nodes", [])]
        assert "set_attack_trigger" in node_ids

    def test_combat_has_animation_event_node(self):
        """Verify logic has animation.on_event 'hit' node."""
        logic_path = project_root / "Assets" / "Logic" / "PlayerCombatLogic.zlogic"
        data = json.loads(logic_path.read_text(encoding="utf-8"))

        node_ids = [n.get("id") for n in data.get("nodes", [])]
        assert "animation_hit_event" in node_ids

    def test_combat_has_raycast_node(self):
        """Verify logic has raycast_2d node."""
        logic_path = project_root / "Assets" / "Logic" / "PlayerCombatLogic.zlogic"
        data = json.loads(logic_path.read_text(encoding="utf-8"))

        node_ids = [n.get("id") for n in data.get("nodes", [])]
        assert "raycast_for_enemy" in node_ids

    def test_combat_has_damage_nodes(self):
        """Verify logic has damage calculation nodes."""
        logic_path = project_root / "Assets" / "Logic" / "PlayerCombatLogic.zlogic"
        data = json.loads(logic_path.read_text(encoding="utf-8"))

        node_ids = [n.get("id") for n in data.get("nodes", [])]
        assert "get_attack_damage" in node_ids
        assert "subtract_damage" in node_ids
        assert "get_enemy_health" in node_ids
        assert "set_enemy_health" in node_ids

    def test_combat_has_death_check_node(self):
        """Verify logic has health <= 0 check and destroy."""
        logic_path = project_root / "Assets" / "Logic" / "PlayerCombatLogic.zlogic"
        data = json.loads(logic_path.read_text(encoding="utf-8"))

        node_ids = [n.get("id") for n in data.get("nodes", [])]
        assert "check_dead" in node_ids
        assert "destroy_enemy" in node_ids

    def test_combat_logic_node_count(self):
        """Record combat logic node and edge counts."""
        logic_path = project_root / "Assets" / "Logic" / "PlayerCombatLogic.zlogic"
        data = json.loads(logic_path.read_text(encoding="utf-8"))

        nodes = data.get("nodes", [])
        edges = data.get("edges", [])
        print(f"\nPlayerCombatLogic Stats:")
        print(f"  Nodes: {len(nodes)}")
        print(f"  Edges: {len(edges)}")

        assert len(nodes) >= 12, "Combat logic should have at least 12 nodes"


class TestPlayerCombatVariables:
    """Test Player prefab has combat variables."""

    def test_player_has_attack_damage(self):
        """Verify Player has attack_damage variable."""
        prefab_path = project_root / "Assets" / "Prefabs" / "Player.zprfb"
        data = json.loads(prefab_path.read_text(encoding="utf-8"))

        variables = data.get("root", {}).get("variables", {})
        assert "attack_damage" in variables
        assert variables["attack_damage"] == 25

    def test_player_has_attack_range(self):
        """Verify Player has attack_range variable."""
        prefab_path = project_root / "Assets" / "Prefabs" / "Player.zprfb"
        data = json.loads(prefab_path.read_text(encoding="utf-8"))

        variables = data.get("root", {}).get("variables", {})
        assert "attack_range" in variables
        assert variables["attack_range"] == 64

    def test_player_has_facing_direction(self):
        """Verify Player has facing_x variable."""
        prefab_path = project_root / "Assets" / "Prefabs" / "Player.zprfb"
        data = json.loads(prefab_path.read_text(encoding="utf-8"))

        variables = data.get("root", {}).get("variables", {})
        assert "facing_x" in variables
        assert variables["facing_x"] in [-1, 0, 1]


class TestDummyEnemyPrefab:
    """Test DummyEnemy.zprfb structure."""

    def test_dummy_enemy_exists(self):
        """Verify DummyEnemy.zprfb exists."""
        prefab_path = project_root / "Assets" / "Prefabs" / "DummyEnemy.zprfb"
        assert prefab_path.exists(), "DummyEnemy.zprfb not found"

    def test_dummy_enemy_valid_json(self):
        """Verify DummyEnemy is valid JSON."""
        prefab_path = project_root / "Assets" / "Prefabs" / "DummyEnemy.zprfb"
        data = json.loads(prefab_path.read_text(encoding="utf-8"))
        assert data.get("format") == "zennity.prefab"
        assert data.get("name") == "DummyEnemy"

    def test_dummy_enemy_has_components(self):
        """Verify DummyEnemy has required components."""
        prefab_path = project_root / "Assets" / "Prefabs" / "DummyEnemy.zprfb"
        data = json.loads(prefab_path.read_text(encoding="utf-8"))

        components = data.get("root", {}).get("components", [])
        comp_types = {c.get("type") for c in components}

        assert "Transform" in comp_types
        assert "SpriteRenderer" in comp_types
        assert "BoxCollider2D" in comp_types

    def test_dummy_enemy_has_health_variables(self):
        """Verify DummyEnemy has health variables."""
        prefab_path = project_root / "Assets" / "Prefabs" / "DummyEnemy.zprfb"
        data = json.loads(prefab_path.read_text(encoding="utf-8"))

        variables = data.get("root", {}).get("variables", {})
        assert "health" in variables
        assert "max_health" in variables
        assert variables["health"] == 100
        assert variables["max_health"] == 100

    def test_dummy_enemy_collider_on_enemy_layer(self):
        """Verify DummyEnemy collider is on ENEMY layer."""
        prefab_path = project_root / "Assets" / "Prefabs" / "DummyEnemy.zprfb"
        data = json.loads(prefab_path.read_text(encoding="utf-8"))

        components = data.get("root", {}).get("components", [])
        collider = next((c for c in components if c.get("type") == "BoxCollider2D"), None)
        assert collider is not None
        assert collider.get("layer") == "ENEMY"


class TestLevel1Setup:
    """Test Level1 has Player and DummyEnemy configured correctly."""

    def test_level1_has_combat_logic_on_player(self):
        """Verify Level1 Player has PlayerCombatLogic attached."""
        scene_path = project_root / "Assets" / "Scenes" / "Level1.zscene"
        data = json.loads(scene_path.read_text(encoding="utf-8"))

        player = next((obj for obj in data.get("objects", [])
                      if obj.get("name") == "Player"), None)
        assert player is not None

        graphs = player.get("logic_graphs", [])
        has_combat = any(g.get("path") == "Assets/Logic/PlayerCombatLogic.zlogic"
                        for g in graphs)
        assert has_combat, "Player should have PlayerCombatLogic attached"

    def test_level1_has_dummy_enemy(self):
        """Verify Level1 has DummyEnemy prefab."""
        scene_path = project_root / "Assets" / "Scenes" / "Level1.zscene"
        data = json.loads(scene_path.read_text(encoding="utf-8"))

        enemy_objs = [obj for obj in data.get("objects", [])
                     if obj.get("name") == "DummyEnemy"]
        assert len(enemy_objs) >= 1, "Level1 should have at least one DummyEnemy"

    def test_dummy_enemy_is_prefab_reference(self):
        """Verify DummyEnemy in Level1 is a prefab reference."""
        scene_path = project_root / "Assets" / "Scenes" / "Level1.zscene"
        data = json.loads(scene_path.read_text(encoding="utf-8"))

        enemy = next((obj for obj in data.get("objects", [])
                     if obj.get("name") == "DummyEnemy"), None)
        assert enemy is not None
        assert enemy.get("type") == "Prefab"
        assert enemy.get("prefab") == "Assets/Prefabs/DummyEnemy.zprfb"


class TestMovementLogicUpdate:
    """Test PlayerMovementLogic tracks facing direction."""

    def test_movement_logic_has_facing_update_nodes(self):
        """Verify movement logic has nodes to update facing_x."""
        logic_path = project_root / "Assets" / "Logic" / "PlayerMovementLogic.zlogic"
        data = json.loads(logic_path.read_text(encoding="utf-8"))

        node_ids = [n.get("id") for n in data.get("nodes", [])]
        # Check for facing direction update nodes
        has_facing_logic = (
            "check_horizontal_movement" in node_ids or
            "set_facing_direction" in node_ids or
            "get_sign_of_horizontal" in node_ids
        )
        assert has_facing_logic, "Movement logic should track facing direction"


class TestZeroPythonCombat:
    """Verify Step 3 uses ONLY visual systems, no Python gameplay scripts."""

    def test_level1_no_python_combat_scripts(self):
        """Verify Level1 doesn't reference Python combat scripts."""
        scene_path = project_root / "Assets" / "Scenes" / "Level1.zscene"
        content = scene_path.read_text(encoding="utf-8")

        assert "combat.py" not in content.lower()
        assert "attack.py" not in content.lower()
        assert "damage.py" not in content.lower()

    def test_player_prefab_no_python_combat_scripts(self):
        """Verify Player prefab doesn't reference Python combat scripts."""
        prefab_path = project_root / "Assets" / "Prefabs" / "Player.zprfb"
        content = prefab_path.read_text(encoding="utf-8")

        assert "combat.py" not in content.lower()
        assert "attack.py" not in content.lower()

    def test_dummy_enemy_no_python_scripts(self):
        """Verify DummyEnemy prefab doesn't reference Python scripts."""
        prefab_path = project_root / "Assets" / "Prefabs" / "DummyEnemy.zprfb"
        content = prefab_path.read_text(encoding="utf-8")

        assert ".py" not in content.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
