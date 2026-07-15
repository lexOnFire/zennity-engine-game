import os
from PySide6.QtWidgets import (
    QDockWidget, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QTreeView, QListView, QLineEdit, QPushButton, QLabel
)
from PySide6.QtCore import Qt, QSize, Slot, QModelIndex, QDir
from PySide6.QtGui import QIcon, QPainter, QColor, QPixmap
from editor.models.asset_model import AssetModel
from editor.viewmodels.asset_viewmodel import AssetViewModel


class AssetBrowserDock(QDockWidget):
    """
    Painel acoplável do navegador de recursos (Asset Browser).
    Componente 'View' na arquitetura MVVM do editor.
    """
    
    def __init__(self, parent: QWidget = None) -> None:
        super().__init__("Recursos", parent)
        self.setObjectName("AssetBrowserDock")
        self.setAllowedAreas(Qt.BottomDockWidgetArea | Qt.LeftDockWidgetArea)
        
        self.model: Optional[AssetModel] = None
        self.viewmodel: Optional[AssetViewModel] = None
        
        # Conteúdo interno
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(4, 4, 4, 4)
        
        # 1. Barra de Ferramentas Superior
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
        
        # 2. Splitter para dividir a árvore de pastas e a grade de arquivos
        splitter = QSplitter(Qt.Horizontal)
        
        # Árvore de Pastas (Esquerda)
        self.tree_folders = QTreeView()
        self.tree_folders.setHeaderHidden(True)
        self.tree_folders.setColumnHidden(1, True)
        self.tree_folders.setColumnHidden(2, True)
        self.tree_folders.setColumnHidden(3, True)
        self.tree_folders.clicked.connect(self.on_folder_tree_clicked)
        splitter.addWidget(self.tree_folders)
        
        # Grade de Arquivos (Direita)
        self.list_files = QListView()
        self.list_files.setViewMode(QListView.IconMode)
        self.list_files.setResizeMode(QListView.Adjust)
        self.list_files.setGridSize(QSize(95, 95))
        self.list_files.setIconSize(QSize(48, 48))
        self.list_files.setWordWrap(True)
        self.list_files.clicked.connect(self.on_file_list_clicked)
        self.list_files.doubleClicked.connect(self.on_file_list_double_clicked)
        splitter.addWidget(self.list_files)
        
        # Proporção inicial do Splitter (25% esquerda, 75% direita)
        splitter.setSizes([200, 600])
        layout.addWidget(splitter)
        
        self.setWidget(content)

    def set_models(self, model: AssetModel, viewmodel: AssetViewModel) -> None:
        """Conecta a View ao Model e ViewModel correspondentes."""
        self.model = model
        self.viewmodel = viewmodel
        
        # Configura as fontes de dados do Qt
        self.tree_folders.setModel(self.model)
        self.list_files.setModel(self.model)
        
        # Restringe a árvore esquerda a exibir apenas diretórios
        self.tree_folders.setRootIndex(self.model.index(self.model.get_assets_root_path()))
        self.model.setFilter(QDir.AllDirs | QDir.NoDotAndDotDot)
        
        # ListView direita exibirá arquivos e diretórios da pasta ativa
        self.list_files.setRootIndex(self.model.index(self.viewmodel.current_path))
        
        # Registra callbacks no ViewModel
        self.viewmodel.current_folder_changed.connect(self.on_current_folder_changed)
        self.viewmodel.navigation_state_changed.connect(self.update_nav_buttons)
        
        self.update_nav_buttons(self.viewmodel.can_go_back(), self.viewmodel.can_go_forward())
        self.update_path_label()

    @Slot(QModelIndex)
    def on_folder_tree_clicked(self, index: QModelIndex) -> None:
        """Chamado quando uma pasta é clicada na árvore da esquerda."""
        path = self.model.filePath(index)
        if self.viewmodel:
            self.viewmodel.go_to_folder(path)

    @Slot(QModelIndex)
    def on_file_list_clicked(self, index: QModelIndex) -> None:
        """Chamado quando um item da grade é selecionado."""
        path = self.model.filePath(index)
        if self.viewmodel:
            self.viewmodel.select_asset(path)

    @Slot(QModelIndex)
    def on_file_list_double_clicked(self, index: QModelIndex) -> None:
        """Chamado ao dar duplo clique em um item da grade (navega se for pasta)."""
        path = self.model.filePath(index)
        if os.path.isdir(path) and self.viewmodel:
            self.viewmodel.go_to_folder(path)

    @Slot(str)
    def on_current_folder_changed(self, path: str) -> None:
        """Sincroniza a exibição da grade ao alterar o diretório ativo."""
        idx = self.model.index(path)
        self.list_files.setRootIndex(idx)
        
        # Sincroniza a seleção na árvore esquerda
        self.tree_folders.blockSignals(True)
        self.tree_folders.setCurrentIndex(idx)
        self.tree_folders.scrollTo(idx)
        self.tree_folders.blockSignals(False)
        
        self.update_path_label()

    def update_path_label(self) -> None:
        """Atualiza a exibição amigável do caminho ativo."""
        if not self.viewmodel:
            return
        rel = os.path.relpath(self.viewmodel.current_path, self.viewmodel.root_path)
        if rel == ".":
            self.lbl_path.setText("Assets/")
        else:
            self.lbl_path.setText(f"Assets/{rel.replace(os.sep, '/')}/")

    @Slot(bool, bool)
    def update_nav_buttons(self, can_back: bool, can_forward: bool) -> None:
        """Habilita ou desabilita botões de navegação."""
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
        """Aplica filtros de nome para busca de arquivos."""
        if not self.model:
            return
        if text.strip():
            # Busca de forma geral no diretório
            self.model.setNameFilters([f"*{text}*"])
        else:
            # Reseta para as extensões padrão
            self.model.setNameFilters(["*.py", "*.png", "*.jpg", "*.json", "*.wav", "*.ogg", "*.obj", "*.zprefab", "*.zscene", "*.zmat", "*.zanim", "*.zanimator", "*.zbehavior", "*.zlogic"])
