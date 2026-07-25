"""Zennity Engine Service Locator (IoC Container)."""
from typing import Dict, Type, TypeVar, Any, Optional, List, Tuple
from abc import ABC, abstractmethod
import time

from engine.core.lifecycle import ServiceState, ServiceScope

T = TypeVar('T', bound='IService')

class IService(ABC):
    """Base interface for all engine services."""
    
    def __init__(self):
        self.state: ServiceState = ServiceState.CREATED
        self.scope: ServiceScope = ServiceScope.ENGINE
        self.depends_on: List[Type['IService']] = []
    
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
    
    def __init__(self, parent: Optional['EngineServices'] = None):
        self._services: Dict[Type[IService], IService] = {}
        self.parent = parent
    
    def register(self, service_type: Type[T], instance: T) -> None:
        """Registers a service instance."""
        self._services[service_type] = instance
        instance.state = ServiceState.REGISTERED
        
    def get(self, service_type: Type[T]) -> T:
        """Retrieves a service instance. Raises KeyError if not found."""
        if service_type in self._services:
            return self._services[service_type]  # type: ignore
        if self.parent:
            return self.parent.get(service_type)
        raise KeyError(f"Service {service_type.__name__} is not registered in this scope.")
        
    def try_get(self, service_type: Type[T]) -> Tuple[bool, Optional[T]]:
        """Safely attempts to retrieve a service, returning (success, instance)."""
        instance = self._services.get(service_type)
        if instance is None and self.parent:
            return self.parent.try_get(service_type)
        return (instance is not None, instance) # type: ignore
        
    def get_optional(self, service_type: Type[T]) -> Optional[T]:
        """Retrieves a service instance if it exists, otherwise returns None."""
        instance = self._services.get(service_type)
        if instance is None and self.parent:
            return self.parent.get_optional(service_type)
        return instance # type: ignore
        
    def has(self, service_type: Type[IService]) -> bool:
        """Checks if a service is registered."""
        if service_type in self._services:
            return True
        if self.parent:
            return self.parent.has(service_type)
        return False
        
    def list_services(self) -> List[Type[IService]]:
        """Returns a list of all registered service types (including parent)."""
        local_keys = list(self._services.keys())
        if self.parent:
            # Combine keys but local overrides parent if duplicate
            return list(set(local_keys + self.parent.list_services()))
        return local_keys

    def _topological_sort_services(self) -> List[Type[IService]]:
        """Sorts registered services based on their depends_on property."""
        graph = {sType: set(svc.depends_on) for sType, svc in self._services.items()}
        
        # We only care about dependencies that are within THIS container.
        # If a dependency is in the parent container, it should already be initialized.
        for deps in graph.values():
            deps.intersection_update(set(self._services.keys()))
            
        sorted_types = []
        no_deps = [sType for sType, deps in graph.items() if not deps]
        
        while no_deps:
            node = no_deps.pop(0)
            sorted_types.append(node)
            
            for sType, deps in list(graph.items()):
                if node in deps:
                    deps.remove(node)
                    if not deps:
                        no_deps.append(sType)
                        del graph[sType]
                        
        if any(deps for deps in graph.values()):
            cycle_nodes = [t.__name__ for t, deps in graph.items() if deps]
            raise RuntimeError(f"Circular dependency detected among services: {', '.join(cycle_nodes)}")
            
        return sorted_types
        
    def initialize_all(self, context=None) -> None:
        """Initializes all registered services and validates their health."""
        if context and not hasattr(context, "diagnostics"):
            context = None # Fallback safety
            
        if context:
            if "service_boot_times" not in context.diagnostics:
                context.diagnostics["service_boot_times"] = {}
            if "health_reports" not in context.diagnostics:
                context.diagnostics["health_reports"] = {}
            if "service_errors" not in context.diagnostics:
                context.diagnostics["service_errors"] = []
            
        sorted_types = self._topological_sort_services()
        
        for service_type in sorted_types:
            service = self._services[service_type]
            service_name = service_type.__name__
            if service.state == ServiceState.REGISTERED:
                t_start = time.perf_counter()
                errors = []
                
                try:
                    service.initialize()
                    service.state = ServiceState.INITIALIZED
                    
                    if not service.validate():
                        service.state = ServiceState.FAILED
                        msg = f"Validation failed for service: {service_name}"
                        errors.append(msg)
                        if context:
                            context.diagnostics["service_errors"].append(msg)
                    else:
                        service.state = ServiceState.RUNNING
                        
                except Exception as e:
                    service.state = ServiceState.FAILED
                    msg = f"Exception initializing service {service_name}: {str(e)}"
                    errors.append(msg)
                    if context:
                        context.diagnostics["service_errors"].append(msg)
                        
                boot_time = time.perf_counter() - t_start
                if context:
                    context.diagnostics["service_boot_times"][service_name] = boot_time
                    context.diagnostics["health_reports"][service_name] = {
                        "state": service.state.name,
                        "boot_time_ms": boot_time * 1000.0,
                        "errors": errors
                    }
            
    def shutdown_all(self) -> None:
        """Shuts down all services in reverse registration (or dependency) order."""
        try:
            sorted_types = self._topological_sort_services()
            shutdown_order = reversed(sorted_types)
        except RuntimeError:
            # If graph is broken somehow on shutdown, just use dict reverse order
            shutdown_order = reversed(list(self._services.keys()))
            
        for service_type in shutdown_order:
            service = self._services[service_type]
            if service.state in (ServiceState.RUNNING, ServiceState.INITIALIZED):
                service.shutdown()
                service.state = ServiceState.STOPPED
            
    def clear(self) -> None:
        """Clears all registered services."""
        self._services.clear()
        
    def generate_dependency_graph_mermaid(self) -> str:
        """Generates a Mermaid JS graph of service dependencies."""
        lines = ["graph TD;"]
        
        for sType, svc in self._services.items():
            s_name = sType.__name__
            if svc.state == ServiceState.FAILED:
                lines.append(f"    {s_name}[{s_name}]:::failed;")
            else:
                lines.append(f"    {s_name}[{s_name}];")
                
            for dep in svc.depends_on:
                dep_name = dep.__name__
                lines.append(f"    {s_name} -->|depends on| {dep_name};")
                
        lines.append("    classDef failed fill:#ffcccc,stroke:#ff0000,stroke-width:2px;")
        return "\n".join(lines)
