"""
editor/visual_scripting/smart_context_menu.py
─────────────────────────────────────────────────────────────────────────────
Menu Contextual Inteligente com Busca Fuzzy & Context-Aware Pin Matching estilo Unreal Engine.
"""
from __future__ import annotations

from typing import Any, List, Dict
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QListWidget, QListWidgetItem, QLabel


from engine.logic.node_definitions import NODE_DEFINITIONS


class SmartContextMenu(QDialog):
    """Popup de inserção de nós com filtro por texto e contexto de pinos."""

    node_selected = Signal(str)

    def __init__(self, parent=None, pin_context: Dict[str, Any] | None = None) -> None:
        super().__init__(parent)
        self.pin_context = pin_context or {}
        self.setWindowTitle("Criar Nó (Blueprint Style)")
        self.resize(340, 450)
        self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        # Header / Search Line
        self.search_field = QLineEdit(self)
        self.search_field.setPlaceholderText("Buscar nó... (ex: Add, Branch, Move, Timer)")
        self.search_field.setStyleSheet("""
            QLineEdit {
                background-color: #1a1d22;
                color: #e0e0e0;
                border: 1px solid #0096ff;
                border-radius: 4px;
                padding: 6px;
                font-size: 13px;
            }
        """)
        self.search_field.textChanged.connect(self._filter_nodes)
        layout.addWidget(self.search_field)

        # Info de Contexto
        if self.pin_context:
            context_lbl = QLabel(f"Filtrando para pino: <b>{self.pin_context.get('type', 'Any')}</b>", self)
            context_lbl.setStyleSheet("color: #00e5ff; font-size: 11px; margin-top: 2px;")
            layout.addWidget(context_lbl)

        # Lista de Nós
        self.node_list = QListWidget(self)
        self.node_list.setStyleSheet("""
            QListWidget {
                background-color: #121418;
                color: #d0d0d0;
                border: 1px solid #2a2e36;
                border-radius: 4px;
            }
            QListWidget::item {
                padding: 6px;
                border-bottom: 1px solid #1a1d22;
            }
            QListWidget::item:hover {
                background-color: #007acc;
                color: #ffffff;
            }
            QListWidget::item:selected {
                background-color: #0096ff;
                color: #ffffff;
            }
        """)
        self.node_list.itemDoubleClicked.connect(self._on_item_chosen)
        layout.addWidget(self.node_list)

        self._populate_nodes()

    def _populate_nodes(self) -> None:
        self.all_nodes = []
        for node_type, definition in NODE_DEFINITIONS.items():
            title = str(definition.get("title", node_type))
            category = str(definition.get("category", "Geral"))
            desc = f"{category} • Conector nativo de {title}"
            self.all_nodes.append((title, category, desc, node_type))

        self.all_nodes.sort(key=lambda item: (item[1].lower(), item[0].lower()))
        self._filter_nodes(self.search_field.text())

    def _filter_nodes(self, text: str) -> None:
        self.node_list.clear()
        query = text.lower().strip()

        for title, category, desc, node_type in self.all_nodes:
            if not query or query in title.lower() or query in category.lower() or query in node_type.lower():
                item = QListWidgetItem(f"[{category}] {title}")
                item.setToolTip(f"{desc} ({node_type})")
                item.setData(Qt.UserRole, node_type)
                self.node_list.addItem(item)

    def _on_item_chosen(self, item: QListWidgetItem) -> None:
        node_type = item.data(Qt.UserRole)
        self.node_selected.emit(node_type)
        self.accept()
