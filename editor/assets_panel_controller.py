from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from PySide6.QtCore import QFileSystemWatcher, QTimer, Qt
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import QAbstractItemView, QTreeWidgetItem


_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp"}
_ICON_CACHE: dict[tuple[str, int, int], QIcon] = {}


def item_path(item: QTreeWidgetItem | None) -> str:
    if item is None:
        return ""
    asset = item.data(0, Qt.UserRole)
    if asset is not None:
        return str(getattr(asset, "path", "") or "")
    return str(item.data(0, Qt.UserRole + 1) or "")


def walk_items(root: QTreeWidgetItem | None):
    if root is None:
        return
    yield root
    for index in range(root.childCount()):
        yield from walk_items(root.child(index))


def image_icon(asset: Any) -> QIcon | None:
    path = Path(str(getattr(asset, "absolute_path", "") or ""))
    if not path.is_file() or path.suffix.lower() not in _IMAGE_EXTENSIONS:
        return None
    stat = path.stat()
    key = (str(path.resolve()), int(stat.st_mtime_ns), int(stat.st_size))
    cached = _ICON_CACHE.get(key)
    if cached is not None:
        return cached
    pixmap = QPixmap(str(path))
    if pixmap.isNull():
        return None
    icon = QIcon(pixmap.scaled(48, 48, Qt.KeepAspectRatio, Qt.SmoothTransformation))
    _ICON_CACHE[key] = icon
    while len(_ICON_CACHE) > 256:
        _ICON_CACHE.pop(next(iter(_ICON_CACHE)))
    return icon


class AssetsPanelController:
    """Explicit lifecycle for asset refresh, rename and filesystem watching."""

    def __init__(self, panel: Any) -> None:
        self.panel = panel
        self.tree = panel.tree
        self.renaming = False
        self.refresh_after_rename = False
        self.rename_item: QTreeWidgetItem | None = None
        self.rename_old_path = ""
        self.rename_old_text = ""
        self.installed = False
        self.refresh_timer = QTimer(panel)
        self.refresh_timer.setSingleShot(True)
        self.refresh_timer.setInterval(220)
        self.refresh_timer.timeout.connect(self._refresh_if_idle)
        self.watcher = QFileSystemWatcher(panel)
        self.watcher.directoryChanged.connect(self.request_refresh)
        self.watcher.fileChanged.connect(self.request_refresh)

    def install(self) -> None:
        if self.installed:
            return
        self.installed = True
        self.tree.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tree.setDragEnabled(True)
        self.tree.setDragDropMode(QAbstractItemView.DragOnly)
        self.tree.setDefaultDropAction(Qt.CopyAction)
        self.tree.itemDoubleClicked.connect(self.begin_rename)
        self.tree.itemChanged.connect(self.finish_rename)

    def uninstall(self) -> None:
        if not self.installed:
            return
        self.installed = False
        self.refresh_timer.stop()
        try:
            self.tree.itemDoubleClicked.disconnect(self.begin_rename)
            self.tree.itemChanged.disconnect(self.finish_rename)
        except (RuntimeError, TypeError):
            pass
        paths = self.watcher.directories() + self.watcher.files()
        if paths:
            self.watcher.removePaths(paths)

    def refresh(self, refresh_content: Callable[[], None]) -> None:
        if self.renaming:
            self.refresh_after_rename = True
            return
        selected_path = item_path(self.tree.currentItem())
        expanded = {
            item_path(item)
            for item in walk_items(self.tree.topLevelItem(0))
            if item_path(item) and item.isExpanded()
        }
        self.tree.blockSignals(True)
        try:
            refresh_content()
            for item in walk_items(self.tree.topLevelItem(0)):
                flags = item.flags() | Qt.ItemIsDragEnabled
                if item.parent() is not None:
                    flags |= Qt.ItemIsEditable
                item.setFlags(flags)
                path = item_path(item)
                if item.parent() is None or path in expanded:
                    item.setExpanded(True)
                if selected_path and path == selected_path:
                    self.tree.setCurrentItem(item)
        finally:
            self.tree.blockSignals(False)
        self.sync_watcher_paths()

    def request_refresh(self, *_args: Any) -> None:
        if self.renaming:
            self.refresh_after_rename = True
        else:
            self.refresh_timer.start()

    def _refresh_if_idle(self) -> None:
        if not self.renaming:
            self.panel.refresh_assets()

    def sync_watcher_paths(self) -> None:
        if self.renaming:
            return
        root = Path(self.panel.browser.assets_root)
        desired = {str(root)}
        if root.exists():
            desired.update(str(path) for path in root.rglob("*") if path.is_dir())
        current = set(self.watcher.directories()) | set(self.watcher.files())
        remove = list(current - desired)
        add = list(desired - current)
        if remove:
            self.watcher.removePaths(remove)
        if add:
            self.watcher.addPaths(add)

    def begin_rename(self, item: QTreeWidgetItem | None, column: int = 0) -> None:
        if item is None or item.parent() is None:
            return
        self.refresh_timer.stop()
        self.renaming = True
        self.refresh_after_rename = False
        self.rename_item = item
        self.rename_old_path = item_path(item)
        self.rename_old_text = item.text(0)
        self.tree.editItem(item, column)

    def finish_rename(self, item: QTreeWidgetItem, column: int) -> None:
        if column != 0 or not self.renaming or item is not self.rename_item:
            return
        old_path = self.rename_old_path or item_path(item)
        old_text = self.rename_old_text or Path(old_path).name
        new_name = item.text(0).strip()
        self.renaming = False
        try:
            if not old_path or not new_name or new_name == old_text:
                item.setText(0, old_text)
                return
            self.panel.rename_path(old_path, new_name)
        except Exception:
            item.setText(0, old_text)
            self.panel.refresh_assets()
        finally:
            self.rename_item = None
            if self.refresh_after_rename:
                self.refresh_after_rename = False
                QTimer.singleShot(80, self.panel.refresh_assets)
