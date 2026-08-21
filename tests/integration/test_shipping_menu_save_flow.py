"""
Integration tests for Main Menu, New Game & Continue Save/Load Flow.
Phase 13 Item 13.1-E Non-Vacuity Suite.
"""
from __future__ import annotations

import json
from pathlib import Path
import pytest

from engine.core.save_manager import SaveManager
from engine.logic.graph_asset import load_logic_graph, normalize_logic_graph
from engine.logic.runtime.core import LogicGraphRuntime
from engine.logic.event_bus import LogicEventBus, LogicEvent


class MockGameHost:
    def __init__(self, save_dir: Path):
        self.save_path = str(save_dir)
        self.save_manager = SaveManager(save_directory=save_dir)
        self.loaded_scenes: list[str] = []
        self.quit_called = False
        self.variables: dict[str, Any] = {}

    def set_variable(self, name: str, value: Any) -> None:
        self.variables[name] = value

    def load_scene(self, scene_path: str) -> bool:
        self.loaded_scenes.append(str(scene_path))
        return True

    def open_scene(self, scene_path: str) -> bool:
        return self.load_scene(scene_path)

    def quit(self) -> None:
        self.quit_called = True

    def stop(self) -> None:
        self.quit_called = True


def test_main_menu_ui_continue_button_initially_disabled():
    """A - NO SAVE: ContinueButton must start disabled in MainMenu.zui."""
    zui_path = Path("Assets/UI/MainMenu.zui")
    assert zui_path.exists()
    data = json.loads(zui_path.read_text(encoding="utf-8"))
    canvas = data.get("canvas", {})
    children = canvas.get("children", [])
    continue_btn = next((c for c in children if c.get("name") == "ContinueButton"), None)
    assert continue_btn is not None
    assert continue_btn.get("enabled") is False
    assert continue_btn.get("event") != "load_scene"
    assert not continue_btn.get("scene_path")


def test_main_menu_ui_new_game_button_has_no_direct_load_scene():
    """NewGameButton must not directly hijack navigation via load_scene."""
    zui_path = Path("Assets/UI/MainMenu.zui")
    data = json.loads(zui_path.read_text(encoding="utf-8"))
    canvas = data.get("canvas", {})
    children = canvas.get("children", [])
    new_game_btn = next((c for c in children if c.get("name") == "NewGameButton"), None)
    assert new_game_btn is not None
    assert new_game_btn.get("event") != "load_scene"
    assert not new_game_btn.get("scene_path")


def test_main_menu_logic_check_save_flow_on_start(tmp_path: Path):
    """B - SAVE EXISTS: When save exists, start event triggers has_save -> set_widget_enabled."""
    save_mgr = SaveManager(save_directory=tmp_path)
    save_mgr.save_game(
        slot_name="autosave",
        project_variables={"coins": 10},
        scene_name="Assets/Scenes/Level1.zscene"
    )
    assert save_mgr.save_exists("autosave")

    game = MockGameHost(tmp_path)
    graph_path = Path("Assets/Logic/MainMenuLogic.zlogic")
    raw_graph = load_logic_graph(graph_path)
    normalized = normalize_logic_graph(raw_graph)

    event_bus = LogicEventBus()
    runtime = LogicGraphRuntime(normalized, event_bus=event_bus)
    runtime.start(game)

    assert "check_save_exists" in runtime.executed_nodes
    assert "enable_continue" in runtime.executed_nodes


def test_main_menu_new_game_flow_resets_state_and_loads_level1(tmp_path: Path):
    """C - NEW GAME: Resets state variables and requests Level1 exactly once."""
    game = MockGameHost(tmp_path)
    graph_path = Path("Assets/Logic/MainMenuLogic.zlogic")
    raw_graph = load_logic_graph(graph_path)
    normalized = normalize_logic_graph(raw_graph)

    event_bus = LogicEventBus()
    runtime = LogicGraphRuntime(normalized, event_bus=event_bus)
    runtime.start(game)

    game.set_variable("coins", 50)
    game.set_variable("score", 999)
    game.set_variable("health", 10)
    game.set_variable("has_key", True)

    event_bus.emit("ui.button_clicked", payload={"widget_name": "NewGameButton", "button": "NewGameButton"})
    event_bus.dispatch()

    assert game.variables.get("coins") == 0
    assert game.variables.get("score") == 0
    assert game.variables.get("health") == 100
    assert game.variables.get("has_key") is False

    assert game.loaded_scenes == ["Assets/Scenes/Level1.zscene"]


