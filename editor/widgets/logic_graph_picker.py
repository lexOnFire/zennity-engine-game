"""Seletor interno de Logic Graphs para o componente do Inspector."""
from __future__ import annotations

import unicodedata
from pathlib import Path
from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QDialogButtonBox, QLabel, QLineEdit, QTreeWidget,
    QTreeWidgetItem, QVBoxLayout, QWidget, QPushButton,
)


def _search_key(value: Any) -> str:
    normalized = unicodedata.normalize("NFKD", str(value).casefold())
    return "".join(character for character in normalized if not unicodedata.combining(character))


class LogicGraphPickerDialog(QDialog):
    """Lista assets do projeto sem abrir o seletor de arquivos do sistema."""

    def __init__(self, entries: list[tuple[Path, dict[str, Any]]], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Vincular Lógica Visual")
        self.setModal(True)
        self.resize(540, 460)
        self._entries = entries
        self.selected_path: Path | None = None
        self.create_new = False

        layout = QVBoxLayout(self)
        title = QLabel("Vincular Lógica Visual")
        title.setObjectName("DialogTitle")
        layout.addWidget(title)
        hint = QLabel("Escolha um Logic Graph. O alvo será atualizado para o objeto selecionado.")
        hint.setWordWrap(True)
        hint.setObjectName("DialogDescription")
        layout.addWidget(hint)
        self.search = QLineEdit()
        self.search.setPlaceholderText("Pesquisar por nome, alvo ou evento...")
        self.search.setClearButtonEnabled(True)
        layout.addWidget(self.search)
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Logic Graph", "Alvo", "Nós"])
        self.tree.setRootIsDecorated(False)
        self.tree.setAlternatingRowColors(True)
        layout.addWidget(self.tree, 1)
        self.description = QLabel("Selecione um grafo para ver o resumo.")
        self.description.setWordWrap(True)
        layout.addWidget(self.description)
        self.create_button = QPushButton("＋ Criar novo do zero")
        self.create_button.setObjectName("CreateBlankLogicGraphButton")
        self.create_button.setProperty("uiRole", "primary")
        self.create_button.setToolTip(
            "Cria um Logic Graph vazio e já o vincula ao objeto selecionado"
        )
        layout.addWidget(self.create_button)
        self.buttons = QDialogButtonBox(QDialogButtonBox.Cancel | QDialogButtonBox.Ok)
        self.buttons.button(QDialogButtonBox.Ok).setText("Vincular")
        self.buttons.button(QDialogButtonBox.Ok).setEnabled(False)
        self.buttons.button(QDialogButtonBox.Cancel).setText("Cancelar")
        layout.addWidget(self.buttons)

        self.search.textChanged.connect(self._rebuild)
        self.tree.currentItemChanged.connect(self._selection_changed)
        self.tree.itemDoubleClicked.connect(lambda item, _column: self._accept_item(item))
        self.buttons.accepted.connect(self._accept_current)
        self.buttons.rejected.connect(self.reject)
        self.create_button.clicked.connect(self._accept_create_new)
        self._rebuild("")

    def _rebuild(self, query: str) -> None:
        wanted = _search_key(query).strip()
        self.tree.clear()
        for path, graph in self._entries:
            target = graph.get("target", {})
            events = [node.get("title", "Evento") for node in graph.get("nodes", []) if str(node.get("type", "")).startswith("event_")]
            searchable = _search_key(f"{path.stem} {graph.get('name', '')} {target.get('value', '')} {' '.join(events)}")
            if wanted and wanted not in searchable:
                continue
            enabled = bool(graph.get("enabled", True))
            target_text = str(target.get("value", "Sem alvo")) if enabled else "Desvinculado"
            item = QTreeWidgetItem([str(graph.get("name", path.stem)), target_text, str(len(graph.get("nodes", [])))])
            item.setData(0, Qt.UserRole, str(path))
            item.setData(0, Qt.UserRole + 1, events)
            self.tree.addTopLevelItem(item)
        self.tree.resizeColumnToContents(0)
        if self.tree.topLevelItemCount():
            self.tree.setCurrentItem(self.tree.topLevelItem(0))
        else:
            self.description.setText("Nenhum Logic Graph encontrado para esta pesquisa.")

    def _selection_changed(self, current: QTreeWidgetItem | None, _previous: QTreeWidgetItem | None) -> None:
        valid = current is not None and bool(current.data(0, Qt.UserRole))
        self.buttons.button(QDialogButtonBox.Ok).setEnabled(valid)
        if valid:
            events = current.data(0, Qt.UserRole + 1) or []
            self.description.setText(
                f"{current.text(2)} nó(s) • " + (f"Eventos: {', '.join(events)}" if events else "Sem eventos configurados")
            )

    def _accept_item(self, item: QTreeWidgetItem) -> None:
        value = item.data(0, Qt.UserRole)
        if value:
            self.selected_path = Path(str(value))
            self.accept()

    def _accept_current(self) -> None:
        current = self.tree.currentItem()
        if current is not None:
            self._accept_item(current)

    def _accept_create_new(self) -> None:
        self.create_new = True
        self.selected_path = None
        self.accept()
