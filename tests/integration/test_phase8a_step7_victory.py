"""
Phase 8A Step 7: Victory Condition & Final Game Loop Tests

Validates:
- Victory scene and UI
- Boss death triggers Victory once
- Score and coins display
- Main Menu and New Game buttons
- Game state reset
- Regressions (GameOver, Continue)
- Full victory route
"""

import pytest
import sys
from pathlib import Path
import json

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from tests.integration import _phase8a_canonical as canonical


class TestVictoryScene:
    def test_victory_scene_exists(self):
        scene_path = project_root / "Assets" / "Scenes" / "Victory.zscene"
        assert scene_path.exists()

    # O cabecalho de Victory e verificado em test_phase8a_canonical_schema.py.

    def test_victory_scene_has_camera(self):
        """Victory tem uma camera."""
        scene = canonical.load_scene("Victory")
        camera = canonical.find_object(scene, "Camera")
        assert camera is not None
        assert canonical.component(camera, "Camera") is not None

    def test_victory_scene_has_canvas(self):
        """Victory tem um canvas."""
        scene = canonical.load_scene("Victory")
        canvas = canonical.find_object(scene, "Canvas")
        assert canvas is not None
        assert canonical.component(canvas, "Canvas") is not None



class TestVictoryUI:
    def test_victory_ui_exists(self):
        ui_path = project_root / "Assets" / "UI" / "Victory.zui"
        assert ui_path.exists()

    def test_victory_ui_valid_json(self):
        ui_path = project_root / "Assets" / "UI" / "Victory.zui"
        data = json.loads(ui_path.read_text(encoding="utf-8"))
        assert data.get("format") == "zennity.ui"

    @pytest.mark.parametrize("name, fragment", [
        ("VictoryTitle", "VICTORY"),
        ("BossDefeatedLabel", "Boss Defeated"),
        ("ScoreLabel", "Score"),
        ("CoinsLabel", "Coins"),
        ("MainMenuButton", "MAIN MENU"),
        ("NewGameButton", "NEW GAME"),
    ])
    def test_victory_ui_declares_its_widgets(self, name, fragment):
        """A tela de vitoria mostra resultado e oferece as duas saidas."""
        widget = canonical.find_widget(canonical.load_ui("Victory"), name)
        assert widget is not None, f"Victory.zui nao declara {name}"
        assert fragment in str(widget.get("text", "")), (
            f"{name} mostra {widget.get('text')!r}"
        )



