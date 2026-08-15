"""Suíte de testes dedicada para a recuperação da Victory Screen (Phase 9 Item 22).

Valida:
1. VictoryLogic.zlogic possui 0 nós phantom e 0 conexões orphan.
2. Contratos canônicos de portas e nós.
3. Pipeline de inicialização via event_start atualiza ScoreLabel e CoinsLabel com valores reais formatados.
4. Clique no MainMenuButton carrega Assets/Scenes/MainMenu.zscene.
5. Clique no NewGameButton reseta variáveis globais de projeto (coins=0, score=0, has_key=False, boss_defeated=False, health=100) e carrega Assets/Scenes/Level1.zscene.
6. Múltiplos cliques / ciclos de Play/Stop sem duplicação de bindings ou vazamento de estado.
"""

from __future__ import annotations

import pathlib
from typing import Any

import pytest

from engine.logic.graph_asset import (
    NODE_DEFINITIONS,
    NODE_PORT_DEFINITIONS,
    load_logic_graph,
    normalize_logic_graph,
)
from engine.logic.node_definitions.catalogue import ensure_catalogue_loaded, resolve_node_id
from engine.logic.node_system import load_runtime_node_modules
from engine.logic.runtime import LogicGraphRuntime

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
LOGIC_PATH = REPO_ROOT / "Assets" / "Logic" / "VictoryLogic.zlogic"


class MockGame:
    def __init__(self) -> None:
        self.ui_texts: dict[str, str] = {}
        self.loaded_scenes: list[str] = []

    def set_ui_text(self, object_name: str, text: str) -> None:
        self.ui_texts[str(object_name)] = str(text)

    def load_scene(self, scene_path: str) -> bool:
        if scene_path:
            self.loaded_scenes.append(str(scene_path))
            return True
        return False


@pytest.fixture(autouse=True)
def _ensure_catalogue_and_runtime() -> None:
    ensure_catalogue_loaded()
    load_runtime_node_modules()


def test_victory_logic_has_zero_phantoms_and_zero_orphans() -> None:
    raw = load_logic_graph(LOGIC_PATH)
    graph = normalize_logic_graph(raw)
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])
    node_map = {str(n["id"]): n for n in nodes}

    assert len(nodes) == 18
    assert len(edges) == 15

    phantoms = [n for n in nodes if resolve_node_id(str(n.get("type", ""))) not in NODE_DEFINITIONS]
    assert not phantoms, f"Phantoms encontrados: {phantoms}"

    orphans = []
    for e in edges:
        fn = node_map.get(str(e.get("from_node")))
        tn = node_map.get(str(e.get("to_node")))
        fp = str(e.get("from_port", ""))
        tp = str(e.get("to_port", ""))
        if fn:
            ft = resolve_node_id(str(fn.get("type", "")))
            outs = {p for p, _ in NODE_PORT_DEFINITIONS.get(ft, {}).get("outputs", [])}
            if outs and fp not in outs:
                orphans.append(f"{ft}.{fp}>out")
        if tn:
            tt = resolve_node_id(str(tn.get("type", "")))
            ins = {p for p, _ in NODE_PORT_DEFINITIONS.get(tt, {}).get("inputs", [])}
            if ins and tp not in ins:
                orphans.append(f"{tt}.{tp}>in")

    assert not orphans, f"Orphans encontrados: {orphans}"


def test_victory_screen_initialization_updates_labels_with_actual_project_data() -> None:
    graph = normalize_logic_graph(load_logic_graph(LOGIC_PATH))
    game = MockGame()
    runtime = LogicGraphRuntime(graph, object_key="Victory")

    runtime.blackboard.set("project", "score", 750, "global")
    runtime.blackboard.set("project", "coins", 42, "global")

    runtime.start(game)

    assert game.ui_texts.get("ScoreLabel") == "Score: 750.0"
    assert game.ui_texts.get("CoinsLabel") == "Coins: 42.0"


def test_main_menu_button_click_transitions_to_main_menu_scene() -> None:
    graph = normalize_logic_graph(load_logic_graph(LOGIC_PATH))
    game = MockGame()
    runtime = LogicGraphRuntime(graph, object_key="Victory")
    runtime.start(game)

    assert not game.loaded_scenes

    runtime.event_bus.emit("ui.button_clicked", {"widget_name": "MainMenuButton"})
    runtime.event_bus.dispatch()

    assert game.loaded_scenes == ["Assets/Scenes/MainMenu.zscene"]


def test_new_game_button_resets_full_gameplay_state_and_loads_level1() -> None:
    graph = normalize_logic_graph(load_logic_graph(LOGIC_PATH))
    game = MockGame()
    runtime = LogicGraphRuntime(graph, object_key="Victory")

    # Set initial dirty state representing a completed run
    runtime.blackboard.set("project", "coins", 50, "global")
    runtime.blackboard.set("project", "score", 1200, "global")
    runtime.blackboard.set("project", "has_key", True, "global")
    runtime.blackboard.set("project", "boss_defeated", True, "global")
    runtime.blackboard.set("project", "health", 25, "global")

    runtime.start(game)

    # Click New Game button
    runtime.event_bus.emit("ui.button_clicked", {"widget_name": "NewGameButton"})
    runtime.event_bus.dispatch()

    assert game.loaded_scenes == ["Assets/Scenes/Level1.zscene"]

    # Verify every project variable reset to initial defaults
    assert runtime.blackboard.get("project", "coins", "global") == 0.0
    assert runtime.blackboard.get("project", "score", "global") == 0.0
    assert runtime.blackboard.get("project", "has_key", "global") is False
    assert runtime.blackboard.get("project", "boss_defeated", "global") is False
    assert runtime.blackboard.get("project", "health", "global") == 100.0


def test_repeated_play_stop_cycles_maintain_clean_subscriptions() -> None:
    graph = normalize_logic_graph(load_logic_graph(LOGIC_PATH))

    for cycle in range(3):
        game = MockGame()
        runtime = LogicGraphRuntime(graph, object_key="Victory")
        runtime.blackboard.set("project", "score", cycle * 100, "global")
        runtime.blackboard.set("project", "coins", cycle * 5, "global")
        runtime.start(game)

        assert game.ui_texts.get("ScoreLabel") == f"Score: {float(cycle * 100)}"
        assert game.ui_texts.get("CoinsLabel") == f"Coins: {float(cycle * 5)}"

        runtime.event_bus.emit("ui.button_clicked", {"widget_name": "MainMenuButton"})
        runtime.event_bus.dispatch()

        assert game.loaded_scenes == ["Assets/Scenes/MainMenu.zscene"]
