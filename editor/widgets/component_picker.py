"""Seletor pesquisavel de componentes do Inspector isolado."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QDialogButtonBox, QLabel, QLineEdit, QTreeWidget,
    QTreeWidgetItem, QVBoxLayout, QWidget,
)


COMPONENT_CATALOG = (
    ("Renderização", "Sprite Renderer", "sprite", "Textura, cor e ordem de desenho"),
    ("Renderização", "Animator 2D", "animator", "Clipes e animações 2D"),
    ("Física", "RigidBody 2D", "rigidbody", "Gravidade e movimento físico"),
    ("Física", "Box Collider", "box", "Colisão retangular"),
    ("Física", "Circle Collider", "circle", "Colisão circular"),
    ("Câmera e áudio", "Camera 2D", "camera", "Visão e acompanhamento da cena"),
    ("Câmera e áudio", "Audio Source", "audio", "Reprodução de efeitos e música"),
    ("Interface", "Canvas", "ui_canvas", "Raiz da interface do jogo"),
    ("Interface", "UI Text", "ui_text", "Texto em screen-space"),
    ("Interface", "UI Image", "ui_image", "Imagem em screen-space"),
    ("Interface", "UI Button", "ui_button", "Botão com evento para scripts"),
    ("Código", "Script", "script", "Comportamento Python"),
)


class ComponentPickerDialog(QDialog):
    """Dialog compacto com busca, categorias e descrição dos componentes."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("ComponentPickerDialog")
        self.setWindowTitle("Adicionar Componente")
        self.setModal(True)
        self.resize(430, 480)
        self._selected_component: str | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        title = QLabel("Adicionar Componente")
        title.setObjectName("DialogTitle")
        layout.addWidget(title)

        self.search = QLineEdit()
        self.search.setPlaceholderText("Pesquisar componente...")
        self.search.setClearButtonEnabled(True)
        layout.addWidget(self.search)

        self.tree = QTreeWidget()
        self.tree.setObjectName("ComponentPickerTree")
        self.tree.setHeaderHidden(True)
        self.tree.setRootIsDecorated(True)
        self.tree.setIndentation(16)
        self.tree.setAlternatingRowColors(False)
        layout.addWidget(self.tree, 1)

        self.description = QLabel("Selecione um componente para ver sua função.")
        self.description.setObjectName("DialogDescription")
        self.description.setWordWrap(True)
        layout.addWidget(self.description)

        self.buttons = QDialogButtonBox(QDialogButtonBox.Cancel | QDialogButtonBox.Ok)
        self.buttons.button(QDialogButtonBox.Ok).setText("Adicionar")
        self.buttons.button(QDialogButtonBox.Ok).setProperty("uiRole", "primary")
        self.buttons.button(QDialogButtonBox.Cancel).setText("Cancelar")
        self.buttons.button(QDialogButtonBox.Ok).setEnabled(False)
        layout.addWidget(self.buttons)

        self.search.textChanged.connect(self._rebuild)
        self.tree.currentItemChanged.connect(self._selection_changed)
        self.tree.itemDoubleClicked.connect(lambda item, _column: self._accept_item(item))
        self.buttons.accepted.connect(self._accept_current)
        self.buttons.rejected.connect(self.reject)
        self._rebuild("")
        self.search.setFocus(Qt.OtherFocusReason)

    @property
    def selected_component(self) -> str | None:
        return self._selected_component

    def _rebuild(self, query: str) -> None:
        normalized = query.strip().casefold()
        self.tree.clear()
        self.description.setText("Selecione um componente para ver sua função.")
        categories: dict[str, QTreeWidgetItem] = {}
        for category, label, key, description in COMPONENT_CATALOG:
            searchable = f"{category} {label} {description}".casefold()
            if normalized and normalized not in searchable:
                continue
            parent = categories.get(category)
            if parent is None:
                parent = QTreeWidgetItem([category])
                parent.setFlags(parent.flags() & ~Qt.ItemIsSelectable)
                parent.setData(0, Qt.UserRole + 1, "category")
                categories[category] = parent
                self.tree.addTopLevelItem(parent)
            child = QTreeWidgetItem([label])
            child.setData(0, Qt.UserRole, key)
            child.setData(0, Qt.UserRole + 1, description)
            parent.addChild(child)
        self.tree.expandAll()
        if not categories:
            empty = QTreeWidgetItem(["Nenhum componente encontrado"])
            empty.setDisabled(True)
            self.tree.addTopLevelItem(empty)
            self.description.setText("Tente pesquisar por outro nome ou categoria.")
        if normalized:
            first = next((self.tree.topLevelItem(i).child(0) for i in range(self.tree.topLevelItemCount()) if self.tree.topLevelItem(i).childCount()), None)
            if first is not None:
                self.tree.setCurrentItem(first)

    def _selection_changed(self, current: QTreeWidgetItem | None, _previous: QTreeWidgetItem | None) -> None:
        key = current.data(0, Qt.UserRole) if current is not None else None
        valid = bool(key)
        self.buttons.button(QDialogButtonBox.Ok).setEnabled(valid)
        self.description.setText(str(current.data(0, Qt.UserRole + 1)) if valid else "Selecione um componente para ver sua função.")

    def _accept_item(self, item: QTreeWidgetItem) -> None:
        key = item.data(0, Qt.UserRole)
        if key:
            self._selected_component = str(key)
            self.accept()

    def _accept_current(self) -> None:
        current = self.tree.currentItem()
        if current is not None:
            self._accept_item(current)
