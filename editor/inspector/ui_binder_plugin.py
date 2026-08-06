"""Inspector plugin para UIBinder com seleção visual de propriedades."""

from __future__ import annotations
from typing import Any

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QComboBox,
    QPushButton, QLabel, QTreeWidget, QTreeWidgetItem, QDialog,
    QDialogButtonBox
)
from PySide6.QtCore import Qt

from editor.inspector.plugin import InspectorPlugin
from editor.runtime.command_manager import CommandManager


class PropertyPickerDialog(QDialog):
    """Dialog para selecionar propriedade de um objeto."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Property Path")
        self.setGeometry(100, 100, 400, 500)

        layout = QVBoxLayout()

        # Info label
        info = QLabel("Select object → property to generate path")
        layout.addWidget(info)

        # Tree widget
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Object / Property"])
        layout.addWidget(self.tree)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)
        self.selected_path = ""

    def set_scene_objects(self, scene_objects: list[Any]) -> None:
        """Popula a árvore com objetos da cena."""
        self.tree.clear()

        for obj in scene_objects:
            obj_name = getattr(obj, "name", "Unknown")
            obj_item = QTreeWidgetItem([obj_name])
            obj_item.setData(0, Qt.UserRole, obj)

            # Adiciona propriedades do objeto
            try:
                for prop_name in dir(obj):
                    if prop_name.startswith("_"):
                        continue
                    try:
                        prop_value = getattr(obj, prop_name)
                        # Ignora métodos
                        if callable(prop_value):
                            continue
                        prop_text = f"{prop_name}: {type(prop_value).__name__}"
                        prop_item = QTreeWidgetItem([prop_text])
                        prop_item.setData(0, Qt.UserRole, f"{obj_name}.{prop_name}")
                        obj_item.addChild(prop_item)
                    except:
                        pass
            except:
                pass

            self.tree.addTopLevelItem(obj_item)

        self.tree.expandAll()

    def get_selected_path(self) -> str:
        """Retorna o caminho selecionado."""
        selected = self.tree.currentItem()
        if selected:
            path = selected.data(0, Qt.UserRole)
            if isinstance(path, str):
                return path.lower()  # "Player.health" → "player.health"
        return ""


class UIBinderPlugin(InspectorPlugin):
    """Editor visual para UIBinder component."""

    component_type = "UIBinder"
    title = "UI Binder"

    def create_widget(
        self,
        component: Any,
        command_manager: CommandManager | None,
        refresh: callable | None = None,
    ) -> QWidget:
        """Cria widget editor para UIBinder."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Source Path com Picker
        source_layout = QHBoxLayout()
        source_label = QLabel("Source Path:")
        self.source_input = QLineEdit()
        self.source_input.setText(getattr(component, "source_path", ""))
        self.source_input.setPlaceholderText("player.health")

        pick_btn = QPushButton("Pick...")
        pick_btn.clicked.connect(lambda: self._pick_source_path(component, command_manager, refresh))

        source_layout.addWidget(source_label)
        source_layout.addWidget(self.source_input)
        source_layout.addWidget(pick_btn)
        layout.addLayout(source_layout)

        # UI Element Name
        elem_layout = QHBoxLayout()
        elem_label = QLabel("UI Element:")
        self.elem_input = QLineEdit()
        self.elem_input.setText(getattr(component, "ui_element_name", ""))
        self.elem_input.setPlaceholderText("HealthLabel")
        elem_layout.addWidget(elem_label)
        elem_layout.addWidget(self.elem_input)
        layout.addLayout(elem_layout)

        # Bind Mode
        mode_layout = QHBoxLayout()
        mode_label = QLabel("Bind Mode:")
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["auto", "event"])
        self.mode_combo.setCurrentText(getattr(component, "bind_mode", "auto"))
        mode_layout.addWidget(mode_label)
        mode_layout.addWidget(self.mode_combo)
        layout.addLayout(mode_layout)

        # Format String
        fmt_layout = QHBoxLayout()
        fmt_label = QLabel("Format:")
        self.fmt_input = QLineEdit()
        self.fmt_input.setText(getattr(component, "format_string", "{value}"))
        self.fmt_input.setPlaceholderText("{value}/100")
        fmt_layout.addWidget(fmt_label)
        fmt_layout.addWidget(self.fmt_input)
        layout.addLayout(fmt_layout)

        # Conecta mudanças
        self.source_input.textChanged.connect(
            lambda text: self._set_property(component, "source_path", text, command_manager, refresh)
        )
        self.elem_input.textChanged.connect(
            lambda text: self._set_property(component, "ui_element_name", text, command_manager, refresh)
        )
        self.mode_combo.currentTextChanged.connect(
            lambda text: self._set_property(component, "bind_mode", text, command_manager, refresh)
        )
        self.fmt_input.textChanged.connect(
            lambda text: self._set_property(component, "format_string", text, command_manager, refresh)
        )

        # Store references
        self.component = component
        self.command_manager = command_manager
        self.refresh = refresh

        return widget

    def _pick_source_path(self, component: Any, command_manager: CommandManager | None, refresh: callable | None) -> None:
        """Abre dialog para picker visual."""
        # Tenta obter objetos da cena
        scene = getattr(component.game_object, "scene", None) if hasattr(component, "game_object") else None
        scene_objects = list(getattr(scene, "editable_objects", [])) if scene else []

        dialog = PropertyPickerDialog()
        dialog.set_scene_objects(scene_objects)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            path = dialog.get_selected_path()
            if path:
                self.source_input.setText(path)

    def _set_property(self, component: Any, prop_name: str, value: Any, command_manager: CommandManager | None, refresh: callable | None) -> None:
        """Define propriedade com undo/redo."""
        self.set_property(component, prop_name, value, command_manager, refresh)

    def refresh_widget(self, widget: QWidget, component: Any) -> None:
        """Atualiza widget quando componente muda."""
        if hasattr(self, "source_input"):
            self.source_input.blockSignals(True)
            self.source_input.setText(getattr(component, "source_path", ""))
            self.source_input.blockSignals(False)

        if hasattr(self, "elem_input"):
            self.elem_input.blockSignals(True)
            self.elem_input.setText(getattr(component, "ui_element_name", ""))
            self.elem_input.blockSignals(False)

        if hasattr(self, "mode_combo"):
            self.mode_combo.blockSignals(True)
            self.mode_combo.setCurrentText(getattr(component, "bind_mode", "auto"))
            self.mode_combo.blockSignals(False)

        if hasattr(self, "fmt_input"):
            self.fmt_input.blockSignals(True)
            self.fmt_input.setText(getattr(component, "format_string", "{value}"))
            self.fmt_input.blockSignals(False)
