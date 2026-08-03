"""Metadata-only context for graph authoring inside the Qt editor.

This intentionally avoids ``EngineBootstrap``: its recursive discovery imports
the complete runtime, including SDL/Pygame modules that must stay in the
isolated viewport process.
"""
from __future__ import annotations

from engine.core.context import EngineContext
from engine.graph.validation_service import GraphValidationService
from engine.metadata.manager import MetadataManager


def ensure_editor_metadata_context() -> EngineContext:
    context = EngineContext.current()
    if context is not None and context.services.get_optional(MetadataManager):
        return context

    context = EngineContext({"editor_metadata_only": True})
    metadata = MetadataManager()
    validation = GraphValidationService()
    context.services.register(MetadataManager, metadata)
    context.services.register(GraphValidationService, validation)
    EngineContext._current = context

    # These providers only register graph definitions; none owns a display,
    # audio device, render loop or runtime service.
    from engine.ai.provider import AIProvider
    from engine.dialogue.provider import DialogueProvider
    from engine.graphics.material_provider import MaterialProvider

    for provider_type in (AIProvider, DialogueProvider, MaterialProvider):
        provider_type().boot(context)
    context.services.initialize_all(context=context)
    return context


__all__ = ["ensure_editor_metadata_context"]
