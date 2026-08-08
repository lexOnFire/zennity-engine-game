"""
Phase 8A Step 6: Boss Fight Tests

Validates:
- Boss prefab and components
- Boss animations and controller
- Boss AI logic
- Boss health and HUD
- Boss phases
- Boss death and boss_defeated flag
"""

import pytest
import sys
from pathlib import Path
import json

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


class TestBossPrefab:
    def test_boss_prefab_exists(self):
        prefab_path = project_root / "Assets" / "Prefabs" / "Boss.zprfb"
        assert prefab_path.exists()

    def test_boss_has_components(self):
        prefab_path = project_root / "Assets" / "Prefabs" / "Boss.zprfb"
        data = json.loads(prefab_path.read_text(encoding="utf-8"))
        components = data.get("root", {}).get("components", [])
        comp_types = {c.get("type") for c in components}
        assert "Transform" in comp_types
        assert "SpriteRenderer" in comp_types
        assert "BoxCollider2D" in comp_types
        assert "RigidBody2D" in comp_types
        assert "Animator" in comp_types

    def test_boss_health_500(self):
        prefab_path = project_root / "Assets" / "Prefabs" / "Boss.zprfb"
        data = json.loads(prefab_path.read_text(encoding="utf-8"))
        variables = data.get("root", {}).get("variables", {})
        assert variables.get("health") == 500
        assert variables.get("max_health") == 500

    def test_boss_phase_initial(self):
        prefab_path = project_root / "Assets" / "Prefabs" / "Boss.zprfb"
        data = json.loads(prefab_path.read_text(encoding="utf-8"))
        variables = data.get("root", {}).get("variables", {})
        assert variables.get("phase") == 1

    def test_boss_attack_damage(self):
        prefab_path = project_root / "Assets" / "Prefabs" / "Boss.zprfb"
        data = json.loads(prefab_path.read_text(encoding="utf-8"))
        variables = data.get("root", {}).get("variables", {})
        assert variables.get("attack_damage") == 20
        assert variables.get("heavy_attack_damage") == 35

    def test_boss_has_logic_graphs(self):
        prefab_path = project_root / "Assets" / "Prefabs" / "Boss.zprfb"
        data = json.loads(prefab_path.read_text(encoding="utf-8"))
        graphs = data.get("root", {}).get("logic_graphs", [])
        graph_paths = {g.get("path") for g in graphs}
        assert "Assets/Logic/BossAILogic.zlogic" in graph_paths
        assert "Assets/Logic/BossCombatLogic.zlogic" in graph_paths
        assert "Assets/Logic/BossHealthLogic.zlogic" in graph_paths


class TestBossAnimations:
    def test_boss_idle_exists(self):
        clip_path = project_root / "Assets" / "Animations" / "Clips" / "BossIdle.zanim"
        assert clip_path.exists()

    def test_boss_run_exists(self):
        clip_path = project_root / "Assets" / "Animations" / "Clips" / "BossRun.zanim"
        assert clip_path.exists()

    def test_boss_attack_exists(self):
        clip_path = project_root / "Assets" / "Animations" / "Clips" / "BossAttack.zanim"
        assert clip_path.exists()

    def test_boss_heavy_attack_exists(self):
        clip_path = project_root / "Assets" / "Animations" / "Clips" / "BossHeavyAttack.zanim"
        assert clip_path.exists()

    def test_boss_hit_exists(self):
        clip_path = project_root / "Assets" / "Animations" / "Clips" / "BossHit.zanim"
        assert clip_path.exists()

    def test_boss_death_exists(self):
        clip_path = project_root / "Assets" / "Animations" / "Clips" / "BossDeath.zanim"
        assert clip_path.exists()


class TestBossController:
    def test_boss_controller_exists(self):
        controller_path = project_root / "Assets" / "Animations" / "BossController.zcontroller"
        assert controller_path.exists()

    def test_boss_controller_valid_json(self):
        controller_path = project_root / "Assets" / "Animations" / "BossController.zcontroller"
        data = json.loads(controller_path.read_text(encoding="utf-8"))
        assert data.get("format") == "zennity.animation_controller"

    def test_boss_controller_has_states(self):
        controller_path = project_root / "Assets" / "Animations" / "BossController.zcontroller"
        data = json.loads(controller_path.read_text(encoding="utf-8"))
        states = [s.get("name") for s in data["layers"][0].get("states", [])]
        assert "Idle" in states
        assert "Run" in states
        assert "Attack" in states
        assert "HeavyAttack" in states
        assert "Hit" in states
        assert "Death" in states

    def test_boss_controller_has_triggers(self):
        controller_path = project_root / "Assets" / "Animations" / "BossController.zcontroller"
        data = json.loads(controller_path.read_text(encoding="utf-8"))
        parameters = data.get("parameters", [])
        param_names = {p.get("name") for p in parameters}
        assert "attack" in param_names
        assert "heavy_attack" in param_names
        assert "dead" in param_names


