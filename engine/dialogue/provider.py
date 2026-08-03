"""EngineProvider do sistema de Diálogos e Narrativa da Zennity Engine."""
from engine.core.provider import EngineProvider
from engine.core.context import EngineContext
from engine.metadata.manager import MetadataManager
from engine.core.metadata.asset import AssetTypeDefinition
from engine.dialogue.dialogue_nodes import (
    DialogueNode,
    ChoiceNode,
    ConditionNode,
    EndNode,
    DialogueEventNode,
)


class DialogueProvider(EngineProvider):
    """Provedor oficial de metadados do sistema de Diálogos."""

    def register_services(self, context: EngineContext) -> None:
        pass

    def boot(self, context: EngineContext) -> None:
        manager = context.services.get_optional(MetadataManager)
        if not manager:
            return

        # 1. Registro do Asset de Diálogo (.zdialogue)
        manager.register(AssetTypeDefinition(
            id="dialogue_graph",
            title_key="asset.dialogue_graph",
            extensions=[".zdialogue"],
        ))

        # 2. Registro dos Nós de Diálogo no Graph Framework
        manager.register(DialogueNode.__node_definition__)
        manager.register(ChoiceNode.__node_definition__)
        manager.register(ConditionNode.__node_definition__)
        manager.register(EndNode.__node_definition__)
        manager.register(DialogueEventNode.__node_definition__)
