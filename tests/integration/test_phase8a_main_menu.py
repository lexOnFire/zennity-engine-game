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

from tests.integration import _phase8a_canonical as canonical
from engine.core.engine import Engine
from engine.logic.event_bus import LogicEventBus
from engine.logic.blackboard import BlackboardStore


class TestMainMenuSceneLoads:
    """Test that MainMenu.zscene loads correctly."""

    def test_main_menu_scene_exists(self):
        """Verify MainMenu.zscene file exists."""
        scene_path = project_root / "Assets" / "Scenes" / "MainMenu.zscene"
        assert scene_path.exists(), f"MainMenu.zscene not found at {scene_path}"

    # O cabecalho serializado das cinco cenas e verificado em
    # test_phase8a_canonical_schema.py (format_version / scene_name /
    # engine_version). A assercao que existia aqui usava a grafia anterior a
    # 6a3fb0a7 e foi retirada em 13.1-B.

    def test_main_menu_has_ui_asset_reference(self):
        """Verify MainMenu references MainMenu.zui."""
        scene_path = project_root / "Assets" / "Scenes" / "MainMenu.zscene"
        data = json.loads(scene_path.read_text(encoding="utf-8"))

        scene = canonical.load_scene("MainMenu")
        bound = [canonical.ui_asset_of(o) for o in canonical.objects(scene)]
        assert any(bound), "MainMenu should bind a .zui"
        assert "Assets/UI/MainMenu.zui" in bound

    def test_main_menu_has_logic_graph_reference(self):
        """Verify MainMenu references MainMenuLogic graph."""
        scene_path = project_root / "Assets" / "Scenes" / "MainMenu.zscene"
        data = json.loads(scene_path.read_text(encoding="utf-8"))

        scene = canonical.load_scene("MainMenu")
        bound = {
            path
            for obj in canonical.objects(scene)
            for path in canonical.logic_graph_paths(obj)
        }
        assert bound, "MainMenu should bind a logic graph"
        assert "Assets/Logic/MainMenuLogic.zlogic" in bound


class TestMainMenuUILoads:
    """Test that MainMenu.zui compiles and renders."""

    def test_main_menu_ui_exists(self):
        """Verify MainMenu.zui file exists."""
        ui_path = project_root / "Assets" / "UI" / "MainMenu.zui"
        assert ui_path.exists(), f"MainMenu.zui not found at {ui_path}"

    def test_main_menu_ui_valid_json(self):
        """Verify MainMenu.zui is valid JSON."""
        data = canonical.load_ui("MainMenu")
        assert data.get("format") == "zennity.ui"
        # Um .zui e uma arvore a partir de canvas, nao uma lista plana widgets.
        assert isinstance(data.get("canvas"), dict)
        assert canonical.widgets(data), "o canvas nao declara nenhum widget"

    def test_main_menu_ui_has_required_buttons(self):
        """Verify MainMenu UI has New Game, Continue, Exit buttons."""
        names = canonical.widget_names(canonical.load_ui("MainMenu"))
        assert "NewGameButton" in names, "Missing New Game button"
        assert "ContinueButton" in names, "Missing Continue button"
        assert "ExitButton" in names, "Missing Exit button"

    def test_main_menu_ui_continue_button_initially_disabled(self):
        """Verify Continue button starts disabled (until save is detected)."""
        continue_btn = canonical.find_widget(canonical.load_ui("MainMenu"), "ContinueButton")
        assert continue_btn is not None
        assert continue_btn.get("enabled") is False, (
            "Continue button should start disabled until save exists"
        )


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
        # LOGIC_GRAPH_FORMAT desde b3a24b71; "zennity.generic_graph" era a
        # grafia anterior e nenhum .zlogic do repositorio a usa.
        assert data.get("format") == "zennity.logic_graph"
        assert isinstance(data.get("nodes"), list)

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

    # Idem para Level1: cabecalho coberto por test_phase8a_canonical_schema.py.


class TestMainMenuProjectState:
    """Test that MainMenu scene initializes project variables."""

    @pytest.mark.parametrize("variable, value", [
        ("coins", 0),
        ("score", 0),
        ("has_key", False),
        ("health", 100),
    ])
    def test_new_game_resets_project_state(self, variable, value):
        """Starting a new game must clear the previous run's state.

        The scene used to carry a root-level ``variables`` mapping. The
        canonical scene keeps its blackboard under ``blackboard.variables`` and
        the reset itself belongs to the New Game flow, so the requirement is
        checked where it now lives: MainMenuLogic must author a variables.set
        that writes the initial value.
        """
        graph = canonical.load_logic("MainMenuLogic")

        writes = [
            node.get("properties", {})
            for node in graph.get("nodes", [])
            if str(node.get("type")) in {"variables.set", "set_variable"}
        ]
        matching = [w for w in writes if w.get("name") == variable]

        assert matching, f"MainMenuLogic never resets {variable!r}"
        assert any(w.get("value") == value for w in matching), (
            f"MainMenuLogic resets {variable!r} to "
            f"{[w.get('value') for w in matching]}, expected {value!r}"
        )


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
