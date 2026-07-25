"""Editor de Grafos Genérico (GenericGraphEditorWidget) da Zennity Engine.

Plataforma visual unificada reutilizada por:
- Behavior Tree Editor
- Dialogue Graph Editor
- Material Graph Editor
- Visual Scripting / Logic Graph
- Animator State Machine

Consome 100% o Graph Framework e o MetadataManager oficiais.
"""
from __future__ import annotations
from typing import List, Optional, Type
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QComboBox,
    QSplitter,
    QTreeWidget,
    QTreeWidgetItem,
)

from engine.core.context import EngineContext
from engine.metadata.manager import MetadataManager
from engine.core.metadata import NodeDefinition, PinType
from editor.widgets.graph_editor.graph_canvas import GraphCanvas


class GenericGraphEditorWidget(QWidget):
    """Widget de Editor de Grafos Genérico da Zennity Engine."""

    node_added = Signal(str)

    def __init__(self, graph_category_filter: str = "Behavior Tree", parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.category_filter = graph_category_filter

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # Toolbar Superior
        toolbar = QHBoxLayout()
        self.label_title = QLabel(f"🌐 Graph Editor ({graph_category_filter})", self)
        self.label_title.setStyleSheet("font-weight: bold; color: #EEEEFF;")

        self.btn_zoom_fit = QPushButton("🔍 Fit View", self)
        self.btn_zoom_fit.clicked.connect(self._on_zoom_fit)

        toolbar.addWidget(self.label_title)
        toolbar.addStretch(1)
        toolbar.addWidget(self.btn_zoom_fit)
        layout.addLayout(toolbar)

        # Splitter (Paleta de Nós à Esquerda | Canvas do Graph à Direita)
        splitter = QSplitter(Qt.Horizontal, self)

        # Paleta de Nós (TreeWidget)
        self.node_palette = QTreeWidget(splitter)
        self.node_palette.setHeaderLabel("Paleta de Nós")
        self.node_palette.itemDoubleClicked.connect(self._on_node_double_clicked)
        splitter.addWidget(self.node_palette)

        # Canvas do Graph Framework
        self.canvas = GraphCanvas(splitter)
        splitter.addWidget(self.canvas)

        splitter.setSizes([180, 620])
        layout.addWidget(splitter, 1)

        self.populate_node_palette()

    def populate_node_palette(self) -> None:
        self.node_palette.clear()
        context = EngineContext.current()
        if not context:
            return

        meta_manager = context.services.get_optional(MetadataManager)
        if not meta_manager:
            return

        node_defs = meta_manager.get_all(NodeDefinition)
        category_nodes: dict[str, List[NodeDefinition]] = {}

        for ndef in node_defs:
            cat = getattr(ndef, "category_key", "General")
            if self.category_filter.lower() in cat.lower() or not self.category_filter:
                category_nodes.setdefault(cat, []).append(ndef)

        for cat_name, ndefs in category_nodes.items():
            cat_item = QTreeWidgetItem(self.node_palette, [cat_name])
            cat_item.setExpanded(True)
            for ndef in ndefs:
                node_item = QTreeWidgetItem(cat_item, [ndef.id])
                node_item.setData(0, Qt.UserRole, ndef)

    def _on_node_double_clicked(self, item: QTreeWidgetItem, column: int) -> None:
        ndef = item.data(0, Qt.UserRole)
        if isinstance(ndef, NodeDefinition):
            self.node_added.emit(ndef.id)

    def _on_zoom_fit(self) -> None:
        pass
