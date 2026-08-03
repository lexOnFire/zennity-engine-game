"""EngineProvider oficial da Plataforma de Diagnósticos da Zennity Engine."""
from engine.core.provider import EngineProvider
from engine.core.context import EngineContext
from engine.diagnostics.service import DiagnosticsService


class DiagnosticsProvider(EngineProvider):
    """Provedor de diagnósticos e estatísticas de performance."""

    def register_services(self, context: EngineContext) -> None:
        service = DiagnosticsService()
        context.services.register(DiagnosticsService, service)

    def boot(self, context: EngineContext) -> None:
        pass
