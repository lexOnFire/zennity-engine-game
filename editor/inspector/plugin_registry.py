from __future__ import annotations

import logging
from typing import Any

from editor.inspector.plugin import InspectorPlugin


class InspectorPluginRegistry:
    """Registro central para plugins de Inspector."""

    def __init__(self) -> None:
        self._plugins: list[InspectorPlugin] = []

    def register(self, plugin: InspectorPlugin | type[InspectorPlugin]) -> InspectorPlugin:
        instance = plugin() if isinstance(plugin, type) else plugin

        # Prevenir IDs duplicados exatos (mesma classe de mesmo plugin)
        for existing in self._plugins:
            if type(existing) is type(instance) and existing.component_type == instance.component_type:
                logging.warning(f"InspectorPlugin for {instance.component_type} already registered by {type(existing).__name__}. Ignoring.")
                return existing

        # Se houver outro plugin pro mesmo componente mas de tipo diferente, a política
        # atual (v1.1) é sobrescrever. Para V1.2, avisamos e sobrescrevemos (o último ganha).
        filtered = []
        for existing in self._plugins:
            if existing.component_type == instance.component_type:
                logging.info(f"Overriding inspector for {instance.component_type} with {type(instance).__name__}")
            else:
                filtered.append(existing)

        self._plugins = filtered
        self._plugins.append(instance)
        return instance

    def unregister(self, plugin: InspectorPlugin | type[InspectorPlugin]) -> None:
        target_type = plugin if isinstance(plugin, type) else type(plugin)
        self._plugins = [p for p in self._plugins if type(p) is not target_type]

    def plugin_for(self, component: Any) -> InspectorPlugin | None:
        for plugin in reversed(self._plugins):
            if plugin.supports(component):
                return plugin
        return None

    def registered_plugins(self) -> tuple[InspectorPlugin, ...]:
        return tuple(self._plugins)


inspector_plugin_registry = InspectorPluginRegistry()
