from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import PurePosixPath

from engine.assets import AssetDatabase, AssetInfo


@dataclass
class AssetBrowserItem:
    name: str
    item_type: str
    asset: AssetInfo | None = None
    children: list["AssetBrowserItem"] = field(default_factory=list)

    @property
    def is_folder(self) -> bool:
        return self.asset is None


class AssetBrowserModel:
    def __init__(self, database: AssetDatabase | None = None) -> None:
        self.database = database or AssetDatabase()
        self.root = AssetBrowserItem("Assets", "folder")

    def refresh(self) -> AssetBrowserItem:
        assets = self.database.refresh()
        self.root = self._build_tree(assets)
        return self.root

    def _build_tree(self, assets: list[AssetInfo]) -> AssetBrowserItem:
        root = AssetBrowserItem("Assets", "folder")
        folders: dict[str, AssetBrowserItem] = {"Assets": root}

        for asset in assets:
            rel = PurePosixPath(asset.path)
            parts = rel.parts
            if not parts:
                continue
            parent_key = "Assets"
            parent = root
            folder_parts = parts[1:-1] if parts[0] == "Assets" else parts[:-1]
            current_parts = ["Assets"]

            for folder in folder_parts:
                current_parts.append(folder)
                key = "/".join(current_parts)
                child = folders.get(key)
                if child is None:
                    child = AssetBrowserItem(folder, "folder")
                    folders[key] = child
                    parent.children.append(child)
                parent = child
                parent_key = key

            parent.children.append(AssetBrowserItem(asset.name, asset.type.value, asset=asset))

        self._sort_tree(root)
        return root

    def _sort_tree(self, item: AssetBrowserItem) -> None:
        item.children.sort(key=lambda child: (not child.is_folder, child.name.lower()))
        for child in item.children:
            self._sort_tree(child)
