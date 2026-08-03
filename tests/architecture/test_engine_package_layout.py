from __future__ import annotations

from importlib import import_module


def test_engine_public_package_layout_is_importable() -> None:
    modules = (
        "engine.core.application",
        "engine.core.engine",
        "engine.core.scene",
        "engine.core.game_object",
        "engine.core.component",
        "engine.core.transform",
        "engine.core.system",
        "engine.core.time",
        "engine.core.window",
        "engine.assets.manager",
        "engine.assets.texture",
        "engine.assets.font",
        "engine.assets.animation",
        "engine.assets.cache",
        "engine.graphics",
        "engine.physics",
        "engine.animation",
        "engine.audio",
        "engine.input",
        "engine.events",
        "engine.serialization",
        "engine.utils",
        "engine.editor_support",
    )

    for module_name in modules:
        assert import_module(module_name) is not None


def test_asset_aliases_share_one_runtime_implementation() -> None:
    from engine.assets.cache import AssetCache
    from engine.assets.manager import AssetManager, RuntimeAssetManager

    assert AssetManager is RuntimeAssetManager
    assert AssetCache is RuntimeAssetManager
