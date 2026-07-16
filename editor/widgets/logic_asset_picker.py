"""Seletor interno de imagens, animações e sons para nós visuais."""
from __future__ import annotations

import unicodedata
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QDialogButtonBox, QLabel, QLineEdit, QTreeWidget,
    QTreeWidgetItem, QVBoxLayout, QWidget,
)


ASSET_KINDS = {
    "image": ("Imagem", {".png", ".jpg", ".jpeg", ".bmp", ".webp"}),
    "animation": ("Animação", {".zanim"}),
    "audio": ("Áudio", {".wav", ".ogg", ".mp3", ".flac"}),
}


def _search_key(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", str(value).casefold())
    return "".join(character for character in normalized if not unicodedata.combining(character))


class LogicAssetPickerDialog(QDialog):
    """Pesquisa somente assets compatíveis dentro do projeto atual."""

    def __init__(self, project_root: Path, kind: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        if kind not in ASSET_KINDS:
            raise ValueError(f"Tipo de asset desconhecido: {kind}")
        self.project_root = Path(project_root).resolve()
        self.kind = kind
        self.selected_path = ""
        label, self.extensions = ASSET_KINDS[kind]
        self.setWindowTitle(f"Selecionar {label}")
        self.setModal(True)
        self.resize(600, 480)

        layout = QVBoxLayout(self)
        title = QLabel(f"Vincular {label} ao bloco")
        title.setObjectName("DialogTitle")
        layout.addWidget(title)
        hint = QLabel("Escolha um arquivo de Assets. O caminho relativo será salvo no Logic Graph.")
        hint.setObjectName("DialogDescription")
        hint.setWordWrap(True)
        layout.addWidget(hint)
        self.search = QLineEdit()
        self.search.setPlaceholderText(f"Pesquisar {label.lower()}...")
        self.search.setClearButtonEnabled(True)
        layout.addWidget(self.search)
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Asset", "Tipo", "Pasta"])
        self.tree.setRootIsDecorated(False)
        self.tree.setAlternatingRowColors(True)
        layout.addWidget(self.tree, 1)
        self.summary = QLabel()
        self.summary.setObjectName("PanelHint")
        self.summary.setWordWrap(True)
        layout.addWidget(self.summary)
        self.buttons = QDialogButtonBox(QDialogButtonBox.Cancel | QDialogButtonBox.Ok)
        self.buttons.button(QDialogButtonBox.Ok).setText("Vincular")
        self.buttons.button(QDialogButtonBox.Ok).setProperty("uiRole", "primary")
        self.buttons.button(QDialogButtonBox.Ok).setEnabled(False)
        self.buttons.button(QDialogButtonBox.Cancel).setText("Cancelar")
        layout.addWidget(self.buttons)

        self.search.textChanged.connect(self._rebuild)
        self.tree.currentItemChanged.connect(self._selection_changed)
        self.tree.itemDoubleClicked.connect(lambda item, _column: self._accept_item(item))
        self.buttons.accepted.connect(self._accept_current)
        self.buttons.rejected.connect(self.reject)
        self._entries = self._assets()
        self._rebuild("")

    def _assets(self) -> list[Path]:
        directory = self.project_root / "Assets"
        if not directory.is_dir():
            return []
        return sorted(
            (path for path in directory.rglob("*") if path.is_file() and path.suffix.lower() in self.extensions),
            key=lambda path: str(path.relative_to(directory)).casefold(),
        )

    def _rebuild(self, query: str) -> None:
        wanted = _search_key(query).strip()
        self.tree.clear()
        label, _extensions = ASSET_KINDS[self.kind]
        for path in self._entries:
            relative = path.relative_to(self.project_root).as_posix()
            if wanted and wanted not in _search_key(relative):
                continue
            item = QTreeWidgetItem([path.name, label, path.parent.relative_to(self.project_root).as_posix()])
            item.setData(0, Qt.UserRole, relative)
            self.tree.addTopLevelItem(item)
        self.tree.resizeColumnToContents(0)
        if self.tree.topLevelItemCount():
            self.tree.setCurrentItem(self.tree.topLevelItem(0))
        else:
            self.summary.setText(f"Nenhum asset compatível encontrado em Assets ({', '.join(sorted(self.extensions))}).")
            self.buttons.button(QDialogButtonBox.Ok).setEnabled(False)

    def _selection_changed(self, current: QTreeWidgetItem | None, _previous: QTreeWidgetItem | None) -> None:
        path = str(current.data(0, Qt.UserRole)) if current is not None else ""
        self.buttons.button(QDialogButtonBox.Ok).setEnabled(bool(path))
        if path:
            self.summary.setText(path)

    def _accept_item(self, item: QTreeWidgetItem) -> None:
        path = str(item.data(0, Qt.UserRole) or "")
        if path:
            self.selected_path = path
            self.accept()

    def _accept_current(self) -> None:
        current = self.tree.currentItem()
        if current is not None:
            self._accept_item(current)
