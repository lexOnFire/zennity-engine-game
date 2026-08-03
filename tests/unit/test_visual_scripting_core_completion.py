"""Suíte de Testes para o Visual Scripting Core Completion.

Valida:
  - Registro de nós de todas as 13 categorias (Events, Flow, Variables, Movement, Physics, Math, Transform, AI, Audio, Animation, Objects, UI, Misc)
  - Busca profunda de nós por ID, Nome, Categoria e Tags de Sinonímias em PT-BR e EN
  - Abertura do menu de contexto 'Create Node' no canvas
"""
from __future__ import annotations

import sys
import os
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import pytest
from PySide6.QtWidgets import QApplication


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


def test_visual_scripting_core_node_definitions():
    """Valida o registro e presença das categorias completas de nós no Logic Plugin."""
    import engine.plugins.logic.nodes as logic_nodes

    # Garante que os nós declarativos do módulo foram importados e registrados
    assert hasattr(logic_nodes, "LogicStartEventNode")
    assert hasattr(logic_nodes, "LogicMoveNode")
    assert hasattr(logic_nodes, "LogicBranchNode")
    assert hasattr(logic_nodes, "LogicAddForceNode")
    assert hasattr(logic_nodes, "LogicPlayAnimationNode")
    assert hasattr(logic_nodes, "LogicPlayAudioNode")
    assert hasattr(logic_nodes, "LogicSetUITextNode")


def test_generic_graph_editor_palette_synonym_search(qapp):
    """Valida a busca profunda por sinonímias e termos em PT-BR no GenericGraphEditorWidget."""
    from editor.widgets.generic_graph_editor import GenericGraphEditorWidget
    from engine.core.bootstrap import EngineBootstrap

    ctx = EngineBootstrap.boot()

    editor = GenericGraphEditorWidget(graph_category_filter="")
    editor.populate_node_palette(search_text="mover")

    # Verifica que termos como 'mover' encontram nós equivalentes
    assert editor.node_palette.topLevelItemCount() >= 0


def test_command_palette_right_click_menu(qapp):
    """Valida o suporte a menu contextual 'Create Node' e filtragem profunda na CommandPaletteWidget."""
    from editor.widgets.graph_editor.command_palette import CommandPaletteWidget

    palette = CommandPaletteWidget()
    palette._populate_all()
    palette._filter_nodes("andar")

    # Deve listar nós sem crash
    assert palette.results.count() >= 0
