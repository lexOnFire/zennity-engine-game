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
from engine.graph.runtime import (
    GraphCompiler,
    CompiledGraph,
    GraphExecutor,
    GraphExecutionContext,
)
from editor.widgets.generic_graph_editor import GenericGraphEditorWidget
from editor.material_graph.material_dock import MaterialGraphEditorDock


def test_graph_execution_framework():
    """Valida a compilação e execução de grafos pelo GraphCompiler e GraphExecutor."""
    graph_raw = {
        "name": "TestShader",
        "nodes": [
            {"id": "ColorNode", "type": "material.color_constant", "inputs": {"value": [1.0, 0.0, 0.0, 1.0]}},
            {"id": "OutputNode", "type": "material.pbr_output", "inputs": {}},
        ],
        "connections": [],
    }

    compiled = GraphCompiler.compile(graph_raw)
    assert compiled.name == "TestShader"
    assert len(compiled.instructions) == 2

    executor = GraphExecutor()
    context = GraphExecutionContext()
    result = executor.execute_graph(compiled, context)
    assert result is not None
    assert "ColorNode" in context.node_outputs


def test_material_provider_boots_metadata(qapp):
    """Valida o registro automático dos metadados de Material via MaterialProvider."""
    context = EngineBootstrap.boot()
    manager = context.services.get(MetadataManager)

    asset_def = manager.get(AssetTypeDefinition, "material_graph")
    assert asset_def is not None
    assert ".zmat" in asset_def.extensions

    nodes = manager.get_all(NodeDefinition)
    node_ids = {n.id for n in nodes}
    assert "material.texture_sample" in node_ids
    assert "material.color_constant" in node_ids
    assert "material.float_constant" in node_ids
    assert "material.vector_math" in node_ids
    assert "material.pbr_output" in node_ids


def test_material_graph_editor_dock_specialization(qapp):
    """Valida a 3ª especialização do GenericGraphEditorWidget para Materiais."""
    context = EngineBootstrap.boot()
    dock = MaterialGraphEditorDock()
    assert dock.graph_editor.category_filter == "Material"
    assert dock.graph_editor.node_palette.topLevelItemCount() >= 1
