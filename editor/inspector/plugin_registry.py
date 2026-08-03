from __future__ import annotations

from typing import Any

from editor.inspector.plugin import InspectorPlugin


class InspectorPluginRegistry:
    """Registro central para plugins de Inspector."""

    def __init__(self) -> None:
        self._plugins: list[InspectorPlugin] = []

    def register(self, plugin: InspectorPlugin | type[InspectorPlugin]) -> InspectorPlugin:
        # ── Validação estrutural (Plugin Validation) ───────────────────────
        # Garantimos que o plugin registrado honra o contrato de InspectorPlugin,
        # prevenindo falhas silenciosas na UI ao carregar um componente.
        cls = plugin if isinstance(plugin, type) else type(plugin)
        if not issubclass(cls, InspectorPlugin):
            raise TypeError(
                f"[InspectorPluginRegistry] '{cls.__name__}' não é uma subclasse de "
                f"InspectorPlugin. Verifique a herança do plugin."
            )
        if not callable(getattr(cls, "create_widget", None)):
            raise TypeError(
                f"[InspectorPluginRegistry] '{cls.__name__}' não implementa o método "
                f"'create_widget'. O plugin não pode ser registrado."
            )
        if not getattr(cls, "component_type", None):
            import logging
            logging.warning(
                f"[InspectorPluginRegistry] '{cls.__name__}' não define 'component_type'. "
                f"O plugin pode não aparecer no Inspector corretamente."
            )
        # ── Instanciação e substituição de duplicatas ─────────────────────
        instance = plugin() if isinstance(plugin, type) else plugin
        
        self._plugins = [
            existing
            for existing in self._plugins
            if existing.component_type != instance.component_type
        ]
        self._plugins.append(instance)
        
        from engine.core.context import EngineContext
        from engine.metadata.manager import MetadataManager
        from engine.core.metadata.editor import InspectorDefinition
        
        context = EngineContext.current()
        if context:
            manager = context.services.get_optional(MetadataManager)
            if manager:
                manager.register(InspectorDefinition(
                    id=f"inspector_{instance.component_type}",
                    target_type=instance.component_type,
                    custom_widget=instance
                ))
        return instance

    def plugin_for(self, component: Any) -> InspectorPlugin | None:
        comp_type = getattr(component, "component_type", getattr(component, "type_name", type(component).__name__))
        
        from engine.core.context import EngineContext
        from engine.metadata.manager import MetadataManager
        from engine.core.metadata.editor import InspectorDefinition
        
        context = EngineContext.current()
        if context:
            manager = context.services.get_optional(MetadataManager)
            if manager:
                defs = manager.get_all(InspectorDefinition)
                # Reverse to respect the old behavior where newer plugins override older ones
                for d in reversed(defs):
                    if d.target_type == comp_type and d.custom_widget:
                        return d.custom_widget
                        
        for plugin in reversed(self._plugins):
            if plugin.supports(component):
                return plugin
        return None

    def registered_plugins(self) -> tuple[InspectorPlugin, ...]:
        from engine.core.context import EngineContext
        from engine.metadata.manager import MetadataManager
        from engine.core.metadata.editor import InspectorDefinition
        
        context = EngineContext.current()
        if context:
            manager = context.services.get_optional(MetadataManager)
            if manager:
                defs = manager.get_all(InspectorDefinition)
                return tuple(d.custom_widget for d in defs if d.custom_widget)
                
        return tuple(self._plugins)


inspector_plugin_registry = InspectorPluginRegistry()
