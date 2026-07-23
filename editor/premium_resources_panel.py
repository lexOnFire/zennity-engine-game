from __future__ import annotations

from PySide6.QtCore import Qt, QSize, Signal
from PySide6.QtGui import QColor, QFont, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMenu,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from editor.assets import AssetBrowserModel, AssetBrowserViewModel, ProjectBrowserService
from editor.assets_panel_controller import AssetsPanelController, image_icon
from editor.premium_editor import Panel


class ResourcesPanel(Panel):
    asset_selected = Signal(object)

    def __init__(self) -> None:
        super().__init__("Recursos")
        self.asset_model = AssetBrowserModel()
        self.asset_viewmodel = AssetBrowserViewModel(self.asset_model)
        self.browser = ProjectBrowserService(self.asset_model.database)
        self._items_by_path: dict[str, QTreeWidgetItem] = {}

        toolbar = QWidget()
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(0, 0, 0, 0)
        toolbar_layout.setSpacing(4)

        self.search = QLineEdit()
        self.search.setPlaceholderText("Buscar por nome, extensão ou tipo...")
        self.search.setObjectName("SearchBox")
        self.search.textChanged.connect(self.apply_filter)
        self.list_button = QPushButton("Lista")
        self.grid_button = QPushButton("Grade")
        self.list_button.clicked.connect(lambda: self.set_view_mode("list"))
        self.grid_button.clicked.connect(lambda: self.set_view_mode("grid"))
        toolbar_layout.addWidget(self.search, 1)
        toolbar_layout.addWidget(self.list_button)
        toolbar_layout.addWidget(self.grid_button)
        self.layout.addWidget(toolbar)

        self.favorites = QTreeWidget()
        self.favorites.setHeaderLabels(["Favoritos"])
        self.favorites.setMaximumHeight(92)
        self.favorites.itemSelectionChanged.connect(self._favorite_selected)
        self.layout.addWidget(self.favorites)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Nome", "Tipo"])
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.open_context_menu)
        self.layout.addWidget(self.tree)
        self.assets_controller = AssetsPanelController(self)
        self.assets_controller.install()
        self.set_view_mode(self.browser.session.view_mode)
        self.refresh_assets()
        self.tree.itemSelectionChanged.connect(self._selected)

    def refresh_assets(self) -> None:
        self.assets_controller.refresh(self._refresh_assets_content)

    def closeEvent(self, event) -> None:
        self.assets_controller.uninstall()
        super().closeEvent(event)

    def _refresh_assets_content(self) -> None:
        self.browser.refresh()
        self.tree.clear()
        self._items_by_path.clear()
        root = self.asset_viewmodel.refresh()
        root_item = QTreeWidgetItem(self.tree, [root.name, "folder"])
        root_item.setIcon(0, self._icon_for("thumbnail:folder"))
        self._populate_item(root_item, root)
        root_item.setExpanded(True)
        self.refresh_favorites()
        self.apply_filter(self.search.text())

    def _populate_item(self, parent_item: QTreeWidgetItem, browser_item) -> None:
        for child in browser_item.children:
            tree_item = QTreeWidgetItem(parent_item, [child.name, child.item_type])
            tree_item.setData(0, Qt.UserRole, child.asset)
            rel_path = child.asset.path if child.asset is not None else self._folder_path(parent_item, child.name)
            tree_item.setData(0, Qt.UserRole + 1, rel_path)
            tree_item.setIcon(0, self._icon_for_item(child))
            if rel_path:
                self._items_by_path[rel_path] = tree_item
            self._populate_item(tree_item, child)

    def _selected(self) -> None:
        item = self.tree.currentItem()
        if item is None:
            self.asset_selected.emit(None)
            return
        self.asset_selected.emit(item.data(0, Qt.UserRole))

    def _favorite_selected(self) -> None:
        item = self.favorites.currentItem()
        if item is None:
            return
        path = item.data(0, Qt.UserRole)
        target = self._items_by_path.get(path)
        if target is not None:
            self.tree.setCurrentItem(target)
            parent = target.parent()
            while parent is not None:
                parent.setExpanded(True)
                parent = parent.parent()

    def set_view_mode(self, mode: str) -> None:
        self.browser.session.set_view_mode(mode)
        if mode == "grid":
            self.tree.setIconSize(QSize(48, 48))
            self.tree.setColumnWidth(0, 150)
        else:
            self.tree.setIconSize(QSize(20, 20))
            self.tree.setColumnWidth(0, 220)
        self._sync_view_mode_buttons()

    def _sync_view_mode_buttons(self) -> None:
        mode = self.browser.session.view_mode
        self.list_button.setEnabled(mode != "list")
        self.grid_button.setEnabled(mode != "grid")

    def refresh_favorites(self) -> None:
        self.favorites.clear()
        for path in self.browser.session.list_favorites():
            item = QTreeWidgetItem(self.favorites, [path])
            item.setData(0, Qt.UserRole, path)
            item.setIcon(0, self._icon_for("thumbnail:folder"))

    def apply_filter(self, text: str) -> None:
        query = text.strip().lower()
        root = self.tree.topLevelItem(0)
        if root is None:
            return
        if not query:
            self._set_visible_recursive(root, True)
            root.setExpanded(True)
            return
        self._filter_item(root, query)
        root.setHidden(False)
        root.setExpanded(True)

    def _set_visible_recursive(self, item: QTreeWidgetItem, visible: bool) -> None:
        item.setHidden(not visible)
        for index in range(item.childCount()):
            self._set_visible_recursive(item.child(index), visible)

    def _filter_item(self, item: QTreeWidgetItem, query: str) -> bool:
        asset = item.data(0, Qt.UserRole)
        fields = [item.text(0), item.text(1)]
        if asset is not None:
            fields.extend([asset.extension, asset.type.value, asset.path])
        own_match = any(query in str(field).lower() for field in fields)
        child_match = False
        for index in range(item.childCount()):
            child_match = self._filter_item(item.child(index), query) or child_match
        visible = own_match or child_match
        item.setHidden(not visible)
        if child_match:
            item.setExpanded(True)
        return visible

    def open_context_menu(self, pos) -> None:
        item = self.tree.itemAt(pos)
        asset = item.data(0, Qt.UserRole) if item is not None else None
        path = item.data(0, Qt.UserRole + 1) if item is not None else "Assets"
        menu = QMenu(self)
        new_folder = menu.addAction("New Folder")
        rename = menu.addAction("Rename")
        duplicate = menu.addAction("Duplicate")
        delete = menu.addAction("Delete")
        reveal = menu.addAction("Reveal in Explorer/Finder")
        copy_path = menu.addAction("Copy Path")
        menu.addSeparator()
        favorite = menu.addAction("Add Favorite")
        rename.setEnabled(item is not None and item.parent() is not None)
        duplicate.setEnabled(asset is not None)
        delete.setEnabled(item is not None and item.parent() is not None)
        reveal.setEnabled(item is not None)
        copy_path.setEnabled(item is not None)
        action = menu.exec(self.tree.viewport().mapToGlobal(pos))
        if action is new_folder:
            self.create_folder(path if asset is None else str(asset.absolute_path.parent))
        elif action is rename and item is not None:
            self.rename_path(path, f"{item.text(0)}_renamed")
        elif action is duplicate and asset is not None:
            self.duplicate_path(asset.path)
        elif action is delete and item is not None:
            self.delete_path(path)
        elif action is reveal and item is not None:
            self.browser.reveal_path(path)
        elif action is copy_path and item is not None:
            QApplication.clipboard().setText(self.browser.copy_path(path))
        elif action is favorite and item is not None:
            self.add_favorite(path if asset is None else str(asset.absolute_path.parent))

    def create_folder(self, parent: str = "Assets", name: str = "New Folder") -> None:
        self.browser.create_folder(parent, name)
        self.refresh_assets()

    def rename_path(self, path: str, new_name: str) -> None:
        self.browser.rename_asset(path, new_name)
        self.refresh_assets()

    def duplicate_path(self, path: str) -> None:
        self.browser.duplicate_asset(path)
        self.refresh_assets()

    def delete_path(self, path: str) -> None:
        self.browser.delete_asset(path)
        self.refresh_assets()

    def move_path(self, path: str, folder: str) -> None:
        self.browser.move_asset(path, folder)
        self.refresh_assets()

    def add_favorite(self, path: str) -> None:
        rel = self.browser.copy_path(path)
        self.browser.session.add_favorite(rel)
        self.refresh_favorites()

    def _icon_for_item(self, item) -> QIcon:
        if item.asset is not None:
            thumbnail = image_icon(item.asset)
            if thumbnail is not None:
                return thumbnail
        if item.asset is None:
            return self._icon_for("thumbnail:folder")
        return self._icon_for(self.browser.thumbnail_for_asset(item.asset))

    def _icon_for(self, key: str) -> QIcon:
        colors = {
            "thumbnail:folder": "#d6a84f",
            "thumbnail:image": "#4ca3ff",
            "thumbnail:scene": "#79c267",
            "thumbnail:prefab": "#b57cff",
            "thumbnail:tilemap": "#5db7a5",
            "thumbnail:default": "#8a93a6",
        }
        pixmap = QPixmap(48, 48)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QColor(colors.get(key, colors["thumbnail:default"])))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(6, 8, 36, 32, 5, 5)
        painter.end()
        return QIcon(pixmap)

    def _folder_path(self, parent_item: QTreeWidgetItem, name: str) -> str:
        parts = [name]
        item = parent_item
        while item is not None and item.parent() is not None:
            parts.append(item.text(0))
            item = item.parent()
        return "/".join(["Assets", *reversed(parts)])
