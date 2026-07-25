from engine.core.provider import EngineProvider
from engine.core.context import EngineContext

class CoreProvider(EngineProvider):
    depends_on = []
    def register_services(self, context: EngineContext) -> None:
        # Em breve, EventBus, Logger e AssetManager também virão para cá
        pass
        
    def boot(self, context: EngineContext) -> None:
        pass
