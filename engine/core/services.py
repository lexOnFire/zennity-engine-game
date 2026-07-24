"""Zennity Engine Service Locator (IoC Container)."""
from typing import Dict, Type, TypeVar, Any
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
    _services: Dict[Type[IService], IService] = {}
    
    @classmethod
    def register(cls, service_type: Type[T], instance: T) -> None:
        """Registers a service instance."""
        cls._services[service_type] = instance
        
    @classmethod
    def get(cls, service_type: Type[T]) -> T:
        """Retrieves a service instance. Raises KeyError if not found."""
        if service_type not in cls._services:
            raise KeyError(f"Service {service_type.__name__} is not registered.")
        return cls._services[service_type] # type: ignore
        
    @classmethod
    def initialize_all(cls) -> None:
        """Initializes all registered services."""
        for service in cls._services.values():
            service.initialize()
            
    @classmethod
    def shutdown_all(cls) -> None:
        """Shuts down all services in reverse registration order."""
        for service in reversed(list(cls._services.values())):
            service.shutdown()
            
    @classmethod
    def clear(cls) -> None:
        cls._services.clear()
