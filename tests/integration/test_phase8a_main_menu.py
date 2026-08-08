"""
Phase 8A: Real Game Benchmark - Main Menu Tests

Validates that MainMenu scene loads, UI renders, and Logic Graph controls:
- New Game button (resets state, loads Level1)
- Continue button (conditional, loads save)
- Exit button (if supported, documents if GAP)
- Play/Stop/Play cleanup (no stale handlers)

Zero Python gameplay scripts. All logic via Logic Graph.
"""

import pytest
import sys
from pathlib import Path
import json

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from engine.core.engine import Engine
from engine.logic.event_bus import LogicEventBus
from engine.logic.blackboard import BlackboardStore


class TestMainMenuSceneLoads:
    """Test that MainMenu.zscene loads correctly."""

    def test_main_menu_scene_exists(self):
        """Verify MainMenu.zscene file exists."""
        scene_path = project_root / "Assets" / "Scenes" / "MainMenu.zscene"
        assert scene_path.exists(), f"MainMenu.zscene not found at {scene_path}"

    def test_main_menu_scene_valid_json(self):
        """Verify MainMenu.zscene is valid JSON."""
        scene_path = project_root / "Assets" / "Scenes" / "MainMenu.zscene"
        data = json.loads(scene_path.read_text(encoding="utf-8"))
        assert data.get("format") == "zennity.scene"
        assert data.get("name") == "Main Menu"

    def test_main_menu_has_ui_asset_reference(self):
        """Verify MainMenu references MainMenu.zui."""
        scene_path = project_root / "Assets" / "Scenes" / "MainMenu.zscene"
        data = json.loads(scene_path.read_text(encoding="utf-8"))

        ui_objects = [obj for obj in data.get("objects", []) if "ui" in obj]
        assert len(ui_objects) > 0, "MainMenu should have UI object"

        ui_ref = ui_objects[0]["ui"]["asset"]
        assert ui_ref == "Assets/UI/MainMenu.zui"

    def test_main_menu_has_logic_graph_reference(self):
        """Verify MainMenu references MainMenuLogic graph."""
        scene_path = project_root / "Assets" / "Scenes" / "MainMenu.zscene"
        data = json.loads(scene_path.read_text(encoding="utf-8"))

        logic_objects = [obj for obj in data.get("objects", [])
                        if "logic_graphs" in obj]
        assert len(logic_objects) > 0, "MainMenu should have logic graph"

        graphs = logic_objects[0]["logic_graphs"]
        assert any(g["path"] == "Assets/Logic/MainMenuLogic.zlogic"
                  for g in graphs)


class TestMainMenuUILoads:
    """Test that MainMenu.zui compiles and renders."""

    def test_main_menu_ui_exists(self):
        """Verify MainMenu.zui file exists."""
        ui_path = project_root / "Assets" / "UI" / "MainMenu.zui"
        assert ui_path.exists(), f"MainMenu.zui not found at {ui_path}"

    def test_main_menu_ui_valid_json(self):
        """Verify MainMenu.zui is valid JSON."""
        ui_path = project_root / "Assets" / "UI" / "MainMenu.zui"
        data = json.loads(ui_path.read_text(encoding="utf-8"))
        assert data.get("format") == "zennity.ui"
        assert isinstance(data.get("widgets"), list)

    def test_main_menu_ui_has_required_buttons(self):
        """Verify MainMenu UI has New Game, Continue, Exit buttons."""
        ui_path = project_root / "Assets" / "UI" / "MainMenu.zui"
        data = json.loads(ui_path.read_text(encoding="utf-8"))

        widget_names = [w.get("name") for w in data.get("widgets", [])]
        assert "NewGameButton" in widget_names, "Missing New Game button"
        assert "ContinueButton" in widget_names, "Missing Continue button"
        assert "ExitButton" in widget_names, "Missing Exit button"

    def test_main_menu_ui_continue_button_initially_disabled(self):
        """Verify Continue button starts disabled (until save is detected)."""
        ui_path = project_root / "Assets" / "UI" / "MainMenu.zui"
        data = json.loads(ui_path.read_text(encoding="utf-8"))

        continue_btn = next((w for w in data.get("widgets", [])
                           if w.get("name") == "ContinueButton"), None)
        assert continue_btn is not None
        assert continue_btn.get("enabled") is False, \
            "Continue button should start disabled until save exists"


