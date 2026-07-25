"""EngineProvider do sistema de Visual Scripting da Zennity Engine."""
from engine.core.provider import EngineProvider
from engine.core.context import EngineContext
from engine.metadata.manager import MetadataManager
from engine.core.metadata.asset import AssetTypeDefinition
from engine.scripting.visual_scripting_nodes import (
    EventOnStartNode,
    EventOnUpdateNode,
    IfElseNode,
    SetPositionNode,
    LogMessageNode,
)


class VisualScriptingProvider(EngineProvider):
    """Provedor oficial de metadados de Visual Scripting."""

    def register_services(self, context: EngineContext) -> None:
        pass

    def boot(self, context: EngineContext) -> None:
        manager = context.services.get_optional(MetadataManager)
        if not manager:
            return

        # 1. Registro do Asset de Script Visual (.zscriptgraph)
        manager.register(AssetTypeDefinition(
            id="visual_script_graph",
            title_key="asset.visual_script_graph",
            extensions=[".zscriptgraph"],
        ))

        # 2. Registro dos Nós de Visual Scripting no Graph Framework
        manager.register(EventOnStartNode.__node_definition__)
        manager.register(EventOnUpdateNode.__node_definition__)
        manager.register(IfElseNode.__node_definition__)
        manager.register(SetPositionNode.__node_definition__)
        manager.register(LogMessageNode.__node_definition__)
