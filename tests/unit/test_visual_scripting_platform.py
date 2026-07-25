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
    GraphExecutor,
    GraphNodeRuntime,
    CompiledGraphInstruction,
    GraphExecutionContext,
)
from editor.widgets.generic_graph_editor import GenericGraphEditorWidget
from editor.visual_scripting.visual_scripting_dock import VisualScriptingEditorDock


class CustomLogNodeRuntime(GraphNodeRuntime):
    def execute(self, instruction: CompiledGraphInstruction, context: GraphExecutionContext) -> str:
        msg = instruction.inputs.get("message", "LogExecuted")
        context.node_outputs[instruction.node_id] = {"msg": msg}
        return msg


def test_graph_node_runtime_dispatch():
    """Valida a execução por despacho dinâmico via GraphNodeRuntime no GraphExecutor."""
    executor = GraphExecutor()
    executor.register_node_runtime("vs.log_message", CustomLogNodeRuntime())

    graph_raw = {
        "name": "ScriptTest",
        "nodes": [
            {"id": "LogNode", "type": "vs.log_message", "inputs": {"message": "ZennityScriptEngine"}},
        ],
        "connections": [],
    }

    compiled = GraphCompiler.compile(graph_raw)
    context = GraphExecutionContext()
    res = executor.execute_graph(compiled, context)
    assert res == "ZennityScriptEngine"
    assert context.node_outputs["LogNode"]["msg"] == "ZennityScriptEngine"


def test_visual_scripting_provider_boots_metadata(qapp):
    """Valida o registro automático dos metadados de Visual Scripting via VisualScriptingProvider."""
    context = EngineBootstrap.boot()
    manager = context.services.get(MetadataManager)

    asset_def = manager.get(AssetTypeDefinition, "visual_script_graph")
    assert asset_def is not None
    assert ".zscriptgraph" in asset_def.extensions

    nodes = manager.get_all(NodeDefinition)
    node_ids = {n.id for n in nodes}
    assert "vs.event_on_start" in node_ids
    assert "vs.event_on_update" in node_ids
    assert "vs.if_else" in node_ids
    assert "vs.set_position" in node_ids
    assert "vs.log_message" in node_ids


def test_visual_scripting_editor_dock_specialization(qapp):
    """Valida o Editor de Scripting Visual completo (Logic Graph Editor restaurado)."""
    context = EngineBootstrap.boot()
    dock = VisualScriptingEditorDock()
    assert dock.graph_editor.category_filter == "Visual Scripting"
    assert hasattr(dock.graph_editor, "palette")
