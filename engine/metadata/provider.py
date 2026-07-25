"""Metadata Provider."""
from engine.core.provider import EngineProvider
from engine.core.lifecycle import BootProfile
from engine.metadata.manager import MetadataManager

class MetadataProvider(EngineProvider):
    """Provides the MetadataManager to the Engine Core."""
    
    profiles = [BootProfile.ALL]
    
    def register_services(self, context: 'EngineContext') -> None:
        from engine.metadata.manager import MetadataManager
        from engine.metadata.validator import MetadataValidator
        context.services.register(MetadataManager, MetadataManager())
        context.services.register(MetadataValidator, MetadataValidator())