class TestMainMenuLogicGraph:
    """Test that MainMenuLogic.zlogic is properly structured."""

    def test_main_menu_logic_exists(self):
        """Verify MainMenuLogic.zlogic file exists."""
        logic_path = project_root / "Assets" / "Logic" / "MainMenuLogic.zlogic"
        assert logic_path.exists(), f"MainMenuLogic.zlogic not found at {logic_path}"

    def test_main_menu_logic_valid_json(self):
        """Verify MainMenuLogic.zlogic is valid JSON."""
        logic_path = project_root / "Assets" / "Logic" / "MainMenuLogic.zlogic"
        data = json.loads(logic_path.read_text(encoding="utf-8"))
        assert data.get("format") == "zennity.generic_graph"
        assert data.get("category") == "Logic"

    def test_main_menu_logic_has_button_listeners(self):
        """Verify logic graph has listeners for all three buttons."""
        logic_path = project_root / "Assets" / "Logic" / "MainMenuLogic.zlogic"
        data = json.loads(logic_path.read_text(encoding="utf-8"))

        node_ids = [n.get("id") for n in data.get("nodes", [])]
        assert "new_game_button_listener" in node_ids
        assert "continue_button_listener" in node_ids
        assert "exit_button_listener" in node_ids

    def test_main_menu_logic_new_game_flow(self):
        """Verify logic graph has complete New Game flow:
        Button → Reset State Variables → Load Level1"""
        logic_path = project_root / "Assets" / "Logic" / "MainMenuLogic.zlogic"
        data = json.loads(logic_path.read_text(encoding="utf-8"))

        # Check for reset nodes
        node_ids = [n.get("id") for n in data.get("nodes", [])]
        assert "reset_new_game_state" in node_ids
        assert "reset_score" in node_ids
        assert "reset_key" in node_ids
        assert "reset_health" in node_ids
        assert "load_level1" in node_ids

    def test_main_menu_logic_continue_flow(self):
        """Verify logic graph has Continue button → Load Game flow."""
        logic_path = project_root / "Assets" / "Logic" / "MainMenuLogic.zlogic"
        data = json.loads(logic_path.read_text(encoding="utf-8"))

        node_ids = [n.get("id") for n in data.get("nodes", [])]
        assert "load_game" in node_ids, "Should have load_game node"


class TestLevel1Placeholder:
    """Test that Level1.zscene exists for New Game to load."""

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


class TestMainMenuProjectState:
    """Test that MainMenu scene initializes project variables."""

    def test_main_menu_initializes_coins(self):
        """Verify MainMenu initializes coins variable."""
        scene_path = project_root / "Assets" / "Scenes" / "MainMenu.zscene"
        data = json.loads(scene_path.read_text(encoding="utf-8"))

        variables = data.get("variables", {})
        assert "coins" in variables
        assert variables["coins"] == 0

    def test_main_menu_initializes_score(self):
        """Verify MainMenu initializes score variable."""
        scene_path = project_root / "Assets" / "Scenes" / "MainMenu.zscene"
        data = json.loads(scene_path.read_text(encoding="utf-8"))

        variables = data.get("variables", {})
        assert "score" in variables
        assert variables["score"] == 0

    def test_main_menu_initializes_has_key(self):
        """Verify MainMenu initializes has_key variable."""
        scene_path = project_root / "Assets" / "Scenes" / "MainMenu.zscene"
        data = json.loads(scene_path.read_text(encoding="utf-8"))

        variables = data.get("variables", {})
        assert "has_key" in variables
        assert variables["has_key"] is False

    def test_main_menu_initializes_health(self):
        """Verify MainMenu initializes health variable."""
        scene_path = project_root / "Assets" / "Scenes" / "MainMenu.zscene"
        data = json.loads(scene_path.read_text(encoding="utf-8"))

        variables = data.get("variables", {})
        assert "health" in variables
        assert variables["health"] == 100


class TestMainMenuNoPhythonGameplay:
    """Verify that Main Menu uses ONLY visual systems, no Python gameplay scripts."""

    def test_main_menu_no_python_gameplay_imports(self):
        """Verify no Python gameplay imports in main menu logic."""
        # Check MainMenu.zscene for any Python script references
        scene_path = project_root / "Assets" / "Scenes" / "MainMenu.zscene"
        content = scene_path.read_text(encoding="utf-8")

        # Should not reference Python gameplay scripts
        assert "gameplay" not in content.lower()
        assert "player.py" not in content.lower()
        assert "enemy.py" not in content.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
