from engine.core.provider import EngineProvider
from engine.core.context import EngineContext

class LogicProvider(EngineProvider):
    """Provides Logic Runtime services and syncs metadata."""
    
    def register_services(self, context: EngineContext) -> None:
        pass
        
    def boot(self, context: EngineContext) -> None:
        print("LogicProvider.boot EXECUTADO!")
        # Força o carregamento dos decorators
        import engine.logic.runtime.nodes.actions_nodes
        import engine.logic.runtime.nodes.components_nodes
        import engine.logic.runtime.nodes.event_nodes
        import engine.logic.runtime.nodes.flow_nodes
        import engine.logic.runtime.nodes.math_nodes
        import engine.logic.runtime.nodes.misc_nodes
        import engine.logic.runtime.nodes.movement_nodes
        import engine.logic.runtime.nodes.prefab_nodes
        import engine.logic.runtime.nodes.scene_nodes
        import engine.logic.runtime.nodes.string_nodes
        import engine.logic.runtime.nodes.dynamic_ui_nodes

        from engine.logic.runtime.registry import sync_logic_registry_to_metadata
        from engine.metadata.manager import MetadataManager
        from engine.logic.node_definitions.dynamic_ui_nodes import (
            CreateUILabelNode, CreateUIProgressBarNode, CreateUIButtonNode,
            CreateUIImageNode, DestroyUIWidgetNode, UpdateUIWidgetPropertyNode,
            GetUIWidgetPropertyNode
        )

        # Registra as definições dos nós dinâmicos
        manager = context.services.get_optional(MetadataManager)
        if manager:
            manager.register(CreateUILabelNode.__node_definition__)
            manager.register(CreateUIProgressBarNode.__node_definition__)
            manager.register(CreateUIButtonNode.__node_definition__)
            manager.register(CreateUIImageNode.__node_definition__)
            manager.register(DestroyUIWidgetNode.__node_definition__)
            manager.register(UpdateUIWidgetPropertyNode.__node_definition__)
            manager.register(GetUIWidgetPropertyNode.__node_definition__)

        sync_logic_registry_to_metadata(context)
