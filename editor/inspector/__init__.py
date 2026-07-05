from editor.inspector.plugin import InspectorPlugin
from editor.inspector.plugin_registry import InspectorPluginRegistry, inspector_plugin_registry
from editor.inspector.default_plugins import register_default_inspector_plugins

__all__ = [
    "InspectorPlugin",
    "InspectorPluginRegistry",
    "inspector_plugin_registry",
    "register_default_inspector_plugins",
]