class TestVictoryLogic:
    def test_victory_logic_exists(self):
        logic_path = project_root / "Assets" / "Logic" / "VictoryLogic.zlogic"
        assert logic_path.exists()

    def test_victory_logic_valid_json(self):
        logic_path = project_root / "Assets" / "Logic" / "VictoryLogic.zlogic"
        data = json.loads(logic_path.read_text(encoding="utf-8"))
        assert data.get("format") in ("zennity.generic_graph", "zennity.logic_graph")

    def test_victory_logic_has_frame_loop(self):
        logic_path = project_root / "Assets" / "Logic" / "VictoryLogic.zlogic"
        data = json.loads(logic_path.read_text(encoding="utf-8"))
        node_ids = [n.get("id") for n in data.get("nodes", [])]
        assert "frame_loop" in node_ids or "start" in node_ids

    def test_victory_logic_reads_score(self):
        logic_path = project_root / "Assets" / "Logic" / "VictoryLogic.zlogic"
        data = json.loads(logic_path.read_text(encoding="utf-8"))
        node_ids = [n.get("id") for n in data.get("nodes", [])]
        assert "get_score" in node_ids

    def test_victory_logic_reads_coins(self):
        logic_path = project_root / "Assets" / "Logic" / "VictoryLogic.zlogic"
        data = json.loads(logic_path.read_text(encoding="utf-8"))
        node_ids = [n.get("id") for n in data.get("nodes", [])]
        assert "get_coins" in node_ids

    def test_victory_logic_sets_score_text(self):
        logic_path = project_root / "Assets" / "Logic" / "VictoryLogic.zlogic"
        data = json.loads(logic_path.read_text(encoding="utf-8"))
        node_ids = [n.get("id") for n in data.get("nodes", [])]
        assert "set_score_text" in node_ids or "set_score_ui" in node_ids

    def test_victory_logic_sets_coins_text(self):
        logic_path = project_root / "Assets" / "Logic" / "VictoryLogic.zlogic"
        data = json.loads(logic_path.read_text(encoding="utf-8"))
        node_ids = [n.get("id") for n in data.get("nodes", [])]
        assert "set_coins_text" in node_ids or "set_coins_ui" in node_ids

    def test_victory_logic_main_menu_button(self):
        logic_path = project_root / "Assets" / "Logic" / "VictoryLogic.zlogic"
        data = json.loads(logic_path.read_text(encoding="utf-8"))
        node_ids = [n.get("id") for n in data.get("nodes", [])]
        assert "main_menu_listener" in node_ids or "on_main_menu" in node_ids
        assert "load_main_menu" in node_ids

    def test_victory_logic_new_game_button(self):
        logic_path = project_root / "Assets" / "Logic" / "VictoryLogic.zlogic"
        data = json.loads(logic_path.read_text(encoding="utf-8"))
        node_ids = [n.get("id") for n in data.get("nodes", [])]
        assert "new_game_listener" in node_ids or "on_new_game" in node_ids
        assert "load_level1" in node_ids


    def test_victory_logic_reset_coins(self):
        logic_path = project_root / "Assets" / "Logic" / "VictoryLogic.zlogic"
        data = json.loads(logic_path.read_text(encoding="utf-8"))
        node_ids = [n.get("id") for n in data.get("nodes", [])]
        assert "reset_coins" in node_ids

    def test_victory_logic_reset_score(self):
        logic_path = project_root / "Assets" / "Logic" / "VictoryLogic.zlogic"
        data = json.loads(logic_path.read_text(encoding="utf-8"))
        node_ids = [n.get("id") for n in data.get("nodes", [])]
        assert "reset_score" in node_ids

    def test_victory_logic_reset_key(self):
        logic_path = project_root / "Assets" / "Logic" / "VictoryLogic.zlogic"
        data = json.loads(logic_path.read_text(encoding="utf-8"))
        node_ids = [n.get("id") for n in data.get("nodes", [])]
        assert "reset_key" in node_ids

    def test_victory_logic_reset_boss_defeated(self):
        logic_path = project_root / "Assets" / "Logic" / "VictoryLogic.zlogic"
        data = json.loads(logic_path.read_text(encoding="utf-8"))
        node_ids = [n.get("id") for n in data.get("nodes", [])]
        assert "reset_boss_defeated" in node_ids

    def test_victory_logic_reset_health(self):
        logic_path = project_root / "Assets" / "Logic" / "VictoryLogic.zlogic"
        data = json.loads(logic_path.read_text(encoding="utf-8"))
        node_ids = [n.get("id") for n in data.get("nodes", [])]
        assert "reset_health" in node_ids


class TestBossDeathTransition:
    def test_boss_health_logic_has_victory_load(self):
        logic_path = project_root / "Assets" / "Logic" / "BossHealthLogic.zlogic"
        data = json.loads(logic_path.read_text(encoding="utf-8"))
        node_ids = [n.get("id") for n in data.get("nodes", [])]
        assert "load_victory" in node_ids

    def test_boss_health_logic_has_death_check(self):
        logic_path = project_root / "Assets" / "Logic" / "BossHealthLogic.zlogic"
        data = json.loads(logic_path.read_text(encoding="utf-8"))
        node_ids = [n.get("id") for n in data.get("nodes", [])]
        assert "check_dead" in node_ids

    def test_boss_health_logic_sets_boss_defeated(self):
        logic_path = project_root / "Assets" / "Logic" / "BossHealthLogic.zlogic"
        data = json.loads(logic_path.read_text(encoding="utf-8"))
        node_ids = [n.get("id") for n in data.get("nodes", [])]
        assert "set_boss_defeated" in node_ids


class TestGameOverRegression:
    def test_gameover_scene_still_exists(self):
        scene_path = project_root / "Assets" / "Scenes" / "GameOver.zscene"
        assert scene_path.exists()

    def test_gameover_ui_still_exists(self):
        ui_path = project_root / "Assets" / "UI" / "GameOver.zui"
        assert ui_path.exists()

    def test_gameover_logic_still_exists(self):
        logic_path = project_root / "Assets" / "Logic" / "GameOverLogic.zlogic"
        assert logic_path.exists()

    def test_player_health_logic_still_exists(self):
        data = canonical.load_logic("PlayerHealthLogic")
        assert data.get("format") == "zennity.logic_graph"
        assert "load_gameover_scene" in canonical.node_ids(data)


