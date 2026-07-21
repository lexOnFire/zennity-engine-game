"""Asset tree discovery and preview presentation for the editor."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QTreeWidgetItem

from editor.asset_preview_service import AssetPreviewService
from editor.ui.tokens import DEFAULT_TOKENS


class AssetBrowserController:
    HIDDEN_DIRECTORY_NAMES = {"scripts", "behaviors"}
    HIDDEN_EXTENSIONS = {".meta", ".py", ".zbehavior"}

    def __init__(
        self,
        host: Any,
        project_root: Path,
        preview_service: AssetPreviewService | None = None,
    ) -> None:
        self.host = host
        self.project_root = Path(project_root)
        self.preview_service = preview_service or AssetPreviewService(DEFAULT_TOKENS.danger)
        self._connected = False

    def connect(self) -> bool:
        if self._connected:
            return False
        self.host.assets_tree.itemClicked.connect(self.preview)
        self.host.assets_tree.itemDoubleClicked.connect(self.open_item)
        self._connected = True
        return True

    def disconnect(self) -> bool:
        if not self._connected:
            return False
        self.host.assets_tree.itemClicked.disconnect(self.preview)
        self.host.assets_tree.itemDoubleClicked.disconnect(self.open_item)
        self._connected = False
        return True

    def refresh(self) -> None:
        tree = self.host.assets_tree
        tree.clear()
        root_path = self.asset_root()
        root_item = QTreeWidgetItem([
            "📁 " + (root_path.name if root_path.exists() else "Assets")
        ])
        tree.addTopLevelItem(root_item)
        if root_path.exists():
            self._add_directory(root_item, root_path)
        root_item.setExpanded(True)

    def asset_root(self) -> Path:
        preferred = self.project_root / "Assets"
        fallback = self.project_root / "assets"
        return preferred if preferred.exists() or not fallback.exists() else fallback

    def _add_directory(self, parent_item: QTreeWidgetItem, directory: Path) -> None:
        for child in sorted(directory.iterdir(), key=lambda path: (path.is_file(), path.name.lower())):
            if self._hidden(child):
                continue
            item = QTreeWidgetItem([self.asset_icon(child) + child.name])
            item.setToolTip(0, str(child))
            parent_item.addChild(item)
            if child.is_dir():
                self._add_directory(item, child)

    @classmethod
    def _hidden(cls, path: Path) -> bool:
        return (
            path.name.startswith(".")
            or path.suffix.lower() in cls.HIDDEN_EXTENSIONS
            or (path.is_dir() and path.name.casefold() in cls.HIDDEN_DIRECTORY_NAMES)
        )

    @staticmethod
    def asset_icon(path: Path) -> str:
        if path.is_dir():
            return "📁 "
        extension = path.suffix.lower()
        if extension in {".png", ".jpg", ".jpeg"}:
            return "🖼️ "
        if extension in {".ogg", ".wav", ".mp3"}:
            return "🔊 "
        return {".zanim": "🎞 ", ".zanimator": "◉ ", ".zlogic": "◇ "}.get(
            extension, "📄 ",
        )

    def preview(self, item: QTreeWidgetItem) -> None:
        path_value = item.toolTip(0)
        if not path_value:
            return
        preview = self.preview_service.preview(Path(path_value))
        self.set_preview_state("content")
        label = self.host.preview_label
        label.clear()
        if preview.pixmap is not None:
            label.setPixmap(preview.pixmap.scaled(
                label.width(), label.height(), Qt.KeepAspectRatio, Qt.SmoothTransformation,
            ))
        else:
            label.setText(preview.label)
        self.host.preview_details_label.setText(preview.details)

    def set_preview_state(self, state: str) -> None:
        label = self.host.preview_label
        label.setProperty("uiState", state)
        label.style().unpolish(label)
        label.style().polish(label)

    def dragged_path(self) -> Path | None:
        selected_items = self.host.assets_tree.selectedItems()
        if not selected_items:
            return None
        path_value = selected_items[0].toolTip(0)
        return Path(path_value) if path_value else None

    def open_item(self, item: QTreeWidgetItem, _column: int = 0) -> None:
        path_value = item.toolTip(0)
        path = Path(path_value) if path_value else None
        if path is not None and path.is_file() and path.suffix.lower() == ".zlogic":
            self.host._show_logic_window(preferred_path=path)
