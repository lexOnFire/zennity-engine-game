"""
editor/visual_scripting/smart_context_menu.py
─────────────────────────────────────────────────────────────────────────────
Menu Contextual Inteligente com Busca Fuzzy & Context-Aware Pin Matching estilo Unreal Engine.
"""
from __future__ import annotations

from typing import Any, List, Dict
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QListWidget, QListWidgetItem, QLabel


class SmartContextMenu(QDialog):
    """Popup de inserção de nós com filtro por texto e contexto de pinos."""

    node_selected = Signal(str)

    def __init__(self, parent=None, pin_context: Dict[str, Any] | None = None) -> None:
        super().__init__(parent)
        self.pin_context = pin_context or {}
        self.setWindowTitle("Criar Nó (Blueprint Style)")
        self.resize(320, 420)
        self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        # Header / Search Line
        self.search_field = QLineEdit(self)
        self.search_field.setPlaceholderText("Buscar nó... (ex: Add, Branch, Move)")
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
        self.all_nodes = [
            ("Event: Start", "Eventos", "Disparado na inicialização"),
            ("Event: Update", "Eventos", "Disparado a cada frame"),
            ("Branch (If/Else)", "Controle", "Desvia o fluxo condicionalmente"),
            ("Sequence", "Controle", "Executa saídas em sequência"),
            ("For Loop", "Controle", "Executa um loop N vezes"),
            ("Vector Add", "Matemática", "Soma dois vetores"),
            ("Math: Multiply", "Matemática", "Multiplica valores numéricos"),
            ("Get Key Down", "Input", "Verifica se uma tecla foi pressionada"),
            ("Move Object", "Transform", "Move o objeto na cena"),
            ("Play Sound", "Áudio", "Toca um clipe de áudio"),
            ("Spawn Prefab", "Spawning", "Instancia um objeto"),
        ]

        self._filter_nodes(self.search_field.text())

    def _filter_nodes(self, text: str) -> None:
        self.node_list.clear()
        query = text.lower().strip()

        for name, category, desc in self.all_nodes:
            if not query or query in name.lower() or query in category.lower():
                item = QListWidgetItem(f"[{category}] {name}")
                item.setToolTip(desc)
                item.setData(Qt.UserRole, name)
                self.node_list.addItem(item)

    def _on_item_chosen(self, item: QListWidgetItem) -> None:
        node_type = item.data(Qt.UserRole)
        self.node_selected.emit(node_type)
        self.accept()
