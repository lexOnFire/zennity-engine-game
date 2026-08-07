"""EngineProvider oficial do módulo de Inteligência Artificial e Behavior Trees."""
from engine.core.provider import EngineProvider
from engine.core.context import EngineContext
from engine.metadata.manager import MetadataManager
from engine.core.metadata.asset import AssetTypeDefinition
from engine.ai.behavior_tree_nodes import (
    # Composite
    BTSequenceNode,
    BTSelectorNode,
    # Decorator
    BTRepeatNode,
    BTCooldownNode,
    BTLimiterNode,
    BTInverterNode,
    # Condition
    BTTargetInRangeNode,
    BTHealthCheckNode,
    BTParameterCheckNode,
    BTRandomChanceNode,
    # Action
    BTWaitNode,
    BTIdleNode,
    BTPatrolNode,
    BTChaseNode,
    BTMoveToNode,
    BTAttackNode,
    BTPlayAnimationNode,
    BTSetParameterNode,
    BTLogNode,
    # UI Actions
    BTSetUITextNode,
    BTSetUIProgressNode,
    BTSetUIVisibleNode,
    BTIncrementUIValueNode,
    BTDecrementUIValueNode,
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
        # Composite
        manager.register(BTSequenceNode.__node_definition__)
        manager.register(BTSelectorNode.__node_definition__)
        # Decorator
        manager.register(BTRepeatNode.__node_definition__)
        manager.register(BTCooldownNode.__node_definition__)
        manager.register(BTLimiterNode.__node_definition__)
        manager.register(BTInverterNode.__node_definition__)
        # Condition
        manager.register(BTTargetInRangeNode.__node_definition__)
        manager.register(BTHealthCheckNode.__node_definition__)
        manager.register(BTParameterCheckNode.__node_definition__)
        manager.register(BTRandomChanceNode.__node_definition__)
        # Action
        manager.register(BTWaitNode.__node_definition__)
        manager.register(BTIdleNode.__node_definition__)
        manager.register(BTPatrolNode.__node_definition__)
        manager.register(BTChaseNode.__node_definition__)
        manager.register(BTMoveToNode.__node_definition__)
        manager.register(BTAttackNode.__node_definition__)
        manager.register(BTPlayAnimationNode.__node_definition__)
        manager.register(BTSetParameterNode.__node_definition__)
        manager.register(BTLogNode.__node_definition__)
        # UI Actions
        manager.register(BTSetUITextNode.__node_definition__)
        manager.register(BTSetUIProgressNode.__node_definition__)
        manager.register(BTSetUIVisibleNode.__node_definition__)
        manager.register(BTIncrementUIValueNode.__node_definition__)
        manager.register(BTDecrementUIValueNode.__node_definition__)
