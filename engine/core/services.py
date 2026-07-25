"""Zennity Engine Service Locator (IoC Container)."""
from typing import Dict, Type, TypeVar, Any, Optional, List, Tuple
from abc import ABC, abstractmethod

T = TypeVar('T', bound='IService')

class IService(ABC):
    """Base interface for all engine services."""
    
    @abstractmethod
    def initialize(self) -> None:
        """Called when the service is registered and the engine starts."""
        pass
        
    @abstractmethod
    def shutdown(self) -> None:
        """Called when the engine shuts down."""
        pass
        
    def reload(self) -> None:
        """Optional: Hot-reload service resources."""
        pass
        
    def validate(self) -> bool:
        """Optional: Check health of the service."""
        return True


class EngineServices:
    """Service Locator for the Zennity Engine."""
    
    def __init__(self):
        self._services: Dict[Type[IService], IService] = {}
    
    def register(self, service_type: Type[T], instance: T) -> None:
        """Registers a service instance."""
        self._services[service_type] = instance
        
    def get(self, service_type: Type[T]) -> T:
        """Retrieves a service instance. Raises KeyError if not found."""
        if service_type not in self._services:
            raise KeyError(f"Service {service_type.__name__} is not registered.")
        return self._services[service_type]  # type: ignore
        
    def try_get(self, service_type: Type[T]) -> Tuple[bool, Optional[T]]:
        """Safely attempts to retrieve a service, returning (success, instance)."""
        instance = self._services.get(service_type)
        return (instance is not None, instance) # type: ignore
        
    def get_optional(self, service_type: Type[T]) -> Optional[T]:
        """Retrieves a service instance if it exists, otherwise returns None."""
        return self._services.get(service_type) # type: ignore
        
    def has(self, service_type: Type[IService]) -> bool:
        """Checks if a service is registered."""
        return service_type in self._services
        
    def list_services(self) -> List[Type[IService]]:
        """Returns a list of all registered service types."""
        return list(self._services.keys())
        
    def initialize_all(self, context=None) -> None:
        """Initializes all registered services and validates their health."""
        for service_type, service in self._services.items():
            service.initialize()
            if not service.validate():
                # Store warning/error in diagnostics if context is passed
                if context and hasattr(context, "diagnostics"):
                    context.diagnostics.setdefault("service_errors", []).append(
                        f"Validation failed for service: {service_type.__name__}"
                    )
            
    def shutdown_all(self) -> None:
        """Shuts down all services in reverse registration order."""
        for service in reversed(list(self._services.values())):
            service.shutdown()
            
    def clear(self) -> None:
        """Clears all registered services."""
        self._services.clear()
