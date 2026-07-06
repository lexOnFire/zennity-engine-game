from __future__ import annotations

import sys
from PySide6.QtCore import Qt, QSize, Signal
from PySide6.QtGui import QAction, QColor, QFont, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QPushButton,
    QSplitter,
    QStatusBar,
    QTabWidget,
    QTextBrowser,
    QToolBar,
    QToolButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from editor.assets import AssetBrowserModel, AssetBrowserViewModel, ProjectBrowserService
from editor.models.scene_model import SceneModel
from editor.runtime.editor_context import EditorContext
from editor.viewmodels.scene_viewmodel import SceneViewModel
from editor.widgets.viewport_widget import ViewportWidget


class Panel(QFrame):
    def __init__(self, title: str) -> None:
        super().__init__()
        self.setObjectName("PremiumPanel")
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        header = QWidget()
        header.setObjectName("PanelHeader")
        row = QHBoxLayout(header)
        row.setContentsMargins(8, 4, 8, 4)
        label = QLabel(title)
        label.setObjectName("PanelHeaderTitle")
        row.addWidget(label)
        row.addStretch(1)
        row.addWidget(QLabel("gear x"))
        self.layout.addWidget(header)


class HierarchyPanel(Panel):
    selected = Signal(str)

    def __init__(self) -> None:
        super().__init__("Hierarchy")
        search = QLineEdit()
        search.setPlaceholderText("Filtrar...")
        search.setObjectName("SearchBox")
        self.layout.addWidget(search)
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.layout.addWidget(self.tree)
        self.populate()
        self.tree.itemSelectionChanged.connect(self._selected)

    def populate(self) -> None:
        self.tree.clear()
        root = QTreeWidgetItem(self.tree, ["MainScene"])
        for name in ["Environment", "DirectionalLight", "Camera", "Player", "Enemies"]:
            item = QTreeWidgetItem(root, [name])
            item.setData(0, Qt.UserRole, name)
        root.setExpanded(True)

    def add_object(self, name: str) -> None:
        root = self.tree.topLevelItem(0)
        item = QTreeWidgetItem(root, [name])
        item.setData(0, Qt.UserRole, name)
        root.setExpanded(True)
        self.tree.setCurrentItem(item)

    def _selected(self) -> None:
        item = self.tree.currentItem()
        if item:
            self.selected.emit(item.data(0, Qt.UserRole) or item.text(0))


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
        self.set_view_mode(self.browser.session.view_mode)
        self.refresh_assets()
        self.tree.itemSelectionChanged.connect(self._selected)

    def refresh_assets(self) -> None:
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


class CreatePanel(Panel):
    create_requested = Signal(str)

    def __init__(self) -> None:
        super().__init__("Criar")
        body = QWidget()
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(8, 8, 8, 8)
        groups = [
            ("2D", ["Player", "Plataforma", "Inimigo", "Sprite 2D", "Camera 2D"]),
            ("Templates", ["Plataforma 2D", "Top-down 2D"]),
        ]
        for title, items in groups:
            label = QLabel(title)
            label.setObjectName("SectionLabel")
            body_layout.addWidget(label)
            for item in items:
                button = QPushButton(item)
                button.setObjectName("CreatePresetButton")
                button.clicked.connect(lambda checked=False, value=item: self.create_requested.emit(value))
                body_layout.addWidget(button)
        body_layout.addStretch(1)
        self.layout.addWidget(body)


class PrefabsPanel(Panel):
    asset_selected = Signal(object)

    def __init__(self) -> None:
        super().__init__("Prefabs")
        self.asset_model = AssetBrowserModel()
        self.asset_viewmodel = AssetBrowserViewModel(self.asset_model)
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Nome", "Path"])
        self.layout.addWidget(self.tree)
        self.refresh_prefabs()
        self.tree.itemSelectionChanged.connect(self._selected)

    def refresh_prefabs(self) -> None:
        self.tree.clear()
        self.asset_viewmodel.refresh()
        for asset in self.asset_viewmodel.assets_by_type("prefab"):
            item = QTreeWidgetItem(self.tree, [asset.name, asset.path])
            item.setData(0, Qt.UserRole, asset)

    def _selected(self) -> None:
        item = self.tree.currentItem()
        if item is None:
            self.asset_selected.emit(None)
            return
        self.asset_selected.emit(item.data(0, Qt.UserRole))


