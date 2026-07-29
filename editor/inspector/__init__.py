from __future__ import annotations

from editor.inspector.plugin import InspectorPlugin
from editor.inspector.plugin_registry import InspectorPluginRegistry

_registry: InspectorPluginRegistry | None = None


def _build_registry() -> InspectorPluginRegistry:
    from editor.inspector.asset_component_plugins import register_asset_component_plugins
    from editor.inspector.default_plugins import register_default_inspector_plugins
    from editor.inspector.plugin_registry import inspector_plugin_registry

    register_default_inspector_plugins()
    register_asset_component_plugins()
    return inspector_plugin_registry


def _get_registry() -> InspectorPluginRegistry:
    global _registry
    if _registry is None:
        _registry = _build_registry()
    return _registry


inspector_plugin_registry: InspectorPluginRegistry = _get_registry()  # type: ignore[assignment]

__all__ = [
    "InspectorPlugin",
    "InspectorPluginRegistry",
    "inspector_plugin_registry",
]
