from PySide6.QtWidgets import (
    QDockWidget, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
    QTreeWidget, QTreeWidgetItem, QLabel, QHeaderView
)
from typing import Optional
from PySide6.QtCore import Qt, Slot
from engine.game_object import GameObject
from editor.viewmodels.scene_viewmodel import SceneViewModel


class HierarchyDock(QDockWidget):
    """
    Painel acoplável da Hierarquia de Objetos da Cena (Outliner).
    Componente 'View' na arquitetura MVVM do editor.
    """
    
    def __init__(self, parent: QWidget = None) -> None:
        super().__init__("Hierarchy", parent)
        self.setObjectName("HierarchyDock")
        self.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        
        self.viewmodel: Optional[SceneViewModel] = None
        self._updating_selection = False
        
        # Conteúdo interno
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(4, 4, 4, 4)
        
        # Barra de pesquisa
        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("Filtrar objetos...")
        self.txt_search.textChanged.connect(self.filter_tree)
        layout.addWidget(self.txt_search)
        
        # Árvore de entidades (Outliner - Suporte a Multi-Seleção ExtendedSelection)
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setColumnCount(1)
        self.tree.setSelectionMode(QTreeWidget.ExtendedSelection)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.show_context_menu)
        self.tree.itemSelectionChanged.connect(self.on_item_selection_changed)
        self.tree.itemDoubleClicked.connect(self.on_item_double_clicked)
        self.tree.itemChanged.connect(self.on_item_changed)
        
        layout.addWidget(self.tree)
        self.setWidget(content)

    def set_viewmodel(self, viewmodel: SceneViewModel) -> None:
        """Conecta a View ao ViewModel da cena."""
        self.viewmodel = viewmodel
        self.viewmodel.hierarchy_updated.connect(self.populate_tree)
        self.viewmodel.selection_changed.connect(self.select_object_in_tree)
        self.populate_tree()

    @Slot()
    def populate_tree(self) -> None:
        """Popula a árvore recursivamente com base nos GameObjects do ViewModel."""
        if not self.viewmodel:
            return
            
        self.tree.blockSignals(True)
        self.tree.clear()
        
        root_objects = self.viewmodel.get_root_objects()
        for obj in root_objects:
            self.add_object_node(self.tree.invisibleRootItem(), obj)
            
        self.tree.blockSignals(False)
        self.select_object_in_tree(self.viewmodel.selected_object)
        self.filter_tree(self.txt_search.text())

    def add_object_node(self, parent_item: QTreeWidgetItem, obj: GameObject) -> None:
        """Adiciona recursivamente nós de GameObjects à árvore com ícones por tipo/tag."""
        item = QTreeWidgetItem(parent_item)
        
        # Define o ícone representativo baseado no nome/tag/componentes
        icon_prefix = "📦 "
        name_lower = obj.name.lower()
        if "folder" in name_lower or "group" in name_lower:
            icon_prefix = "📁 "
        elif "camera" in name_lower:
            icon_prefix = "📷 "
        elif "light" in name_lower:
            icon_prefix = "💡 "
        elif "sprite" in name_lower or "mesh" in name_lower:
            icon_prefix = "🖼️ "

        item.setText(0, f"{icon_prefix}{obj.name}")
        item.setData(0, Qt.UserRole, obj)
        
        # Permite edição do nome ao dar duplo clique
        item.setFlags(item.flags() | Qt.ItemIsEditable)
        
        # Adiciona filhos recursivamente
        for child in obj.children:
            self.add_object_node(item, child)

    def show_context_menu(self, pos) -> None:
        """Exibe o menu de contexto de clique com o botão direito na Hierarquia."""
        from PySide6.QtWidgets import QMenu
        item = self.tree.itemAt(pos)
        obj = item.data(0, Qt.UserRole) if item else None

        menu = QMenu(self)
        act_create = menu.addAction("➕ Criar Novo Objeto")
        act_rename = menu.addAction("✏️ Renomear Objeto") if item else None
        act_duplicate = menu.addAction("📄 Duplicar Objeto") if item else None
        act_delete = menu.addAction("🗑️ Excluir Objeto") if item else None

        chosen = menu.exec(self.tree.mapToGlobal(pos))
        if not chosen or not self.viewmodel:
            return

        if chosen == act_create:
            self.viewmodel.create_object("Quadrado")
        elif chosen == act_rename and item:
            self.tree.editItem(item, 0)
        elif chosen == act_duplicate:
            self.viewmodel.duplicate_selected()
        elif chosen == act_delete:
            self.viewmodel.delete_selected()

    @Slot()
    def on_item_selection_changed(self) -> None:
        """Chamado quando a seleção da árvore Qt é alterada pelo usuário."""
        if self._updating_selection or not self.viewmodel:
            return
            
        selected_items = self.tree.selectedItems()
        if selected_items:
            obj = selected_items[0].data(0, Qt.UserRole)
            self._updating_selection = True
            self.viewmodel.selected_object = obj
            self._updating_selection = False
        else:
            self._updating_selection = True
            self.viewmodel.selected_object = None
            self._updating_selection = False

    @Slot(object)
    def select_object_in_tree(self, selected_obj: Optional[GameObject]) -> None:
        """Sincroniza a seleção da árvore quando o ViewModel muda a seleção."""
        if self._updating_selection:
            return
            
        self.tree.blockSignals(True)
        self.tree.clearSelection()
        
        if selected_obj:
            item = self.find_item_by_object(self.tree.invisibleRootItem(), selected_obj)
            if item:
                item.setSelected(True)
                # Garante que os pais fiquem expandidos
                parent = item.parent()
                while parent:
                    parent.setExpanded(True)
                    parent = parent.parent()
                self.tree.scrollToItem(item)
                
        self.tree.blockSignals(False)

    def find_item_by_object(self, parent_item: QTreeWidgetItem, obj: GameObject) -> Optional[QTreeWidgetItem]:
        """Busca recursivamente o item correspondente ao GameObject."""
        for i in range(parent_item.childCount()):
            child = parent_item.child(i)
            if child.data(0, Qt.UserRole) == obj:
                return child
            res = self.find_item_by_object(child, obj)
            if res:
                return res
        return None

    @Slot(str)
    def filter_tree(self, text: str) -> None:
        """Filtra os elementos da hierarquia com base no texto inserido."""
        text = text.lower()
        self.tree.blockSignals(True)
        
        for i in range(self.tree.invisibleRootItem().childCount()):
            self._filter_item_recursive(self.tree.invisibleRootItem().child(i), text)
            
        self.tree.blockSignals(False)

    def _filter_item_recursive(self, item: QTreeWidgetItem, text: str) -> bool:
        """Oculta/exibe itens baseado no filtro de busca (recursivo)."""
        match = text in item.text(0).lower()
        any_child_match = False
        
        for i in range(item.childCount()):
            child_match = self._filter_item_recursive(item.child(i), text)
            any_child_match = any_child_match or child_match
            
        should_show = match or any_child_match
        item.setHidden(not should_show)
        if any_child_match:
            item.setExpanded(True)
            
        return should_show

    @Slot(QTreeWidgetItem, int)
    def on_item_double_clicked(self, item: QTreeWidgetItem, column: int) -> None:
        """Abre a edição do nome do nó."""
        self.tree.editItem(item, column)

    @Slot(QTreeWidgetItem, int)
    def on_item_changed(self, item: QTreeWidgetItem, column: int) -> None:
        """Submete o novo nome para o ViewModel após a edição."""
        obj = item.data(0, Qt.UserRole)
        if obj and self.viewmodel:
            raw_name = item.text(column)
            clean_name = raw_name
            for prefix in ("📦 ", "📁 ", "📷 ", "💡 ", "🖼️ "):
                if clean_name.startswith(prefix):
                    clean_name = clean_name[len(prefix):]
            clean_name = clean_name.strip()
            if clean_name and clean_name != obj.name:
                self.viewmodel.rename_object(obj, clean_name)
