from __future__ import annotations

from typing import Any

from editor.inspector.plugin import InspectorPlugin


class InspectorPluginRegistry:
    """Registro central para plugins de Inspector."""

    def __init__(self) -> None:
        self._plugins: list[InspectorPlugin] = []

    def register(self, plugin: InspectorPlugin | type[InspectorPlugin]) -> InspectorPlugin:
        instance = plugin() if isinstance(plugin, type) else plugin
        self._plugins = [
            existing
            for existing in self._plugins
            if existing.component_type != instance.component_type
        ]
        self._plugins.append(instance)
        return instance

    def plugin_for(self, component: Any) -> InspectorPlugin | None:
        for plugin in reversed(self._plugins):
            if plugin.supports(component):
                return plugin
        return None

    def registered_plugins(self) -> tuple[InspectorPlugin, ...]:
        return tuple(self._plugins)


inspector_plugin_registry = InspectorPluginRegistry()
