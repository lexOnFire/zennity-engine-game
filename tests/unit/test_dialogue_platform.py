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
from engine.graph.validation_service import GraphValidationService, GraphValidationError
from engine.core.metadata import NodeDefinition
from engine.core.metadata.asset import AssetTypeDefinition
from editor.widgets.generic_graph_editor import GenericGraphEditorWidget
from editor.dialogue.dialogue_dock import DialogueGraphEditorDock


def test_graph_validation_service():
    """Valida o serviço central de validação de grafos."""
    service = GraphValidationService()
    assert service.validate_connection("exec", "exec") is True
    assert service.validate_connection("float", "int") is True
    assert service.validate_connection("exec", "float") is False

    # Validação de grafo com nós isolados
    nodes = [{"id": "NodeA"}, {"id": "NodeB"}]
    errors = service.validate_graph(nodes, [])
    assert len(errors) == 2
    assert errors[0].error_type == "ORPHAN_NODE"


def test_dialogue_provider_boots_metadata(qapp):
    """Valida o registro automático dos metadados de Diálogo via DialogueProvider."""
    context = EngineBootstrap.boot()
    manager = context.services.get(MetadataManager)

    asset_def = manager.get(AssetTypeDefinition, "dialogue_graph")
    assert asset_def is not None
    assert ".zdialogue" in asset_def.extensions

    nodes = manager.get_all(NodeDefinition)
    node_ids = {n.id for n in nodes}
    assert "dialogue.speech" in node_ids
    assert "dialogue.choice" in node_ids
    assert "dialogue.condition" in node_ids
    assert "dialogue.end" in node_ids
    assert "dialogue.event" in node_ids


def test_dialogue_graph_editor_dock_specialization(qapp):
    """Valida a 2ª especialização do GenericGraphEditorWidget para Diálogos."""
    context = EngineBootstrap.boot()
    dock = DialogueGraphEditorDock()
    assert dock.graph_editor.category_filter == "Dialogue"
    assert dock.graph_editor.node_palette.topLevelItemCount() >= 1

    # Test auto-layout e clipboard
    dock.graph_editor.auto_layout()
    dock.graph_editor.copy_selection()
    assert dock.graph_editor.clipboard_nodes == [{"copied": True}]
    category = dock.graph_editor.node_palette.topLevelItem(0)
    speech = next(
        category.child(i) for i in range(category.childCount())
        if category.child(i).text(0) == "Fala"
    )
    dock.graph_editor.node_palette.itemClicked.emit(speech, 0)
    assert "Conversas" in dock.graph_editor.help_browser.toPlainText()
