import os
from PySide6.QtWidgets import (
    QDockWidget, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QTreeView, QListView, QLineEdit, QPushButton, QLabel
)
from PySide6.QtCore import Qt, QSize, Slot, QModelIndex, QDir, QMimeData, QUrl
from PySide6.QtGui import QIcon, QPainter, QColor, QPixmap, QDrag
from editor.models.asset_model import AssetModel
from editor.viewmodels.asset_viewmodel import AssetViewModel

_ASSET_MIME = "application/x-zennity-asset"


class _DraggableListView(QListView):
    """QListView com suporte a drag de assets."""

    def __init__(self, asset_model_ref, parent=None):
        super().__init__(parent)
        self._asset_model_ref = asset_model_ref
        self.setDragEnabled(True)
        self.setDragDropMode(QListView.DragOnly)
        self.setDefaultDropAction(Qt.CopyAction)

    def startDrag(self, supported_actions):
        index = self.currentIndex()
        if not index.isValid():
            return
        model = self._asset_model_ref()
        if model is None:
            return
        path = model.filePath(index)
        if not os.path.isfile(path):
            return

        mime = QMimeData()
        mime.setData(_ASSET_MIME, path.encode("utf-8"))
        mime.setUrls([QUrl.fromLocalFile(path)])

        drag = QDrag(self)
        drag.setMimeData(mime)

        # Thumbnail no cursor
        ext = os.path.splitext(path)[1].lower()
        if ext in (".png", ".jpg", ".jpeg", ".bmp", ".gif"):
            px = QPixmap(path).scaled(48, 48, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            drag.setPixmap(px)
        else:
            # Ícone genérico de arquivo
            icon_px = QPixmap(32, 32)
            icon_px.fill(QColor("#1e2130"))
            drag.setPixmap(icon_px)

        drag.exec(Qt.CopyAction)


class AssetBrowserDock(QDockWidget):
    """
    Painel acoplável do navegador de recursos (Asset Browser).
    Componente 'View' na arquitetura MVVM do editor.
    Suporta drag de assets para a cena e Inspector.
    """

    def __init__(self, parent: QWidget = None) -> None:
        super().__init__("Recursos", parent)
        self.setObjectName("AssetBrowserDock")
        self.setAllowedAreas(Qt.BottomDockWidgetArea | Qt.LeftDockWidgetArea)

        self.model = None
        self.viewmodel = None

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(4, 4, 4, 4)

        # Barra de navegação
        navbar = QWidget()
        nav_layout = QHBoxLayout(navbar)
        nav_layout.setContentsMargins(0, 0, 0, 4)
        nav_layout.setSpacing(4)

        self.btn_back = QPushButton("←")
        self.btn_back.setToolTip("Voltar")
        self.btn_back.setFixedWidth(30)
        self.btn_back.clicked.connect(self.on_back_clicked)

        self.btn_forward = QPushButton("→")
        self.btn_forward.setToolTip("Avançar")
        self.btn_forward.setFixedWidth(30)
        self.btn_forward.clicked.connect(self.on_forward_clicked)

        self.btn_up = QPushButton("↑")
        self.btn_up.setToolTip("Subir Diretório")
        self.btn_up.setFixedWidth(30)
        self.btn_up.clicked.connect(self.on_up_clicked)

        self.lbl_path = QLabel("Assets/")
        self.lbl_path.setStyleSheet("color: #828a9b; font-weight: bold; padding-left: 6px;")

        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("Buscar no diretório...")
        self.txt_search.setFixedWidth(180)
        self.txt_search.textChanged.connect(self.on_search_changed)

        nav_layout.addWidget(self.btn_back)
        nav_layout.addWidget(self.btn_forward)
        nav_layout.addWidget(self.btn_up)
        nav_layout.addWidget(self.lbl_path)
        nav_layout.addStretch()
        nav_layout.addWidget(self.txt_search)

        layout.addWidget(navbar)

        splitter = QSplitter(Qt.Horizontal)

        self.tree_folders = QTreeView()
        self.tree_folders.setHeaderHidden(True)
        self.tree_folders.setColumnHidden(1, True)
        self.tree_folders.setColumnHidden(2, True)
        self.tree_folders.setColumnHidden(3, True)
        self.tree_folders.clicked.connect(self.on_folder_tree_clicked)
        splitter.addWidget(self.tree_folders)

        # Lista de arquivos com drag habilitado
        self.list_files = _DraggableListView(lambda: self.model)
        self.list_files.setViewMode(QListView.IconMode)
        self.list_files.setResizeMode(QListView.Adjust)
        self.list_files.setGridSize(QSize(95, 95))
        self.list_files.setIconSize(QSize(48, 48))
        self.list_files.setWordWrap(True)
        self.list_files.clicked.connect(self.on_file_list_clicked)
        self.list_files.doubleClicked.connect(self.on_file_list_double_clicked)
        splitter.addWidget(self.list_files)

        splitter.setSizes([200, 600])
        layout.addWidget(splitter)

        self.setWidget(content)

    def set_models(self, model: AssetModel, viewmodel: AssetViewModel) -> None:
        self.model = model
        self.viewmodel = viewmodel

        self.tree_folders.setModel(self.model)
        self.list_files.setModel(self.model)

        self.tree_folders.setRootIndex(self.model.index(self.model.get_assets_root_path()))
        self.model.setFilter(QDir.AllDirs | QDir.NoDotAndDotDot)

        self.list_files.setRootIndex(self.model.index(self.viewmodel.current_path))

        self.viewmodel.current_folder_changed.connect(self.on_current_folder_changed)
        self.viewmodel.navigation_state_changed.connect(self.update_nav_buttons)

        self.update_nav_buttons(self.viewmodel.can_go_back(), self.viewmodel.can_go_forward())
        self.update_path_label()

    @Slot(QModelIndex)
    def on_folder_tree_clicked(self, index: QModelIndex) -> None:
        path = self.model.filePath(index)
        if self.viewmodel:
            self.viewmodel.go_to_folder(path)

    @Slot(QModelIndex)
    def on_file_list_clicked(self, index: QModelIndex) -> None:
        path = self.model.filePath(index)
        if self.viewmodel:
            self.viewmodel.select_asset(path)

    @Slot(QModelIndex)
    def on_file_list_double_clicked(self, index: QModelIndex) -> None:
        path = self.model.filePath(index)
        if os.path.isdir(path) and self.viewmodel:
            self.viewmodel.go_to_folder(path)

    @Slot(str)
    def on_current_folder_changed(self, path: str) -> None:
        idx = self.model.index(path)
        self.list_files.setRootIndex(idx)

        self.tree_folders.blockSignals(True)
        self.tree_folders.setCurrentIndex(idx)
        self.tree_folders.scrollTo(idx)
        self.tree_folders.blockSignals(False)

        self.update_path_label()

    def update_path_label(self) -> None:
        if not self.viewmodel:
            return
        rel = os.path.relpath(self.viewmodel.current_path, self.viewmodel.root_path)
        if rel == ".":
            self.lbl_path.setText("Assets/")
        else:
            self.lbl_path.setText(f"Assets/{rel.replace(os.sep, '/')}/")

    @Slot(bool, bool)
    def update_nav_buttons(self, can_back: bool, can_forward: bool) -> None:
        self.btn_back.setEnabled(can_back)
        self.btn_forward.setEnabled(can_forward)

    @Slot()
    def on_back_clicked(self) -> None:
        if self.viewmodel:
            self.viewmodel.go_back()

    @Slot()
    def on_forward_clicked(self) -> None:
        if self.viewmodel:
            self.viewmodel.go_forward()

    @Slot()
    def on_up_clicked(self) -> None:
        if self.viewmodel:
            parent = self.viewmodel.get_parent_directory()
            self.viewmodel.go_to_folder(parent)

    @Slot(str)
    def on_search_changed(self, text: str) -> None:
        if not self.model:
            return
        if text.strip():
            self.model.setNameFilters([f"*{text}*"])
        else:
            self.model.setNameFilters(["*.py", "*.png", "*.jpg", "*.json", "*.wav", "*.ogg", "*.obj"])
