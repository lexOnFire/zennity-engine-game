import json
from pathlib import Path

import pytest
from PySide6.QtWidgets import QApplication

from engine.core.bootstrap import EngineBootstrap
from engine.logic.graph_asset import load_logic_graph, validate_logic_graph
from engine.logic.blackboard import BlackboardStore
from engine.logic.event_bus import LogicEventBus
from engine.logic.runtime.core import LogicGraphRuntime
from engine.ui.runtime import UICanvas, widget_from_dict
from editor.widgets.generic_graph_editor import GenericGraphEditorWidget
from editor.scene_persistence import EditorScenePersistence
from editor.runtime.viewport_asset_hydration import (
    hydrate_animator_controllers,
    hydrate_behavior_controllers,
    hydrate_dialogues,
    hydrate_logic_graphs,
)
from editor.runtime.viewport_logic_api import PlayLogicAPI
from editor.runtime.viewport_session_orchestrator import ViewportSessionOrchestrator


DEMO = Path("Assets/Demos/PortalStation")


def test_portal_station_demo_covers_every_visual_editor_tab() -> None:
    expected = {
        "PortalTerminal.zlogic", "StationDrone.zbehavior",
        "PortalPilot.zlogic", "EnergyCell.zlogic",
        "StationGuide.zdialogue", "PortalGlow.zmat",
        "PortalAnimator.zanimator", "PortalHUD.zui",
        "PortalStation.zscene",
    }
    assert expected <= {path.name for path in DEMO.iterdir()}


def test_portal_station_logic_graph_is_valid() -> None:
    for path in DEMO.glob("*.zlogic"):
        graph = load_logic_graph(path)
        assert validate_logic_graph(graph) == [], path.name


def test_portal_station_specialized_graphs_are_editable_documents() -> None:
    categories = {
        "StationDrone.zbehavior": "Behavior Tree",
        "StationGuide.zdialogue": "Dialogue",
        "PortalGlow.zmat": "Material",
        "PortalAnimator.zanimator": "Animation",
    }
    for filename, category in categories.items():
        payload = json.loads((DEMO / filename).read_text(encoding="utf-8"))
        assert payload["format"] == "zennity.generic_graph"
        assert payload["category"] == category
        assert len(payload["nodes"]) >= 3
        assert payload["edges"]


def test_portal_station_ui_is_editable_ui_canvas() -> None:
    payload = json.loads((DEMO / "PortalHUD.zui").read_text(encoding="utf-8"))
    canvas = widget_from_dict(payload["canvas"])
    assert isinstance(canvas, UICanvas)
    assert canvas.children[0].children[-1].name == "ActivatePortal"


def test_portal_station_scene_loads_as_one_runtime_ready_experience() -> None:
    payload, snapshots, typed = EditorScenePersistence(Path.cwd()).load(
        DEMO / "PortalStation.zscene"
    )
    objects = {item["name"]: item for item in snapshots}

    assert typed
    assert payload["visual_logic_workspace"].keys() == {
        "logic", "behavior_tree", "dialogue", "material", "animator", "ui"
    }
    assert {
        "PortalCore", "PortalTerminal", "StationDrone", "PortalUICanvas",
        "PortalPilot", "EnergyCellA", "EnergyCellB", "EnergyCellC", "PortalUIEnergy",
    } <= objects.keys()
    assert objects["PortalTerminal"]["logic_assets"] == [
        "Assets/Demos/PortalStation/PortalTerminal.zlogic"
    ]
    assert objects["StationDrone"]["behavior"]["controller_path"].endswith(
        "StationDroneRuntime.zbehavior"
    )
    assert objects["PortalPilot"]["logic_assets"] == [
        "Assets/Demos/PortalStation/PortalPilot.zlogic"
    ]
    assert objects["PortalUIEnergy"]["ui"]["max_value"] == 3.0

    assert hydrate_logic_graphs(objects, Path.cwd())
    assert objects["PortalTerminal"]["logic_graphs"][0]["graph"]["name"] == "PortalTerminal"
    assert hydrate_behavior_controllers(objects, Path.cwd())
    assert objects["StationDrone"]["behavior"]["controller"]["initial_state"] == "Patrol"
    assert hydrate_animator_controllers(objects, Path.cwd())
    assert objects["PortalCore"]["animator"]["controller"]["initial_state"] == "Closed"
    assert hydrate_dialogues(objects, Path.cwd())
    assert objects["PortalTerminal"]["dialogue"]["graph"]["category"] == "Dialogue"


