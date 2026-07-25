import pytest
from PySide6.QtWidgets import QApplication

@pytest.fixture(scope="module", autouse=True)
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


from engine.core.bootstrap import EngineBootstrap
from engine.metadata.manager import MetadataManager
from engine.core.metadata import NodeDefinition
from engine.core.metadata.asset import AssetTypeDefinition
from editor.widgets.generic_graph_editor import GenericGraphEditorWidget
from editor.behavior_tree.behavior_tree_dock import BehaviorTreeEditorDock


def test_ai_provider_boots_metadata(qapp):
    """Valida o registro automático dos metadados de Behavior Tree via AIProvider."""
    context = EngineBootstrap.boot()
    manager = context.services.get(MetadataManager)

    asset_def = manager.get(AssetTypeDefinition, "behavior_tree")
    assert asset_def is not None
    assert ".zbehavior" in asset_def.extensions

    nodes = manager.get_all(NodeDefinition)
    node_ids = {n.id for n in nodes}
    assert "bt.selector" in node_ids
    assert "bt.sequence" in node_ids
    assert "bt.inverter" in node_ids
    assert "bt.wait" in node_ids
    assert "bt.move_to" in node_ids


def test_generic_graph_editor_widget(qapp):
    """Valida a inicialização do editor de grafos genérico."""
    context = EngineBootstrap.boot()
    editor = GenericGraphEditorWidget(graph_category_filter="Behavior Tree")
    assert editor.category_filter == "Behavior Tree"
    assert editor.node_palette.topLevelItemCount() >= 1


def test_behavior_tree_editor_dock_specialization(qapp):
    """Valida que o BehaviorTreeEditorDock reutiliza o GenericGraphEditorWidget sem código duplicado."""
    context = EngineBootstrap.boot()
    dock = BehaviorTreeEditorDock()
    assert dock.graph_editor.category_filter == "Behavior Tree"
