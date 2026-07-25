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
        
        from engine.logic.runtime.registry import sync_logic_registry_to_metadata
        sync_logic_registry_to_metadata(context)
