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
    hydrate_logic_graphs,
)
from editor.runtime.viewport_logic_api import PlayLogicAPI
from editor.runtime.viewport_session_orchestrator import ViewportSessionOrchestrator


DEMO = Path("Assets/Demos/PortalStation")


def test_portal_station_demo_covers_every_visual_editor_tab() -> None:
    expected = {
        "PortalTerminal.zlogic", "StationDrone.zbehavior",
        "StationGuide.zdialogue", "PortalGlow.zmat",
        "PortalAnimator.zanimator", "PortalHUD.zui",
        "PortalStation.zscene",
    }
    assert expected <= {path.name for path in DEMO.iterdir()}


def test_portal_station_logic_graph_is_valid() -> None:
    graph = load_logic_graph(DEMO / "PortalTerminal.zlogic")
    errors = [
        issue for issue in validate_logic_graph(graph)
        if issue.get("level") == "error"
    ]
    assert errors == []


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
    assert {"PortalCore", "PortalTerminal", "StationDrone", "PortalUICanvas"} <= objects.keys()
    assert objects["PortalTerminal"]["logic_assets"] == [
        "Assets/Demos/PortalStation/PortalTerminal.zlogic"
    ]
    assert objects["StationDrone"]["behavior"]["controller_path"].endswith(
        "StationDroneRuntime.zbehavior"
    )

    assert hydrate_logic_graphs(objects, Path.cwd())
    assert objects["PortalTerminal"]["logic_graphs"][0]["graph"]["name"] == "PortalTerminal"
    assert hydrate_behavior_controllers(objects, Path.cwd())
    assert objects["StationDrone"]["behavior"]["controller"]["initial_state"] == "Patrol"
    assert hydrate_animator_controllers(objects, Path.cwd())
    assert objects["PortalCore"]["animator"]["controller"]["initial_state"] == "Closed"


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
    runtime = LogicGraphRuntime(
        graph, BlackboardStore(), "PortalTerminal", bus
    )
    runtime.start(api)
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
