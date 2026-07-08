from __future__ import annotations

from pathlib import Path
from typing import Any

from PySide6.QtCore import QFileSystemWatcher, QEvent, QObject, QTimer, Qt
from PySide6.QtGui import QIcon, QKeySequence, QPixmap
from PySide6.QtWidgets import QApplication, QAbstractItemView, QTreeWidgetItem


_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp"}
_ICON_CACHE: dict[tuple[str, float, int, int], QIcon] = {}


def _item_path(item: QTreeWidgetItem | None) -> str:
    if item is None:
        return ""
    asset = item.data(0, Qt.UserRole)
    if asset is not None:
        return str(getattr(asset, "path", "") or "")
    return str(item.data(0, Qt.UserRole + 1) or "")


def _walk_items(root: QTreeWidgetItem | None):
    if root is None:
        return
    yield root
    for index in range(root.childCount()):
        yield from _walk_items(root.child(index))


def _expanded_paths(tree) -> set[str]:
    root = tree.topLevelItem(0)
    return {path for item in _walk_items(root) if (path := _item_path(item)) and item.isExpanded()}


def _restore_expanded_paths(tree, paths: set[str]) -> None:
    root = tree.topLevelItem(0)
    for item in _walk_items(root):
        path = _item_path(item)
        if path in paths or item.parent() is None:
            item.setExpanded(True)


def _find_item_by_path(tree, path: str) -> QTreeWidgetItem | None:
    root = tree.topLevelItem(0)
    for item in _walk_items(root):
        if _item_path(item) == path:
            return item
    return None


def _mark_item_flags(root: QTreeWidgetItem | None) -> None:
    for item in _walk_items(root):
        flags = item.flags() | Qt.ItemIsDragEnabled
        if item.parent() is not None:
            flags |= Qt.ItemIsEditable
        item.setFlags(flags)


def _image_icon_for(asset: Any) -> QIcon | None:
    path = Path(str(getattr(asset, "absolute_path", "") or ""))
    if not path.exists() or path.suffix.lower() not in _IMAGE_EXTENSIONS:
        return None
    try:
        stat = path.stat()
        key = (str(path.resolve()), float(stat.st_mtime), int(stat.st_size), 48)
    except Exception:
        key = (str(path), 0.0, 0, 48)
    cached = _ICON_CACHE.get(key)
    if cached is not None:
        return cached
    pixmap = QPixmap(str(path))
    if pixmap.isNull():
        return None
    icon = QIcon(pixmap.scaled(48, 48, Qt.KeepAspectRatio, Qt.SmoothTransformation))
    _ICON_CACHE[key] = icon
    # Keep thumbnail cache bounded.
    while len(_ICON_CACHE) > 256:
        _ICON_CACHE.pop(next(iter(_ICON_CACHE)))
    return icon


class _AssetsPanelFilter(QObject):
    def __init__(self, panel: Any) -> None:
        super().__init__(panel)
        self.panel = panel

    def eventFilter(self, obj, event) -> bool:
        if event.type() == QEvent.KeyPress:
            tree = getattr(self.panel, "tree", None)
            if tree is not None and event.matches(QKeySequence.Refresh):
                self.panel.refresh_assets()
                event.accept()
                return True
            if tree is not None and event.key() == Qt.Key_F2:
                item = tree.currentItem()
                if item is not None and item.parent() is not None:
                    self.panel._zennity_begin_asset_rename(item, 0)
                    event.accept()
                    return True
        return False


def _install_assets_watcher(panel: Any) -> None:
    if getattr(panel, "_zennity_assets_watcher_installed", False):
        return
    panel._zennity_assets_watcher_installed = True
    panel._zennity_refresh_timer = QTimer(panel)
    panel._zennity_refresh_timer.setSingleShot(True)
    panel._zennity_refresh_timer.setInterval(180)
    panel._zennity_refresh_timer.timeout.connect(panel.refresh_assets)
    panel._zennity_assets_watcher = QFileSystemWatcher(panel)
    panel._zennity_assets_watcher.directoryChanged.connect(lambda *_: panel._zennity_refresh_timer.start())
    panel._zennity_assets_watcher.fileChanged.connect(lambda *_: panel._zennity_refresh_timer.start())


def _sync_watcher_paths(panel: Any) -> None:
    watcher = getattr(panel, "_zennity_assets_watcher", None)
    browser = getattr(panel, "browser", None)
    if watcher is None or browser is None:
        return
    try:
        current = set(watcher.directories()) | set(watcher.files())
        root = Path(browser.assets_root)
        desired_dirs = {str(root)}
        for path in root.rglob("*"):
            if path.is_dir():
                desired_dirs.add(str(path))
        for path in current - desired_dirs:
            if path in watcher.directories():
                watcher.removePath(path)
            elif path in watcher.files():
                watcher.removePath(path)
        for path in desired_dirs - current:
            watcher.addPath(path)
    except Exception:
        pass


