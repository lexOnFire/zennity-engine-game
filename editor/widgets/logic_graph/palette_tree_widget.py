"""TreeWidget para exibir nós do Logic Graph agrupados por subcategoria."""

from __future__ import annotations
from typing import Any, Dict, List

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QTreeWidget, QTreeWidgetItem, QAbstractItemView
)

from editor.widgets.logic_graph.definitions import CATEGORY_COLORS
from engine.logic.graph_asset import NODE_DEFINITIONS, UNIQUE_EVENT_TYPES
from editor.widgets.logic_graph.definitions import NODE_DESCRIPTIONS


class PaletteTreeWidget(QTreeWidget):
    """TreeWidget para paleta de nós com suporte a categorias hierárquicas."""

    item_double_clicked = Signal(QTreeWidgetItem)
    item_selected = Signal(QTreeWidgetItem)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setColumnCount(1)
        self.setHeaderLabel("")
        self.setHeaderHidden(True)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.itemDoubleClicked.connect(self._on_item_double_clicked)
        self.itemSelectionChanged.connect(self._on_selection_changed)
        self._node_items: Dict[str, QTreeWidgetItem] = {}

    def populate_with_groups(
        self,
        node_groups: Dict[str, Dict[str, List[str]]],
        query: str = ""
    ) -> int:
        """Popula a árvore com nós agrupados por subcategoria.

        Args:
            node_groups: Dicionário {category: {subcategory: [node_ids]}}
            query: String de busca para filtrar nós

        Returns:
            Número de nós exibidos
        """
        self.clear()
        self._node_items.clear()

        if not query:
            # Modo agrupado: exibir árvore hierárquica
            return self._populate_grouped(node_groups)
        else:
            # Modo busca: exibir resultados planos
            return self._populate_search(node_groups, query)

    def _populate_grouped(self, node_groups: Dict[str, Dict[str, List[str]]]) -> int:
        """Exibe nós em árvore hierárquica (Categoria → Subcategoria → Nó)."""
        count = 0

        for category, subcategories in sorted(node_groups.items()):
            # Cria item para categoria
            category_item = QTreeWidgetItem([category])
            category_item.setData(0, Qt.UserRole, None)  # Sem node_type

            # Estilo da categoria
            color = CATEGORY_COLORS.get(category, QColor("#78909c"))
            font = QFont()
            font.setBold(True)
            category_item.setFont(0, font)
            category_item.setForeground(0, color)

            # Cria items para subcategorias
            for subcategory, node_ids in sorted(subcategories.items()):
                subcategory_item = QTreeWidgetItem([subcategory])
                subcategory_item.setData(0, Qt.UserRole, None)

                # Estilo da subcategoria
                font = QFont()
                font.setItalic(True)
                subcategory_item.setFont(0, font)
                subcategory_item.setForeground(0, QColor("#90a4ae"))

                # Cria items para nós
                for node_type in node_ids:
                    definition = NODE_DEFINITIONS.get(node_type, {})
                    title = str(definition.get("title", node_type))

                    node_item = QTreeWidgetItem([title])
                    node_item.setData(0, Qt.UserRole, node_type)

                    # Tooltip com descrição
                    description = NODE_DESCRIPTIONS.get(node_type, "")
                    tooltip = f"{category} • {description}"
                    node_item.setToolTip(0, tooltip)

                    subcategory_item.addChild(node_item)
                    self._node_items[node_type] = node_item
                    count += 1

                category_item.addChild(subcategory_item)

            self.addTopLevelItem(category_item)
            category_item.setExpanded(True)

        return count

    def _populate_search(
        self,
        node_groups: Dict[str, Dict[str, List[str]]],
        query: str
    ) -> int:
        """Exibe nós em modo busca plano (sem agrupamento)."""
        count = 0

        # Coleta todos os nós que matcham a busca
        matching_nodes: List[tuple[str, str, str]] = []  # (node_type, title, category)

        for category, subcategories in node_groups.items():
            for subcategory, node_ids in subcategories.items():
                for node_type in node_ids:
                    definition = NODE_DEFINITIONS.get(node_type, {})
                    title = str(definition.get("title", node_type))

                    # Verifica se node_type ou title matcham a busca
                    if query.lower() in node_type.lower() or query.lower() in title.lower():
                        matching_nodes.append((node_type, title, category))

        # Exibe nós de busca agrupados por categoria (simples)
        for category, subcategories in node_groups.items():
            category_items = [
                (node_type, title)
                for node_type, title, cat in matching_nodes
                if cat == category
            ]

            if not category_items:
                continue

            category_item = QTreeWidgetItem([category])
            category_item.setData(0, Qt.UserRole, None)

            color = CATEGORY_COLORS.get(category, QColor("#78909c"))
            font = QFont()
            font.setBold(True)
            category_item.setFont(0, font)
            category_item.setForeground(0, color)

            for node_type, title in category_items:
                definition = NODE_DEFINITIONS.get(node_type, {})
                node_item = QTreeWidgetItem([title])
                node_item.setData(0, Qt.UserRole, node_type)

                description = NODE_DESCRIPTIONS.get(node_type, "")
                tooltip = f"{category} • {description}"
                node_item.setToolTip(0, tooltip)

                category_item.addChild(node_item)
                self._node_items[node_type] = node_item
                count += 1

            self.addTopLevelItem(category_item)
            category_item.setExpanded(True)

        return count

    def _on_item_double_clicked(self, item: QTreeWidgetItem) -> None:
        """Emite sinal quando item é clicado duas vezes."""
        node_type = item.data(0, Qt.UserRole)
        if node_type:
            self.item_double_clicked.emit(item)

    def _on_selection_changed(self) -> None:
        """Emite sinal quando seleção muda."""
        selected = self.selectedItems()
        if selected:
            self.item_selected.emit(selected[0])

    def get_selected_node_type(self) -> str | None:
        """Retorna o node_type do item selecionado."""
        selected = self.selectedItems()
        if selected:
            return selected[0].data(0, Qt.UserRole)
        return None

    def set_item_count_label(self, count: int, query: str = "") -> str:
        """Retorna texto para exibir contagem."""
        if query:
            return f"{count} bloco(s) encontrados"
        return f"{count} bloco(s) nesta categoria"