class InspectorPanel(Panel):
    def __init__(self) -> None:
        super().__init__("Inspector")
        self.name = QLabel("Nenhum objeto selecionado")
        self.name.setObjectName("InspectorTitle")
        self.layout.addWidget(self.name)
        for section in ["Transform", "Renderer", "Collider", "Scripts"]:
            label = QLabel(section + "\n  X: 0    Y: 0    Z: 0")
            label.setObjectName("InspectorSection")
            self.layout.addWidget(label)
        self.layout.addStretch(1)

    def load_object(self, name: str) -> None:
        self.name.setText(name)


class ConsolePanel(Panel):
    def __init__(self) -> None:
        super().__init__("Console")
        self.log = QTextBrowser()
        self.log.setObjectName("ConsoleLog")
        self.layout.addWidget(self.log)
        self.add("INFO", "Zennity Premium Editor iniciado.")

    def add(self, level: str, message: str) -> None:
        color = {"INFO": "#8bc34a", "WARN": "#ffc107", "ERROR": "#f44336"}.get(level, "#aaaaaa")
        self.log.append(f'<span style="color:{color}">[{level}]</span> {message}')


class SimplePanel(Panel):
    def __init__(self, title: str, text: str) -> None:
        super().__init__(title)
        label = QLabel(text)
        label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(label)


