from engine.core.provider import EngineProvider
from engine.core.context import EngineContext

from engine.localization.manager import LocalizationManager

from engine.core.core_provider import CoreProvider

class LocalizationProvider(EngineProvider):
    depends_on = [CoreProvider]
    def register_services(self, context: EngineContext) -> None:
        loc_manager = LocalizationManager()
        # Ensure it loads locales from context directory
        loc_manager.base_locales_dir = context.locales_dir
        context.services.register(LocalizationManager, loc_manager)
        
    def boot(self, context: EngineContext) -> None:
        pass
