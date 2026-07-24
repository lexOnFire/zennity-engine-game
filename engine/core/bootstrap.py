"""Engine Bootstrap.

Entry point for initializing the Zennity Engine.
Responsible for auto-discovering EngineProviders and booting the core.
"""
import importlib
import inspect
import pkgutil
from typing import List, Type, Dict, Any, Optional

from engine.core.context import EngineContext
from engine.core.provider import EngineProvider
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
    def boot(cls, config: Optional[Dict[str, Any]] = None) -> EngineContext:
        """
        Starts the engine following the lifecycle:
        1. Create EngineContext
        2. Discover Providers
        3. Register Services
        4. Boot Providers
        5. Initialize Services
        """
        context = EngineContext(config=config)
        
        # 1. Discover all providers
        provider_classes = cls._discover_providers()
        
        # Instantiate providers
        # Optionally, we could sort them by dependencies if they declare any
        # For now, CoreProvider should naturally be self-contained
        providers = [p() for p in provider_classes]
        
        # 2. Register Services phase
        for provider in providers:
            provider.register_services(context)
            
        # 3. Boot Providers phase
        for provider in providers:
            provider.boot(context)
            
        # 4. Initialize Services
        context.services.initialize_all()
        
        return context
