"""Canonical asset-manager API."""

from engine.assets import Assets
from engine.assets.runtime_asset_manager import RuntimeAssetManager

AssetManager = RuntimeAssetManager

__all__ = ["AssetManager", "Assets", "RuntimeAssetManager"]
