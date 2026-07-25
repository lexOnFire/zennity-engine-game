"""EngineProvider do Runtime de Produção da Zennity Engine."""
from engine.core.provider import EngineProvider
from engine.core.context import EngineContext
from engine.runtime.production_runtime import (
    SceneStreamingService,
    ResourceManagerCache,
    JobScheduler,
)


class RuntimeProvider(EngineProvider):
    """Provedor dos serviços centrais do Runtime de Produção."""

    def register_services(self, context: EngineContext) -> None:
        context.services.register(SceneStreamingService, SceneStreamingService())
        context.services.register(ResourceManagerCache, ResourceManagerCache())
        context.services.register(JobScheduler, JobScheduler())

    def boot(self, context: EngineContext) -> None:
        pass
