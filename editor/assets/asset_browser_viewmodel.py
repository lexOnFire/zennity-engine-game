from __future__ import annotations

from editor.assets.asset_browser_model import AssetBrowserItem, AssetBrowserModel


class AssetBrowserViewModel:
    def __init__(self, model: AssetBrowserModel | None = None) -> None:
        self.model = model or AssetBrowserModel()
        self.root: AssetBrowserItem = self.model.root

    def refresh(self) -> AssetBrowserItem:
        self.root = self.model.refresh()
        return self.root

    def list_assets(self):
        return self.model.database.list_assets()

    def assets_by_type(self, asset_type: str):
        return self.model.database.list_assets_by_type(asset_type)
