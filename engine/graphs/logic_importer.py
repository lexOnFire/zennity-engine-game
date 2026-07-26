from pathlib import Path
from engine.core.context import EngineContext
from engine.metadata.manager import MetadataManager
from engine.core.metadata import GraphDefinition

def import_legacy_zlogic(filepath: Path):
    import json
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    context = EngineContext.current()
    if not context: return None
    manager = context.services.get_optional(MetadataManager)
    if not manager: return None
    
    # Criar um Logic Graph novo e migrar os dados...
    g_def = manager.get(GraphDefinition, "logicgraph")
    if not g_def or not hasattr(g_def, "_graph_class"):
        return None
    graph_class = g_def._graph_class
        
    graph = graph_class()
    # Mock migration
    graph.properties["legacy_imported"] = True
    return graph
