from engine.core.provider import EngineProvider
from engine.core.context import EngineContext


class LogicProvider(EngineProvider):
    """Provides Logic Runtime services and syncs metadata.

    PHASE 9.5B Stage 2 -- ``boot()`` no longer carries its own import list nor
    re-declares ~100 node definitions by hand.  It composes the three canonical
    steps, so booting with a provider and importing the runtime without one
    converge on the same registration result.
    """

    def register_services(self, context: EngineContext) -> None:
        pass

    def boot(self, context: EngineContext) -> None:
        from engine.logic.node_definitions.catalogue import ensure_catalogue_loaded
        from engine.logic.node_definitions.registry import get_registry
        from engine.logic.node_system import (
            load_runtime_node_modules,
            validate_node_system,
        )
        from engine.logic.runtime.registry import sync_logic_registry_to_metadata

        ensure_catalogue_loaded()
        load_runtime_node_modules()

        violations = validate_node_system()
        if violations:
            import logging

            logger = logging.getLogger(__name__)
            for violation in violations:
                logger.warning("Node system contract violation: %s", violation)

        self._publish_definitions(context)
        sync_logic_registry_to_metadata(context)

    @staticmethod
    def _publish_definitions(context: EngineContext) -> None:
        """Mirror the declarative definitions into the MetadataManager.

        Driven by the registry, not by a hand-maintained import block: whatever
        the catalogue harvested is what gets published, so the provider cannot
        add a registration the non-provider path lacks.
        """
        from engine.metadata.manager import MetadataManager
        from engine.logic.node_definitions.registry import get_registry

        manager = context.services.get_optional(MetadataManager)
        if not manager:
            return
        for definition in get_registry().all_canonical().values():
            try:
                manager.register(definition)
            except Exception:  # pragma: no cover - one bad node must not abort boot
                import logging

                logging.getLogger(__name__).exception(
                    "Failed to register node definition %s", getattr(definition, "id", "?")
                )
