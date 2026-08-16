"""Testes para polimento de UX do Blackboard e Variáveis (Item 10.5)."""
from __future__ import annotations

import pytest
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from editor.widgets.logic_graph_editor import LogicGraphEditor


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_blackboard_workspace_variables_and_filtering(qapp, tmp_path):
    graph = {
        "format": "zennity.logic_graph",
        "version": 1,
        "nodes": [],
        "edges": [],
        "variables": {
            "health": {"type": "number", "scope": "object", "default": 100},
            "move_speed": {"type": "number", "scope": "object", "default": 5.0},
            "score": {"type": "number", "scope": "scene", "default": 0},
            "difficulty": {"type": "text", "scope": "project", "default": "Normal"},
        },
    }

    editor = LogicGraphEditor()
    editor.project_root = tmp_path
    editor.show()

    graph_file = tmp_path / "TestVariables.zlogic"
    editor.set_graph(graph, graph_file)

    # 1. Verifica se aba se chama Variáveis
    tab_titles = [editor.library_tabs.tabText(i) for i in range(editor.library_tabs.count())]
    assert "Variáveis" in tab_titles
    assert "Dados" not in tab_titles

    # 2. Inicialmente todas as 4 variáveis visíveis
    assert editor.blackboard_tree.topLevelItemCount() == 4

    # 3. Filtro por Scope: Objeto
    idx = editor.blackboard_filter_scope_combo.findData("object")
    editor.blackboard_filter_scope_combo.setCurrentIndex(idx)
    assert editor.blackboard_tree.topLevelItemCount() == 2
    names = [editor.blackboard_tree.topLevelItem(i).text(0) for i in range(2)]
    assert "health" in names and "move_speed" in names

    # 4. Search + Scope filter combinados
    editor.blackboard_search_edit.setText("speed")
    assert editor.blackboard_tree.topLevelItemCount() == 1
    assert editor.blackboard_tree.topLevelItem(0).text(0) == "move_speed"

    # Reset filtros
    editor.blackboard_search_edit.clear()
    editor.blackboard_filter_scope_combo.setCurrentIndex(0) # all
    assert editor.blackboard_tree.topLevelItemCount() == 4


def test_blackboard_node_creation_and_drag_drop_helper(qapp, tmp_path):
    graph = {
        "format": "zennity.logic_graph",
        "version": 1,
        "nodes": [],
        "edges": [],
        "variables": {
            "health": {"type": "number", "scope": "object", "default": 100},
        },
    }

    editor = LogicGraphEditor()
    editor.project_root = tmp_path
    editor.show()

    graph_file = tmp_path / "TestDrag.zlogic"
    editor.set_graph(graph, graph_file)

    # 1. Criação via _create_blackboard_accessor_node (Get Variable) na coordenada (250, 150)
    item_get = editor._create_blackboard_accessor_node("health", "object", "get_variable", position=(250.0, 150.0))
    assert item_get is not None
    assert len(editor.graph["nodes"]) == 1
    node_get = editor.graph["nodes"][0]
    assert node_get["type"] == "get_variable"
    assert node_get["properties"]["name"] == "health"
    assert node_get["properties"]["scope"] == "object"
    assert node_get["position"] == [250.0, 150.0]

    # 2. Criação de Set Variable
    item_set = editor._create_blackboard_accessor_node("health", "object", "set_variable", position=(400.0, 150.0))
    assert item_set is not None
    assert len(editor.graph["nodes"]) == 2
    node_set = editor.graph["nodes"][1]
    assert node_set["type"] == "set_variable"
    assert node_set["properties"]["name"] == "health"
    assert node_set["properties"]["scope"] == "object"
    assert node_set["properties"]["value"] == 100

    # 3. Teste de contagem de referências
    refs = editor._count_variable_references("health", "object")
    assert refs == 2
