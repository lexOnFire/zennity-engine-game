"""Engine Bootstrap.

Entry point for initializing the Zennity Engine.
Responsible for auto-discovering EngineProviders and booting the core.
"""
import importlib
import inspect
import pkgutil
import time
from typing import List, Type, Dict, Any, Optional

from engine.core.context import EngineContext
from engine.core.provider import EngineProvider
from engine.core.lifecycle import BootProfile
import engine


class EngineBootstrap:
    """Orchestrates the startup sequence of the engine."""
    
    @classmethod
    def _discover_providers(cls) -> List[Type[EngineProvider]]:
        """Scans the `engine` package for all EngineProvider implementations."""
        providers: List[Type[EngineProvider]] = []
        
        # Recursively walk the 'engine' package
        def _walk_package(pkg):
            if not hasattr(pkg, '__path__'):
                return
            for _, module_name, is_pkg in pkgutil.iter_modules(pkg.__path__, pkg.__name__ + "."):
                try:
                    module = importlib.import_module(module_name)
                    # Find providers in this module
                    for name, obj in inspect.getmembers(module):
                        if inspect.isclass(obj) and issubclass(obj, EngineProvider) and obj is not EngineProvider:
                            if obj not in providers:
                                providers.append(obj)
                    
                    if is_pkg:
                        _walk_package(module)
                except ImportError:
                    pass
        
        _walk_package(engine)
        return providers

    @classmethod
    def _topological_sort(cls, providers: List[Type[EngineProvider]]) -> List[Type[EngineProvider]]:
        """Sorts providers based on their depends_on property to resolve dependency graph."""
        graph = {p: set(getattr(p, 'depends_on', [])) for p in providers}
        
        sorted_providers = []
        # Find all nodes with no dependencies
        no_deps = [p for p, deps in graph.items() if not deps]
        
        while no_deps:
            node = no_deps.pop(0)
            sorted_providers.append(node)
            
            # Remove this node from others' dependencies
            for p, deps in list(graph.items()):
                if node in deps:
                    deps.remove(node)
                    if not deps:
                        no_deps.append(p)
                        del graph[p]
                        
        if any(deps for deps in graph.values()):
            cycle_nodes = [p.__name__ for p, deps in graph.items() if deps]
            raise RuntimeError(f"Circular dependency detected among providers: {', '.join(cycle_nodes)}")
            
        return sorted_providers

    @classmethod
    def boot(cls, config: Optional[Dict[str, Any]] = None, profile: BootProfile = BootProfile.EDITOR) -> EngineContext:
        """
        Starts the engine following the lifecycle:
        1. Create EngineContext
        2. Discover Providers
        3. Register Services
        4. Boot Providers
        5. Initialize Services
        """
        t_start = time.perf_counter()
        
        context = EngineContext(config=config)
        context.diagnostics["active_profile"] = profile.name
        
        # 1. Discover all providers
        provider_classes = cls._discover_providers()
        
        # 1.5 Filter providers by boot profile
        filtered_classes = []
        for p_cls in provider_classes:
            profiles = getattr(p_cls, 'profiles', [BootProfile.ALL])
            if BootProfile.ALL in profiles or profile in profiles:
                filtered_classes.append(p_cls)
        
        # Topological Sort to respect dependencies
        sorted_classes = cls._topological_sort(filtered_classes)
        
        # Instantiate providers
        providers = [p() for p in sorted_classes]
        
        # 2. Register Services phase
        for provider in providers:
            t_prov_start = time.perf_counter()
            provider.register_services(context)
            
            # Initial tracking
            context.diagnostics["provider_boot_times"][provider.__class__.__name__] = time.perf_counter() - t_prov_start
            
        # 3. Boot Providers phase
        for provider in providers:
            t_prov_start = time.perf_counter()
            provider.boot(context)
            
            # Accumulate time
            context.diagnostics["provider_boot_times"][provider.__class__.__name__] += time.perf_counter() - t_prov_start
            
        # 4. Initialize Services (passes context for health check validation)
        context.services.initialize_all(context=context)
        
        context.diagnostics["total_boot_time"] = time.perf_counter() - t_start
        return context
