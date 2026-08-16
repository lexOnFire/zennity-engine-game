"""Testes de paleta e instanciação de nós customizados no Logic Editor (D2.4)."""
from __future__ import annotations

from pathlib import Path
import pytest
from PySide6.QtWidgets import QApplication

from engine.logic.custom_node_asset import save_custom_node_asset
from engine.logic.custom_node_registry import get_custom_node_registry
from editor.widgets.logic_graph_editor import LogicGraphEditor


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_palette_displays_and_instantiates_custom_node(tmp_path: Path, qapp):
    """Testa que o Custom Node é descoberto pelo editor e adicionado ao grafo via paleta."""
    custom_dir = tmp_path / "Assets" / "Logic" / "CustomNodes"
    custom_dir.mkdir(parents=True, exist_ok=True)
    znode_file = custom_dir / "multiply_stat.znode"

    save_custom_node_asset(
        znode_file,
        {
            "node_id": "multiply_stat",
            "title": "Multiply Stat",
            "execution_model": "pure_data",
            "inputs": [
                {"name": "val", "type": "number", "default": 10.0},
                {"name": "factor", "type": "number", "default": 3.0},
            ],
            "outputs": [{"name": "stat_out", "type": "number"}],
            "script": "ctx.set_output('stat_out', ctx.get_input('val') * ctx.get_input('factor'))",
        },
    )

    editor = LogicGraphEditor()
    editor.project_path = str(tmp_path)
    get_custom_node_registry(tmp_path).refresh()
    editor._refresh_palette("All")

    # Verifica se o item foi adicionado à paleta
    found_item = None
    for i in range(editor.palette.count()):
        item = editor.palette.item(i)
        if item and item.data(0x0100) == "custom_asset:multiply_stat":
            found_item = item
            break

    assert found_item is not None, "Custom Node não apareceu na paleta do editor"
    assert "Multiply Stat (Custom)" in found_item.text()

    # Simula adicionar o item da paleta no grafo
    initial_node_count = len(editor.graph.get("nodes", []))
    editor._add_palette_item(found_item)

    assert len(editor.graph["nodes"]) == initial_node_count + 1
    added_node = editor.graph["nodes"][-1]
    assert added_node["type"] == "custom_script"
    assert added_node["title"] == "Multiply Stat"
    assert added_node["properties"]["custom_asset_id"] == "multiply_stat"
    assert added_node["properties"]["execution_model"] == "pure_data"
    assert len(added_node["properties"]["inputs"]) == 2
    assert len(added_node["properties"]["outputs"]) == 1
