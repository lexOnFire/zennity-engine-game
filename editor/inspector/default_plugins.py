from __future__ import annotations

from editor.inspector.plugins.transform_inspector_plugin import TransformInspectorPlugin
from editor.inspector.plugins.rigid_body_inspector_plugin import RigidBodyInspectorPlugin
from editor.inspector.plugins.collider_inspector_plugin import ColliderInspectorPlugin
from editor.inspector.plugins.camera_inspector_plugin import CameraInspectorPlugin
from editor.inspector.plugins.audio_source_inspector_plugin import AudioSourceInspectorPlugin
from editor.inspector.plugins.audio_listener_inspector_plugin import AudioListenerInspectorPlugin
from editor.inspector.plugins.animator_inspector_plugin import AnimatorInspectorPlugin
from editor.inspector.plugins.canvas_inspector_plugin import CanvasInspectorPlugin
from editor.inspector.plugins.label_inspector_plugin import LabelInspectorPlugin
from editor.inspector.plugins.image_inspector_plugin import ImageInspectorPlugin
from editor.inspector.plugins.button_inspector_plugin import ButtonInspectorPlugin
from editor.inspector.plugins.tilemap_inspector_plugin import TilemapInspectorPlugin
from editor.inspector.plugins.tilemap_renderer_inspector_plugin import TilemapRendererInspectorPlugin
from editor.inspector.plugins.asset_inspector_plugin import AssetInspectorPlugin
from editor.inspector.plugins.package_inspector_plugin import PackageInspectorPlugin
from editor.inspector.ui_binder_plugin import UIBinderPlugin
from editor.inspector.animation_controller_plugin import AnimationControllerPlugin

__all__ = [
    "TransformInspectorPlugin",
    "RigidBodyInspectorPlugin",
    "ColliderInspectorPlugin",
    "CameraInspectorPlugin",
    "AudioSourceInspectorPlugin",
    "AudioListenerInspectorPlugin",
    "AnimatorInspectorPlugin",
    "CanvasInspectorPlugin",
    "LabelInspectorPlugin",
    "ImageInspectorPlugin",
    "ButtonInspectorPlugin",
    "TilemapInspectorPlugin",
    "TilemapRendererInspectorPlugin",
    "AssetInspectorPlugin",
    "PackageInspectorPlugin",
    "UIBinderPlugin",
    "AnimationControllerPlugin",
]

from editor.inspector.plugin_registry import inspector_plugin_registry
from editor.inspector.plugin_ui_utils import _section, _property_row, _float_field, _axis_row

def register_default_inspector_plugins() -> None:
    inspector_plugin_registry.register(TransformInspectorPlugin)
    inspector_plugin_registry.register(RigidBodyInspectorPlugin)
    inspector_plugin_registry.register(ColliderInspectorPlugin)
    inspector_plugin_registry.register(CameraInspectorPlugin)
    inspector_plugin_registry.register(AudioSourceInspectorPlugin)
    inspector_plugin_registry.register(AudioListenerInspectorPlugin)
    inspector_plugin_registry.register(AnimatorInspectorPlugin)
    inspector_plugin_registry.register(CanvasInspectorPlugin)
    inspector_plugin_registry.register(LabelInspectorPlugin)
    inspector_plugin_registry.register(ImageInspectorPlugin)
    inspector_plugin_registry.register(ButtonInspectorPlugin)
    inspector_plugin_registry.register(TilemapInspectorPlugin)
    inspector_plugin_registry.register(TilemapRendererInspectorPlugin)
    inspector_plugin_registry.register(AssetInspectorPlugin)
    inspector_plugin_registry.register(PackageInspectorPlugin)
    inspector_plugin_registry.register(UIBinderPlugin)
    inspector_plugin_registry.register(AnimationControllerPlugin)

__all__.extend(["register_default_inspector_plugins", "_section", "_property_row", "_float_field", "_axis_row"])