def apply_assets_panel_polish(panel: Any) -> bool:
    tree = getattr(panel, "tree", None)
    browser = getattr(panel, "browser", None)
    if tree is None or browser is None:
        return False
    if getattr(panel, "_zennity_assets_panel_polish_applied", False):
        _sync_watcher_paths(panel)
        return True
    panel._zennity_assets_panel_polish_applied = True
    panel._zennity_asset_renaming = False
    tree.setEditTriggers(QAbstractItemView.DoubleClicked | QAbstractItemView.EditKeyPressed)
    tree.setDragEnabled(True)
    tree.setDragDropMode(QAbstractItemView.DragOnly)
    tree.setDefaultDropAction(Qt.CopyAction)

    _install_assets_watcher(panel)

    original_refresh = panel.refresh_assets
    original_icon_for_item = panel._icon_for_item

    def icon_for_item(item):
        asset = getattr(item, "asset", None)
        if asset is not None:
            icon = _image_icon_for(asset)
            if icon is not None:
                return icon
        return original_icon_for_item(item)

    def refresh_assets() -> None:
        selected_path = _item_path(tree.currentItem())
        expanded = _expanded_paths(tree)
        tree.blockSignals(True)
        try:
            original_refresh()
            _mark_item_flags(tree.topLevelItem(0))
            _restore_expanded_paths(tree, expanded)
            if selected_path:
                item = _find_item_by_path(tree, selected_path)
                if item is not None:
                    tree.setCurrentItem(item)
        finally:
            tree.blockSignals(False)
        _sync_watcher_paths(panel)
        try:
            panel.apply_filter(panel.search.text())
        except Exception:
            pass

    def begin_asset_rename(item: QTreeWidgetItem | None, column: int = 0) -> None:
        if item is None or item.parent() is None:
            return
        panel._zennity_asset_renaming = True
        panel._zennity_rename_old_path = _item_path(item)
        tree.editItem(item, column)

    def finish_asset_rename(item: QTreeWidgetItem, column: int) -> None:
        if column != 0 or item is None or item.parent() is None:
            return
        old_path = str(getattr(panel, "_zennity_rename_old_path", "") or _item_path(item))
        new_name = item.text(0).strip()
        if not old_path or not new_name:
            return
        old_name = Path(old_path).name
        if new_name == old_name or new_name == Path(old_name).stem:
            return
        try:
            panel.rename_path(old_path, new_name)
        except Exception:
            refresh_assets()
        finally:
            panel._zennity_asset_renaming = False

    panel._icon_for_item = icon_for_item
    panel.refresh_assets = refresh_assets
    panel._zennity_begin_asset_rename = begin_asset_rename
    panel._zennity_finish_asset_rename = finish_asset_rename

    try:
        tree.itemDoubleClicked.disconnect()
    except Exception:
        pass
    tree.itemDoubleClicked.connect(begin_asset_rename)
    tree.itemChanged.connect(finish_asset_rename)

    panel._zennity_assets_filter = _AssetsPanelFilter(panel)
    tree.installEventFilter(panel._zennity_assets_filter)
    tree.viewport().installEventFilter(panel._zennity_assets_filter)

    refresh_assets()
    return True


def _scan_and_apply_assets_panel_polish() -> bool:
    app = QApplication.instance()
    if app is None:
        return False
    applied = False
    for widget in app.topLevelWidgets():
        resources = getattr(widget, "resources", None)
        if resources is not None:
            applied = apply_assets_panel_polish(resources) or applied
    return applied


def install_assets_panel_polish_runtime_watch() -> bool:
    app = QApplication.instance()
    if app is not None:
        for delay in (0, 250, 800, 1600, 3000):
            QTimer.singleShot(delay, _scan_and_apply_assets_panel_polish)
    try:
        from editor.phase1_editor import ZennityPhase1Editor
    except Exception:
        return app is not None
    if getattr(ZennityPhase1Editor, "_zennity_assets_panel_polish_class_patched", False):
        return True
    original_connect = ZennityPhase1Editor._connect

    def connect(self) -> None:
        original_connect(self)
        resources = getattr(self, "resources", None)
        if resources is not None:
            apply_assets_panel_polish(resources)

    ZennityPhase1Editor._connect = connect
    ZennityPhase1Editor._zennity_assets_panel_polish_class_patched = True
    return True