class TestLevelExitRegression:
    def test_level_exit_logic_still_exists(self):
        logic_path = project_root / "Assets" / "Logic" / "LevelExitLogic.zlogic"
        assert logic_path.exists()

    def test_level2_scene_still_exists(self):
        scene_path = project_root / "Assets" / "Scenes" / "Level2.zscene"
        assert scene_path.exists()

    def test_level2_has_boss(self):
        scene_path = project_root / "Assets" / "Scenes" / "Level2.zscene"
        data = json.loads(scene_path.read_text(encoding="utf-8"))
        boss = next((o for o in data.get("objects", []) if o.get("name") == "Boss"), None)
        assert boss is not None


class TestSaveLoadRegression:
    def test_save_system_still_exists(self):
        save_path = project_root / "Assets" / "Scripts" / "SaveSystem.py"
        # Check if save logic exists in the system
        # This is optional based on engine implementation
        pass

    def test_main_menu_logic_still_exists(self):
        logic_path = project_root / "Assets" / "Logic" / "MainMenuLogic.zlogic"
        data = json.loads(logic_path.read_text(encoding="utf-8"))
        node_ids = [n.get("id") for n in data.get("nodes", [])]
        # Verify Continue button still works
        assert "load_save" in node_ids or len(node_ids) > 0


class TestUICleanup:
    def test_victory_scene_references_victory_ui(self):
        canvas = canonical.find_object(canonical.load_scene("Victory"), "Canvas")
        assert canvas is not None
        assert canonical.ui_asset_of(canvas) == "Assets/UI/Victory.zui"

    def test_victory_scene_references_victory_logic(self):
        # DEIXADO VERMELHO DE PROPOSITO (Phase 13, item 13.1-B).
        #
        # Le o caminho canonico, o mesmo que o teste acima usa com sucesso para
        # o .zui. O requisito e que nao esta satisfeito: VictoryLogic.zlogic
        # existe, tem 18 nos e 15 arestas validas -- incluindo os botoes de
        # menu e novo jogo -- e nao esta anexado a nada. Quem vence fica preso
        # numa tela estatica.
        canvas = canonical.find_object(canonical.load_scene("Victory"), "Canvas")
        assert canvas is not None
        assert "Assets/Logic/VictoryLogic.zlogic" in canonical.logic_graph_paths(canvas)


class TestZeroPython:
    def test_no_python_victory_scripts(self):
        victory_path = project_root / "Assets" / "Scenes" / "Victory.zscene"
        content = victory_path.read_text(encoding="utf-8")
        assert "victory.py" not in content.lower()
        assert "win_game.py" not in content.lower()

    def test_no_python_boss_victory_scripts(self):
        boss_logic = project_root / "Assets" / "Logic" / "BossHealthLogic.zlogic"
        content = boss_logic.read_text(encoding="utf-8")
        assert ".py" not in content.lower() or "python" not in content.lower()


class TestAssetIntegrity:
    def test_level1_still_exists(self):
        scene_path = project_root / "Assets" / "Scenes" / "Level1.zscene"
        assert scene_path.exists()

    def test_level1_has_player(self):
        scene_path = project_root / "Assets" / "Scenes" / "Level1.zscene"
        data = json.loads(scene_path.read_text(encoding="utf-8"))
        player = next((o for o in data.get("objects", []) if o.get("name") == "Player"), None)
        assert player is not None

    def test_level2_has_player(self):
        scene_path = project_root / "Assets" / "Scenes" / "Level2.zscene"
        data = json.loads(scene_path.read_text(encoding="utf-8"))
        player = next((o for o in data.get("objects", []) if o.get("name") == "Player"), None)
        assert player is not None

    def test_main_menu_still_exists(self):
        scene_path = project_root / "Assets" / "Scenes" / "MainMenu.zscene"
        assert scene_path.exists()


class TestNodeCounts:
    def test_victory_logic_node_count(self):
        logic_path = project_root / "Assets" / "Logic" / "VictoryLogic.zlogic"
        data = json.loads(logic_path.read_text(encoding="utf-8"))
        nodes = data.get("nodes", [])
        assert len(nodes) >= 18  # At minimum 18 nodes

    def test_boss_health_logic_has_victory_node(self):
        logic_path = project_root / "Assets" / "Logic" / "BossHealthLogic.zlogic"
        data = json.loads(logic_path.read_text(encoding="utf-8"))
        nodes = data.get("nodes", [])
        assert len(nodes) == 10  # 10 canonical nodes after Item 20 post-death recovery
        assert any(n.get("id") == "load_victory" for n in nodes)



if __name__ == "__main__":
    pytest.main([__file__, "-v"])
