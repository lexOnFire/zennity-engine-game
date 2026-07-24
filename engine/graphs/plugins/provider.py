from engine.core.provider import EngineProvider
from engine.core.context import EngineContext
from engine.graphs.plugins.manager import PluginManager

class PluginProvider(EngineProvider):
    def register_services(self, context: EngineContext) -> None:
        plugin_manager = PluginManager()
        context.services.register(PluginManager, plugin_manager)
        
    def boot(self, context: EngineContext) -> None:
        # Load all standard plugins automatically during boot
        plugin_manager = context.services.get(PluginManager)
        plugin_manager.load_all_plugins()
