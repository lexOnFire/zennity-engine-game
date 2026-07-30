import json
from pathlib import Path

import pytest
from PySide6.QtWidgets import QApplication

from engine.core.bootstrap import EngineBootstrap
from engine.logic.graph_asset import load_logic_graph, validate_logic_graph
from engine.ui.runtime import UICanvas, widget_from_dict
from editor.widgets.generic_graph_editor import GenericGraphEditorWidget


DEMO = Path("Assets/Demos/PortalStation")


def test_portal_station_demo_covers_every_visual_editor_tab() -> None:
    expected = {
        "PortalTerminal.zlogic", "StationDrone.zbehavior",
        "StationGuide.zdialogue", "PortalGlow.zmat",
        "PortalAnimator.zanimator", "PortalHUD.zui",
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
