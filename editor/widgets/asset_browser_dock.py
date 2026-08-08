import os
from pathlib import Path
from typing import Optional
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

    def __init__(self, parent: QWidget = None, workflow_controller: Optional[object] = None) -> None:
        super().__init__("Recursos", parent)
        self.setObjectName("AssetBrowserDock")
        self.setAllowedAreas(Qt.BottomDockWidgetArea | Qt.LeftDockWidgetArea)

        self.model: Optional[AssetModel] = None
        self.viewmodel: Optional[AssetViewModel] = None
        self.workflow_controller = workflow_controller
        
        # Conteúdo interno
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(4, 4, 4, 4)
        
        # 1. Barra superior de comandos
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

        # FASE UX ASSET BROWSER: Filtros por Categoria & Favoritos
        from PySide6.QtWidgets import QComboBox
        self.combo_category_filter = QComboBox()
        self.combo_category_filter.addItems(["Todos os Tipos", "Cenas", "Texturas", "Sons", "Scripts", "Materiais", "Favoritos ⭐"])
        self.combo_category_filter.setFixedWidth(120)
        self.combo_category_filter.currentTextChanged.connect(self._on_category_filter_changed)
        nav_layout.addWidget(self.combo_category_filter)

        nav_layout.addWidget(self.txt_search)
        
        layout.addWidget(navbar)

        # Registro de Favoritos
        self.favorites: set[str] = set()
        
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
        self.list_files.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list_files.customContextMenuRequested.connect(self.on_context_menu_requested)
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
        """Chamado ao dar duplo clique em um item da grade."""
        path = self.model.filePath(index)

        # Se for pasta, navega
        if os.path.isdir(path) and self.viewmodel:
            self.viewmodel.go_to_folder(path)
            return

        # Se for arquivo, abre conforme tipo
        self._open_asset_by_path(path)

    def _open_asset_by_path(self, path: str) -> None:
        """Abre um asset conforme sua extensão."""
        filepath = Path(path)
        if not filepath.exists():
            return

        suffix = filepath.suffix.lower()

        # Scene (.zscene)
        if suffix == ".zscene":
            self._open_scene(filepath)
            return

        # Logic Graph (.zlogic)
        if suffix == ".zlogic":
            self._open_logic_graph(filepath)
            return

        # UI (.zui)
        if suffix == ".zui":
            self._open_ui_asset(filepath)
            return

        # Animation Controller (.zcontroller)
        if suffix == ".zcontroller":
            self._open_animation_controller(filepath)
            return

        # Image (.png, .jpg, etc) - pode abrir em visualizador
        if suffix in {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp"}:
            self._open_image(filepath)
            return

    def _open_scene(self, filepath: Path) -> None:
        """Abre uma cena (.zscene) no editor."""
        try:
            # Se workflow_controller foi passado ao construtor, usa ele
            if self.workflow_controller:
                self.workflow_controller.load_scene(filepath)
                return

            # Fallback: procura pela janela principal
            main_window = self._find_main_window()
            if hasattr(main_window, 'workflow_controller'):
                main_window.workflow_controller.load_scene(filepath)
            elif hasattr(main_window, '_scene_persistence'):
                # Editor isolado pode ter _scene_persistence diretamente
                payload, snapshots, typed = main_window._scene_persistence.load(filepath)
                main_window._scene_snapshot = snapshots
                main_window._objects_by_name = {item["name"]: item for item in snapshots}
                main_window._scene_document = payload if typed else None
                main_window._current_scene_path = filepath
                main_window._selected_name = None
                main_window._refresh_hierarchy()
        except Exception as e:
            import logging
            logging.error(f"Falha ao abrir cena {filepath}: {e}")

    def _open_logic_graph(self, filepath: Path) -> None:
        """Abre um grafo de lógica (.zlogic) no editor."""
        try:
            main_window = self._find_main_window()
            if hasattr(main_window, 'open_logic_graph'):
                main_window.open_logic_graph(filepath)
            else:
                import logging
                logging.warning(f"Logic graph editor não disponível para {filepath}")
        except Exception as e:
            import logging
            logging.error(f"Falha ao abrir logic graph {filepath}: {e}")

    def _open_ui_asset(self, filepath: Path) -> None:
        """Abre um asset UI (.zui) no editor."""
        try:
            main_window = self._find_main_window()
            if hasattr(main_window, 'open_ui_asset'):
                main_window.open_ui_asset(filepath)
            else:
                import logging
                logging.warning(f"UI editor não disponível para {filepath}")
        except Exception as e:
            import logging
            logging.error(f"Falha ao abrir UI {filepath}: {e}")

    def _open_animation_controller(self, filepath: Path) -> None:
        """Abre um controlador de animação (.zcontroller) no editor."""
        try:
            main_window = self._find_main_window()
            if hasattr(main_window, 'open_animation_controller'):
                main_window.open_animation_controller(filepath)
            else:
                import logging
                logging.warning(f"Animation controller editor não disponível para {filepath}")
        except Exception as e:
            import logging
            logging.error(f"Falha ao abrir animation controller {filepath}: {e}")

    def _open_image(self, filepath: Path) -> None:
        """Visualiza uma imagem."""
        try:
            import logging
            logging.info(f"Abrindo imagem: {filepath}")
        except Exception as e:
            import logging
            logging.error(f"Falha ao abrir imagem {filepath}: {e}")

    def _find_main_window(self):
        """Procura pela janela principal (QMainWindow)."""
        widget = self
        while widget:
            if widget.__class__.__name__ == "QMainWindow":
                return widget
            widget = getattr(widget, 'parent', lambda: None)()
        return None

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
        """Aplica o filtro de pesquisa no model."""
        if self.model:
            if text:
                self.model.setNameFilters([f"*{text}*"])
                self.model.setNameFilterDisables(False)
            else:
                self.model.setNameFilters([])
                self.model.setNameFilterDisables(True)

    # ──────────────────────────────────────────────────────────────────────────
    # FASE UX ASSET BROWSER: Favoritos & Filtros por Categoria API
    # ──────────────────────────────────────────────────────────────────────────

    @Slot(object)
    def on_context_menu_requested(self, pos) -> None:
        index = self.list_files.indexAt(pos)
        if not index.isValid():
            return
        
        from PySide6.QtWidgets import QMenu
        menu = QMenu(self)
        
        rename_action = menu.addAction("Renomear Seguro")
        is_fav = self.model.filePath(index) in self.favorites
        fav_action = menu.addAction("Remover dos Favoritos" if is_fav else "Adicionar aos Favoritos")
        reimport_action = menu.addAction("Reimportar")
        
        action = menu.exec(self.list_files.viewport().mapToGlobal(pos))
        
        if action == rename_action:
            self.list_files.edit(index)
        elif action == fav_action:
            self.toggle_favorite(self.model.filePath(index))
            self.model.layoutChanged.emit()
        elif action == reimport_action:
            import logging
            logging.info(f"Reimportando: {self.model.filePath(index)}")

    def toggle_favorite(self, file_path: str) -> bool:
        """Adiciona ou remove um arquivo dos favoritos."""
        if file_path in self.favorites:
            self.favorites.remove(file_path)
            is_fav = False
        else:
            self.favorites.add(file_path)
            is_fav = True
        return is_fav

    def _on_category_filter_changed(self, category: str) -> None:
        """Filtra os arquivos exibidos com base na categoria selecionada."""
        if not self.model:
            return
        ext_map = {
            "Cenas": ["*.zscene"],
            "Texturas": ["*.png", "*.jpg", "*.tga"],
            "Sons": ["*.wav", "*.mp3", "*.ogg"],
            "Scripts": ["*.py", "*.zvs"],
            "Materiais": ["*.zmat"],
        }
        filters = ext_map.get(category, [])
        if filters:
            self.model.setNameFilters(filters)
            self.model.setNameFilterDisables(False)
        else:
            self.model.setNameFilters([])
            self.model.setNameFilterDisables(True)
