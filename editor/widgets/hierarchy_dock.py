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
        
        # Árvore de entidades (Outliner)
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setColumnCount(1)
        self.tree.setSelectionMode(QTreeWidget.SingleSelection)
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
        """Adiciona recursivamente nós de GameObjects à árvore."""
        item = QTreeWidgetItem(parent_item)
        item.setText(0, obj.name)
        item.setData(0, Qt.UserRole, obj)
        
        # Permite edição do nome ao dar duplo clique
        item.setFlags(item.flags() | Qt.ItemIsEditable)
        
        # Adiciona filhos recursivamente
        for child in obj.children:
            self.add_object_node(item, child)

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
            new_name = item.text(column)
            self.viewmodel.rename_object(obj, new_name)