class TestBossLogics:
    def test_boss_ai_logic_exists(self):
        logic_path = project_root / "Assets" / "Logic" / "BossAILogic.zlogic"
        assert logic_path.exists()

    def test_boss_ai_logic_valid_json(self):
        logic_path = project_root / "Assets" / "Logic" / "BossAILogic.zlogic"
        data = json.loads(logic_path.read_text(encoding="utf-8"))
        assert data.get("format") == "zennity.generic_graph"

    def test_boss_combat_logic_exists(self):
        logic_path = project_root / "Assets" / "Logic" / "BossCombatLogic.zlogic"
        assert logic_path.exists()

    def test_boss_combat_logic_has_attack_trigger(self):
        logic_path = project_root / "Assets" / "Logic" / "BossCombatLogic.zlogic"
        data = json.loads(logic_path.read_text(encoding="utf-8"))
        node_ids = [n.get("id") for n in data.get("nodes", [])]
        assert "set_normal_attack" in node_ids or "set_heavy_attack" in node_ids

    def test_boss_health_logic_exists(self):
        logic_path = project_root / "Assets" / "Logic" / "BossHealthLogic.zlogic"
        assert logic_path.exists()

    def test_boss_health_logic_has_death_check(self):
        logic_path = project_root / "Assets" / "Logic" / "BossHealthLogic.zlogic"
        data = json.loads(logic_path.read_text(encoding="utf-8"))
        node_ids = [n.get("id") for n in data.get("nodes", [])]
        assert "check_dead" in node_ids
        assert "set_dead_trigger" in node_ids


class TestLevel2:
    def test_level2_has_boss(self):
        scene_path = project_root / "Assets" / "Scenes" / "Level2.zscene"
        data = json.loads(scene_path.read_text(encoding="utf-8"))
        boss = next((o for o in data.get("objects", []) if o.get("name") == "Boss"), None)
        assert boss is not None
        assert boss.get("type") == "Prefab"
        assert boss.get("prefab") == "Assets/Prefabs/Boss.zprfb"

    def test_level2_no_regular_enemies(self):
        scene_path = project_root / "Assets" / "Scenes" / "Level2.zscene"
        data = json.loads(scene_path.read_text(encoding="utf-8"))
        enemies = [o for o in data.get("objects", []) if o.get("name") == "Enemy"]
        assert len(enemies) == 0

    def test_level2_has_player_and_camera(self):
        scene_path = project_root / "Assets" / "Scenes" / "Level2.zscene"
        data = json.loads(scene_path.read_text(encoding="utf-8"))
        player = next((o for o in data.get("objects", []) if o.get("name") == "Player"), None)
        camera = next((o for o in data.get("objects", []) if o.get("name") == "Camera"), None)
        assert player is not None
        assert camera is not None


class TestHUDBoss:
    def test_hud_has_boss_health_bar(self):
        ui_path = project_root / "Assets" / "UI" / "HUD.zui"
        data = json.loads(ui_path.read_text(encoding="utf-8"))
        widgets = [w.get("name") for w in data.get("widgets", [])]
        assert "BossHealthBar" in widgets

    def test_hud_has_boss_name_label(self):
        ui_path = project_root / "Assets" / "UI" / "HUD.zui"
        data = json.loads(ui_path.read_text(encoding="utf-8"))
        widgets = [w.get("name") for w in data.get("widgets", [])]
        assert "BossNameLabel" in widgets

    def test_boss_health_bar_is_progress_bar(self):
        ui_path = project_root / "Assets" / "UI" / "HUD.zui"
        data = json.loads(ui_path.read_text(encoding="utf-8"))
        boss_bar = next((w for w in data.get("widgets", [])
                        if w.get("name") == "BossHealthBar"), None)
        assert boss_bar is not None
        assert boss_bar.get("type") == "ProgressBar"


class TestZeroPython:
    def test_no_python_boss_scripts(self):
        boss_path = project_root / "Assets" / "Prefabs" / "Boss.zprfb"
        content = boss_path.read_text(encoding="utf-8")
        assert "boss.py" not in content.lower()
        assert "boss_ai.py" not in content.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