def test_main_menu_continue_flow_loads_saved_scene_and_state(tmp_path: Path):
    """D & E - CONTINUE: Restores saved variables and saved scene from SaveManager."""
    save_mgr = SaveManager(save_directory=tmp_path)
    save_mgr.save_game(
        slot_name="autosave",
        project_variables={"coins": 99, "score": 1234, "health": 75, "has_key": True},
        scene_name="Assets/Scenes/Level2.zscene"
    )

    game = MockGameHost(tmp_path)
    graph_path = Path("Assets/Logic/MainMenuLogic.zlogic")
    raw_graph = load_logic_graph(graph_path)
    normalized = normalize_logic_graph(raw_graph)

    event_bus = LogicEventBus()
    runtime = LogicGraphRuntime(normalized, event_bus=event_bus)
    runtime.start(game)

    event_bus.emit("ui.button_clicked", payload={"widget_name": "ContinueButton", "button": "ContinueButton"})
    event_bus.dispatch()

    assert runtime.variables.get("coins") == 99 or (hasattr(runtime, "_variables") and runtime._variables.get("coins") == 99)
    assert runtime.variables.get("score") == 1234 or (hasattr(runtime, "_variables") and runtime._variables.get("score") == 1234)
    assert runtime.variables.get("health") == 75 or (hasattr(runtime, "_variables") and runtime._variables.get("health") == 75)
    assert runtime.variables.get("has_key") is True or (hasattr(runtime, "_variables") and runtime._variables.get("has_key") is True)

    assert game.loaded_scenes == ["Assets/Scenes/Level2.zscene"]
    assert len(game.loaded_scenes) == 1


def test_main_menu_exit_button_flow(tmp_path: Path):
    """Exit button triggers app.quit."""
    game = MockGameHost(tmp_path)
    graph_path = Path("Assets/Logic/MainMenuLogic.zlogic")
    raw_graph = load_logic_graph(graph_path)
    normalized = normalize_logic_graph(raw_graph)

    event_bus = LogicEventBus()
    runtime = LogicGraphRuntime(normalized, event_bus=event_bus)
    runtime.start(game)

    event_bus.emit("ui.button_clicked", payload={"widget_name": "ExitButton", "button": "ExitButton"})
    event_bus.dispatch()
    assert game.quit_called is True


def test_main_menu_no_save_safety(tmp_path: Path):
    """H - NO SAVE SAFETY: When no save exists, Continue cannot load game or level."""
    game = MockGameHost(tmp_path)
    graph_path = Path("Assets/Logic/MainMenuLogic.zlogic")
    raw_graph = load_logic_graph(graph_path)
    normalized = normalize_logic_graph(raw_graph)

    event_bus = LogicEventBus()
    runtime = LogicGraphRuntime(normalized, event_bus=event_bus)
    runtime.start(game)

    # Sem save, check_save_exists não ativa enable_continue
    assert "enable_continue" not in runtime.executed_nodes

    # Se por ventura um clique for forçado no ContinueButton sem save:
    event_bus.emit("ui.button_clicked", payload={"widget_name": "ContinueButton", "button": "ContinueButton"})
    event_bus.dispatch()

    # Nenhuma cena deve ter sido carregada
    assert game.loaded_scenes == []


def test_main_menu_no_double_scene_load_on_new_game(tmp_path: Path):
    """F - NO DOUBLE LOAD: Single New Game button click triggers exactly 1 scene load."""
    game = MockGameHost(tmp_path)
    graph_path = Path("Assets/Logic/MainMenuLogic.zlogic")
    raw_graph = load_logic_graph(graph_path)
    normalized = normalize_logic_graph(raw_graph)

    event_bus = LogicEventBus()
    runtime = LogicGraphRuntime(normalized, event_bus=event_bus)
    runtime.start(game)

    event_bus.emit("ui.button_clicked", payload={"widget_name": "NewGameButton", "button": "NewGameButton"})
    event_bus.dispatch()

    assert len(game.loaded_scenes) == 1
    assert game.loaded_scenes == ["Assets/Scenes/Level1.zscene"]


def test_victory_and_gameover_assets_remain_sound():
    """I - VICTORY / GAMEOVER REGRESSION: Ensure Victory and GameOver logic/UI remain valid."""
    victory_logic = Path("Assets/Logic/VictoryLogic.zlogic")
    gameover_logic = Path("Assets/Logic/GameOverLogic.zlogic")
    assert victory_logic.exists()
    assert gameover_logic.exists()
    v_data = json.loads(victory_logic.read_text(encoding="utf-8"))
    g_data = json.loads(gameover_logic.read_text(encoding="utf-8"))
    assert v_data.get("format") == "zennity.logic_graph"
    assert g_data.get("format") == "zennity.logic_graph"