from editor.inspector.plugin import InspectorPlugin
from editor.inspector.plugin_registry import InspectorPluginRegistry, inspector_plugin_registry
from editor.inspector.default_plugins import register_default_inspector_plugins
from editor.inspector.asset_component_plugins import register_asset_component_plugins
from editor.runtime.asset_direct_drop_patch import patch_asset_direct_drop_runtime

patch_asset_direct_drop_runtime()

__all__ = [
    "InspectorPlugin",
    "InspectorPluginRegistry",
    "inspector_plugin_registry",
    "register_default_inspector_plugins",
    "register_asset_component_plugins",
]