class AssetPreviewPanel(Panel):
    def __init__(self) -> None:
        super().__init__("Asset Preview")
        body = QWidget()
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(8, 8, 8, 8)
        body_layout.setSpacing(12)

        self.image = QLabel()
        self.image.setAlignment(Qt.AlignCenter)
        self.image.setMinimumSize(220, 140)
        self.image.setObjectName("AssetPreviewImage")

        self.details = QLabel("Nenhum asset selecionado")
        self.details.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.details.setWordWrap(True)
        self.details.setObjectName("AssetPreviewDetails")

        body_layout.addWidget(self.image)
        body_layout.addWidget(self.details, 1)
        self.layout.addWidget(body)
        self.layout.addStretch(1)

    def load_asset(self, asset) -> None:
        if asset is None:
            self.image.clear()
            self.details.setText("Nenhum asset selecionado")
            return

        if getattr(asset, "type", None) and asset.type.value == "image":
            pixmap = QPixmap(str(asset.absolute_path))
            if not pixmap.isNull():
                self.image.setPixmap(
                    pixmap.scaled(220, 140, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                )
            else:
                self.image.setText("Imagem indisponivel")
        else:
            self.image.clear()

        self.details.setText(
            "\n".join(
                [
                    f"Nome: {asset.name}",
                    f"Tipo: {asset.type.value}",
                    f"Path: {asset.path}",
                    f"UUID: {asset.uuid}",
                    f"Tamanho: {asset.size} bytes",
                ]
            )
        )


class ZennityPremiumEditor(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("ZennityPremiumEditor")
        self.setWindowTitle("Zennity Engine Editor - Premium")
        self.resize(1440, 900)
        self._apply_safe_font()
        self.object_count = 0
        if not hasattr(self, "editor_context"):
            self.editor_context = EditorContext()
        self.scene_model = SceneModel()
        self.scene_view_model = SceneViewModel(
            self.scene_model,
            selection_manager=self.editor_context.selection,
        )
        self._build_menu()
        self._build_toolbar()
        self._build_layout()
        self._build_status()
        self._connect()

    def _apply_safe_font(self) -> None:
        font = QApplication.font() if QApplication.instance() is not None else self.font()
        if font.pointSize() <= 0 and font.pointSizeF() <= 0:
            font = QFont(font)
            font.setPointSize(10)
            QApplication.setFont(font)
            self.setFont(font)

    def _build_menu(self) -> None:
        bar = self.menuBar()
        for name in ["Arquivo", "Editar", "Janela", "Criar", "Ferramentas", "Build + Executar", "Ajuda"]:
            menu = bar.addMenu(name)
            if name == "Criar":
                for item in ["Player", "Plataforma", "Inimigo", "Sprite 2D", "Camera 2D"]:
                    menu.addAction(item, lambda checked=False, value=item: self.create_object(value))
            elif name == "Build + Executar":
                menu.addAction("Play", self.play)
                menu.addAction("Stop", self.stop)

    def _build_toolbar(self) -> None:
        tb = QToolBar("MainToolBar")
        tb.setObjectName("CommandBar")
        tb.setMovable(False)
        tb.setIconSize(QSize(16, 16))
        self.addToolBar(tb)
        for text in ["Open", "Save", "Undo", "Redo"]:
            tb.addWidget(QToolButton(text=text))
        spacer = QWidget()
        spacer.setMinimumWidth(300)
        tb.addWidget(spacer)
        self.btn_play = QToolButton()
        self.btn_play.setText("Play")
        self.btn_play.clicked.connect(self.play)
        tb.addWidget(self.btn_play)
        btn_stop = QToolButton()
        btn_stop.setText("Stop")
        btn_stop.clicked.connect(self.stop)
        tb.addWidget(btn_stop)
        tb.addWidget(QComboBox())

    def _build_layout(self) -> None:
        self.hierarchy = HierarchyPanel()
        self.resources = ResourcesPanel()
        self.create_panel = CreatePanel()
        self.inspector = InspectorPanel()
        self.console = ConsolePanel()
        self.preview = SimplePanel("Asset Preview", "Preview de assets")
        self.profiler = SimplePanel("Profiler", "FPS, CPU, memoria")

        self.viewport = ViewportWidget(self)
        self.viewport.setObjectName("ViewportCanvas")
        self.viewport.set_viewmodel(self.scene_view_model)

        left = QSplitter(Qt.Vertical)
        left.addWidget(self.hierarchy)
        left.addWidget(self.resources)
        left.addWidget(self.create_panel)
        left.setSizes([320, 260, 220])

        center = QSplitter(Qt.Vertical)
        center.addWidget(self.viewport)
        bottom = QSplitter(Qt.Horizontal)
        bottom.addWidget(self.console)
        bottom.addWidget(self.preview)
        bottom.addWidget(self.profiler)
        bottom.setSizes([520, 260, 260])
        center.addWidget(bottom)
        center.setSizes([560, 240])

        main = QSplitter(Qt.Horizontal)
        main.addWidget(left)
        main.addWidget(center)
        main.addWidget(self.inspector)
        main.setSizes([260, 850, 300])
        self.setCentralWidget(main)

    def _build_status(self) -> None:
        status = QStatusBar()
        self.setStatusBar(status)
        self.status_msg = QLabel("Projeto salvo.")
        self.stats = QLabel("FPS: 60 | Memoria: 512 MB | Objetos: 0")
        status.addWidget(self.status_msg)
        status.addPermanentWidget(self.stats)

    def _connect(self) -> None:
        self.hierarchy.selected.connect(self.inspector.load_object)
        self.create_panel.create_requested.connect(self.create_object)

    def create_object(self, name: str) -> None:
        mapping = {"Sprite 2D": "Quadrado"}
        value = mapping.get(name, name)
        if hasattr(self.viewport, "create_object"):
            self.viewport.create_object(value)
        self.object_count += 1
        display_name = f"{name}_{self.object_count}"
        self.hierarchy.add_object(display_name)
        self.inspector.load_object(display_name)
        self.stats.setText(f"FPS: 60 | Memoria: 512 MB | Objetos: {self.object_count}")
        self.console.add("INFO", f"Objeto criado: {name}")

    def play(self) -> None:
        self.viewport._on_play_state_changed("play")
        self.status_msg.setText("Simulacao ativa.")
        self.console.add("INFO", "Play iniciado.")

    def stop(self) -> None:
        self.viewport._on_play_state_changed("stop")
        self.status_msg.setText("Simulacao parada.")
        self.console.add("INFO", "Play finalizado.")


def run() -> None:
    app = QApplication(sys.argv)
    from editor.premium_theme import PREMIUM_QSS
    app.setStyleSheet(PREMIUM_QSS)
    win = ZennityPremiumEditor()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    run()
