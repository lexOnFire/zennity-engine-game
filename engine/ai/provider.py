"""EngineProvider oficial do módulo de Inteligência Artificial e Behavior Trees."""
from engine.core.provider import EngineProvider
from engine.core.context import EngineContext
from engine.metadata.manager import MetadataManager
from engine.core.metadata.asset import AssetTypeDefinition
from engine.ai.behavior_tree_nodes import (
    BTSelectorNode,
    BTSequenceNode,
    BTInverterNode,
    BTWaitNode,
    BTMoveToNode,
    BTRepeatNode, BTCooldownNode, BTTargetInRangeNode, BTParameterConditionNode,
    BTChaseNode, BTPatrolNode, BTAttackNode, BTPlayAnimationNode,
)


class AIProvider(EngineProvider):
    """Provedor oficial de metadados e serviços de IA / Behavior Trees."""

    def register_services(self, context: EngineContext) -> None:
        pass

    def boot(self, context: EngineContext) -> None:
        manager = context.services.get_optional(MetadataManager)
        if not manager:
            return

        # 1. Definição do Asset de Behavior Tree (.zbehavior)
        manager.register(AssetTypeDefinition(
            id="behavior_tree",
            title_key="asset.behavior_tree",
            extensions=[".zbehavior"],
        ))

        # 2. Registro dos Nós de Behavior Tree no Graph Framework
        manager.register(BTSelectorNode.__node_definition__)
        manager.register(BTSequenceNode.__node_definition__)
        manager.register(BTInverterNode.__node_definition__)
        manager.register(BTWaitNode.__node_definition__)
        manager.register(BTMoveToNode.__node_definition__)
        manager.register(BTRepeatNode.__node_definition__)
        manager.register(BTCooldownNode.__node_definition__)
        manager.register(BTTargetInRangeNode.__node_definition__)
        manager.register(BTParameterConditionNode.__node_definition__)
        manager.register(BTChaseNode.__node_definition__)
        manager.register(BTPatrolNode.__node_definition__)
        manager.register(BTAttackNode.__node_definition__)
        manager.register(BTPlayAnimationNode.__node_definition__)
