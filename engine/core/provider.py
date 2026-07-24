"""Engine Provider Interface."""
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from engine.core.context import EngineContext

class EngineProvider(ABC):
    """
    Base class for module providers. 
    A provider registers services to the EngineContext during bootstrap.
    """
    
    @abstractmethod
    def register_services(self, context: 'EngineContext') -> None:
        """
        Phase 1 of bootstrap: Instantiate services and register them in context.services.
        Dependencies on other services should NOT be resolved here.
        """
        pass
        
    def boot(self, context: 'EngineContext') -> None:
        """
        Phase 2 of bootstrap: Called after all providers have registered their services.
        Safe to retrieve other services from context.services here.
        """
        pass