def test_portal_button_event_changes_gameplay_state() -> None:
    graph = load_logic_graph(DEMO / "PortalTerminal.zlogic")
    terminal = {
        "name": "PortalTerminal", "tag": "Interactable",
        "active": True, "rotation": 0.0,
        "logic_events": [{"command": "activate_portal", "value": {"source": "PortalUIButton"}}],
    }
    portal = {
        "name": "PortalCore", "tag": "Portal",
        "active": True, "rotation": 0.0,
    }
    objects = {"PortalTerminal": terminal, "PortalCore": portal}
    bus = LogicEventBus()
    api = PlayLogicAPI("PortalTerminal", terminal, None, objects)
    store = BlackboardStore()
    runtime = LogicGraphRuntime(graph, store, "PortalTerminal", bus)
    runtime.start(api)
    store.set("project", "energy", 3.0, "PortalTerminal")
    hud_values = []
    orchestrator = ViewportSessionOrchestrator(
        objects=objects,
        logic_runtimes={"PortalTerminal": [("PortalTerminal.zlogic", runtime)]},
        behavior_runners={}, logic_modules={},
        logic_apis={"PortalTerminal": api}, animator_controllers={},
        logic_event_bus=lambda: bus,
        runtime_world=api.runtime_world,
        hud_entries=type("_Hud", (), {
            "set_entry": lambda _self, value: hud_values.append(value),
            "remove_entry": lambda *_args: None,
        })(),
        emit=lambda _message: None, play_audio=lambda *_args: None,
        pause_audio=lambda _paused: None, state_hook=lambda *_args: None,
    )

    orchestrator._apply_logic_instructions("PortalTerminal", terminal)
    bus.dispatch()
    orchestrator._apply_logic_instructions("PortalTerminal", terminal)

    assert portal["rotation"] == 45.0
    assert hud_values[-1]["text"] == "PORTAL ATIVO • sistema pronto para travessia"


def test_energy_cell_collection_updates_blackboard_hud_audio_and_object() -> None:
    graph = load_logic_graph(DEMO / "EnergyCell.zlogic")
    cell = {"name": "EnergyCellA", "tag": "EnergyCell", "active": True, "x": 0.0, "y": 0.0}
    energy_ui = {"name": "PortalUIEnergy", "ui": {"type": "progress_bar", "value": 0.0, "max_value": 3.0}}
    player = {"name": "PortalPilot", "tag": "Player", "active": True}
    objects = {"EnergyCellA": cell, "PortalUIEnergy": energy_ui, "PortalPilot": player}
    api = PlayLogicAPI("EnergyCellA", cell, None, objects)
    store = BlackboardStore()
    runtime = LogicGraphRuntime(graph, store, "EnergyCellA")
    runtime.start(api)

    runtime.trigger_event("event_trigger_enter", api, payload=type("Other", (), {"tag": "Player"})())

    assert store.get("project", "energy", "EnergyCellA") == 1.0
    assert cell["active"] is False
    commands = [event["command"] for event in cell["logic_events"]]
    assert "set_ui_progress" in commands
    assert "play_sound" in commands


def test_portal_pilot_moves_with_wasd() -> None:
    graph = load_logic_graph(DEMO / "PortalPilot.zlogic")

    class Game:
        name = "PortalPilot"
        x = y = rotation = 0.0
        @staticmethod
        def key(name): return name == "d"
        @staticmethod
        def key_pressed(_name): return False
        def move(self, dx, dy=0.0): self.x += dx; self.y += dy

    game = Game()
    runtime = LogicGraphRuntime(graph, BlackboardStore(), game.name)
    runtime.start(game)
    runtime.update(game, 0.5)

    assert game.x == 120.0 and game.y == 0.0


@pytest.mark.parametrize(
    ("filename", "category"),
    [
        ("StationDrone.zbehavior", "Behavior Tree"),
        ("StationGuide.zdialogue", "Dialogue"),
        ("PortalGlow.zmat", "Material"),
        ("PortalAnimator.zanimator", "Animation"),
    ],
)
def test_demo_specialized_documents_open_in_their_real_tabs(
    filename: str, category: str
) -> None:
    app = QApplication.instance() or QApplication([])
    EngineBootstrap.boot()
    editor = GenericGraphEditorWidget(category)
    try:
        assert editor.load_document(DEMO / filename)
        assert len(editor.canvas.scene.nodes) >= 3
        assert editor.canvas.scene.edges
    finally:
        editor.deleteLater()
        app.processEvents()
