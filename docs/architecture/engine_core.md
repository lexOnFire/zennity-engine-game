# Zennity Engine Core Architecture

The Zennity Engine is built on a modular, decoupled architecture driven by an Inversion of Control (IoC) container and a Provider-based initialization lifecycle.

## Overview

Instead of scattered Singletons (`Manager.get_instance()`), the engine state is centralized in an `EngineContext`, which owns an instance of `EngineServices`.

This ensures:
1. **Decoupling**: Modules don't need to import concrete implementations of other modules.
2. **Isolation**: Multiple contexts can exist simultaneously without global namespace pollution.
3. **Observability**: Boot times and health checks are measured at startup.

## Creating a Service

A Service is any class that inherits from `IService` and provides core engine functionality.

```python
from engine.core.services import IService

class MyCustomService(IService):
    def initialize(self) -> None:
        print("Service initialized")
        
    def shutdown(self) -> None:
        print("Service shut down")
        
    def validate(self) -> bool:
        # Perform health checks
        return True
```

## Creating a Provider

Providers act as factories and registrars for Services during the bootstrap process. They dictate *when* and *how* services are created.

```python
from engine.core.provider import EngineProvider
from engine.core.context import EngineContext

class MyCustomProvider(EngineProvider):
    # Declare dependencies to enforce topological sorting during bootstrap
    depends_on = [CoreProvider]
    
    def register_services(self, context: EngineContext) -> None:
        service = MyCustomService()
        context.services.register(MyCustomService, service)
        
    def boot(self, context: EngineContext) -> None:
        # Pre-initialization logic (e.g. hooking up EventBus, scanning directories)
        pass
```

## Bootstrap Lifecycle

When `EngineBootstrap.boot()` is called:

1. `EngineContext` is instantiated.
2. Providers are discovered automatically inside the `engine` package.
3. Providers are sorted topologically based on their `depends_on` lists.
4. `register_services(context)` is called on each provider.
5. `boot(context)` is called on each provider.
6. `initialize_all(context)` is called on the `EngineServices` container, which triggers `initialize()` and `validate()` on every registered service.
