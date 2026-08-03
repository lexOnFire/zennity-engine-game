"""Cache-facing asset API.

The runtime manager owns cache lifetime and reference counts. Keeping that
responsibility in one service avoids a second, divergent global cache.
"""

from engine.assets.runtime_asset_manager import RuntimeAssetManager

AssetCache = RuntimeAssetManager

__all__ = ["AssetCache", "RuntimeAssetManager"]
