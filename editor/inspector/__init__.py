from editor.inspector.plugin import InspectorPlugin
from editor.inspector.plugin_registry import InspectorPluginRegistry, inspector_plugin_registry
from editor.inspector.default_plugins import register_default_inspector_plugins
from editor.inspector.asset_component_plugins import register_asset_component_plugins
from editor.inspector.infinite_background_plugin import register_infinite_background_plugin
from editor.runtime.asset_direct_drop_patch import patch_asset_direct_drop_runtime
from editor.runtime.assets_panel_polish_patch import install_assets_panel_polish_runtime_watch
from editor.runtime.rotated_scale_gizmo_patch import apply_rotated_scale_gizmo_patch

patch_asset_direct_drop_runtime()
install_assets_panel_polish_runtime_watch()
apply_rotated_scale_gizmo_patch()
register_infinite_background_plugin()

__all__ = [
    "InspectorPlugin",
    "InspectorPluginRegistry",
    "inspector_plugin_registry",
    "register_default_inspector_plugins",
    "register_asset_component_plugins",
]
