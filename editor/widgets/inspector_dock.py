from __future__ import annotations

from copy import deepcopy
from typing import Optional

from PySide6.QtCore import Qt, Slot
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDockWidget,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMenu,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from engine.game_object import GameObject
from editor.inspector import InspectorPluginRegistry, inspector_plugin_registry
from editor.runtime.command_manager import FunctionCommand
from editor.viewmodels.scene_viewmodel import SceneViewModel


class InspectorDock(QDockWidget):
    """
    Painel acoplável do Inspetor de Propriedades (Inspector) estilizado.
    Componente 'View' na arquitetura MVVM do editor.
    """

    def __init__(self, parent: QWidget = None) -> None:
        super().__init__("Inspector", parent)
        self.setObjectName("InspectorDock")
        self.setAllowedAreas(Qt.RightDockWidgetArea | Qt.LeftDockWidgetArea)

        self.viewmodel: Optional[SceneViewModel] = None
        self.plugin_registry: InspectorPluginRegistry = inspector_plugin_registry
        self._block_updates = False
        self._component_filter_text = ""
        self._component_clipboard: dict[str, object] | None = None

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)

        self.main_content = QWidget()
        self.main_content.setObjectName("main_content")
        self.layout_content = QVBoxLayout(self.main_content)
        self.layout_content.setContentsMargins(10, 10, 10, 10)
        self.layout_content.setSpacing(10)
        self.layout_content.setAlignment(Qt.AlignTop)

        self.scroll.setWidget(self.main_content)
        self.setWidget(self.scroll)

        self.setStyleSheet("""
            QWidget#main_content {
                background-color: #1a1a1a;
            }
            QScrollArea {
                background-color: #1a1a1a;
                border: none;
            }
            QWidget {
                font-family: 'Segoe UI', sans-serif;
                font-size: 11px;
                color: #c5c5c5;
            }
            QLineEdit {
                background-color: #202020;
                border: 1px solid #151515;
                border-radius: 3px;
                padding: 4px;
                color: #ffffff;
            }
            QLineEdit:focus {
                border: 1px solid #4f4f4f;
                background-color: #282828;
            }
            QComboBox {
                background-color: #2b2b2b;
                border: 1px solid #202020;
                border-radius: 3px;
                padding: 3px 6px;
                color: #e0e0e0;
            }
            QComboBox:focus {
                border: 1px solid #4f4f4f;
            }
            QComboBox::drop-down {
                border: none;
                width: 14px;
            }
            QComboBox::down-arrow {
                border-style: solid;
                border-width: 3px 3px 0 3px;
                border-color: #a0a0a0 transparent transparent transparent;
            }
            QDoubleSpinBox, QSpinBox {
                background-color: #202020;
                border: 1px solid #151515;
                border-radius: 3px;
                color: #ffffff;
                padding: 3px;
            }
            QDoubleSpinBox:focus, QSpinBox:focus {
                border: 1px solid #4f4f4f;
                background-color: #282828;
            }
            QDoubleSpinBox::up-button, QDoubleSpinBox::down-button,
            QSpinBox::up-button, QSpinBox::down-button {
                width: 0px;
                height: 0px;
                border: none;
                background: transparent;
            }
            QCheckBox {
                spacing: 5px;
            }
            QCheckBox::indicator {
                width: 14px;
                height: 14px;
                background-color: #202020;
                border: 1px solid #151515;
                border-radius: 2px;
            }
            QCheckBox::indicator:checked {
                background-color: #383838;
                border: 1px solid #5f5f5f;
            }
            QPushButton {
                background-color: #3c3c3c;
                border: 1px solid #282828;
                border-radius: 3px;
                color: #e0e0e0;
                padding: 5px 12px;
            }
            QPushButton:hover {
                background-color: #484848;
            }
            QPushButton:pressed {
                background-color: #2b2b2b;
            }
            QWidget[componentDisabled="true"] {
                color: #777777;
            }
            QLineEdit#InspectorComponentFilter {
                padding: 5px 8px;
                color: #d8d8d8;
            }
        """)

        self.show_empty_state()

    def set_viewmodel(self, viewmodel: SceneViewModel) -> None:
        """Conecta o Inspector ao ViewModel da cena."""
        self.viewmodel = viewmodel
        self.viewmodel.selection_changed.connect(self.on_selection_changed)
        self.viewmodel.property_changed.connect(self.on_property_changed)

    def set_inspector_plugin_registry(self, registry: InspectorPluginRegistry) -> None:
        self.plugin_registry = registry

    def show_empty_state(self) -> None:
        """Exibe tela vazia padrão."""
        self.clear_layout()
        lbl = QLabel("Selecione um objeto para visualizar suas propriedades.")
        lbl.setStyleSheet("color: #606060; font-size: 11px;")
        lbl.setWordWrap(True)
        lbl.setAlignment(Qt.AlignCenter)
        self.layout_content.addWidget(lbl)

    def clear_layout(self) -> None:
        """Remove todos os widgets da área de exibição."""
        while self.layout_content.count():
            item = self.layout_content.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self._clear_sub_layout(item.layout())

    def _clear_sub_layout(self, layout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self._clear_sub_layout(item.layout())

    def _selected_components(self, obj: GameObject) -> list[object]:
        components = list(getattr(obj, "components", []))
        if hasattr(obj, "script_path") and not any(getattr(comp, "type_name", type(comp).__name__) == "Script" for comp in components):
            components.append(_ScriptProxy(obj))
        return components

    def _refresh_selected(self) -> None:
        if self.viewmodel and self.viewmodel.selected_object:
            self.on_selection_changed(self.viewmodel.selected_object)

    def _component_display_name(self, component: object) -> str:
        type_name = getattr(component, "type_name", type(component).__name__)
        return str(getattr(component, "name", type_name) or type_name)

    def _component_matches_filter(self, component: object) -> bool:
        needle = self._component_filter_text.strip().lower()
        if not needle:
            return True
        values = {
            self._component_display_name(component),
            getattr(component, "component_type", ""),
            getattr(component, "type_name", type(component).__name__),
            type(component).__name__,
        }
        return any(needle in str(value).lower() for value in values)

    def _add_component_filter(self) -> None:
        filter_box = QLineEdit()
        filter_box.setObjectName("InspectorComponentFilter")
        filter_box.setPlaceholderText("Filtrar componentes...")
        filter_box.setText(self._component_filter_text)
        filter_box.textChanged.connect(self._on_component_filter_changed)
        self.layout_content.addWidget(filter_box)
        self.component_filter = filter_box

    @Slot(str)
    def _on_component_filter_changed(self, text: str) -> None:
        if self._component_filter_text == text:
            return
        self._component_filter_text = text
        self._refresh_selected()

    @Slot(object)
    def on_selection_changed(self, obj: Optional[GameObject]) -> None:
        """Reconstrói dinamicamente os widgets quando o objeto selecionado muda."""
        if not obj or not self.viewmodel:
            self.show_empty_state()
            return

        self._block_updates = True
        self.clear_layout()

        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 4)
        top_row.setSpacing(6)

        self.chk_active = QCheckBox()
        self.chk_active.setChecked(getattr(obj, "active", True))
        self.chk_active.clicked.connect(self.on_active_toggled)

        self.txt_name = QLineEdit(obj.name)
        self.txt_name.setStyleSheet(
            "font-weight: bold; font-size: 12px; background-color: #202020; border: 1px solid #151515; border-radius: 3px; padding: 4px;"
        )
        self.txt_name.editingFinished.connect(self.on_name_edited)

        self.chk_static = QCheckBox("Estático")
        self.chk_static.setChecked(getattr(obj, "is_static", False))
        self.chk_static.clicked.connect(self.on_static_toggled)

        top_row.addWidget(self.chk_active)
        top_row.addWidget(self.txt_name, 1)
        top_row.addWidget(self.chk_static)
        self.layout_content.addLayout(top_row)

        tag_layer_row = QHBoxLayout()
        tag_layer_row.setContentsMargins(0, 0, 0, 8)
        tag_layer_row.setSpacing(8)

        tag_layout = QHBoxLayout()
        tag_layout.setSpacing(4)
        lbl_tag = QLabel("Tag")
        lbl_tag.setStyleSheet("color: #8c8c8c; font-size: 11px;")
        self.cb_tag = QComboBox()
        self.cb_tag.addItems(["Untagged", "Player", "Enemy", "MainCamera", "UI"])
        self.cb_tag.setCurrentText(obj.tag or "Untagged")
        self.cb_tag.currentTextChanged.connect(self.on_tag_changed)
        tag_layout.addWidget(lbl_tag)
        tag_layout.addWidget(self.cb_tag, 1)

        layer_layout = QHBoxLayout()
        layer_layout.setSpacing(4)
        lbl_layer = QLabel("Layer")
        lbl_layer.setStyleSheet("color: #8c8c8c; font-size: 11px;")
        self.cb_layer = QComboBox()
        self.cb_layer.addItems(["Default", "TransparentFX", "Ignore Raycast", "Water", "UI"])
        self.cb_layer.setCurrentText(getattr(obj, "layer", "Default"))
        self.cb_layer.currentTextChanged.connect(self.on_layer_changed)
        layer_layout.addWidget(lbl_layer)
        layer_layout.addWidget(self.cb_layer, 1)

        tag_layer_row.addLayout(tag_layout, 1)
        tag_layer_row.addLayout(layer_layout, 1)
        self.layout_content.addLayout(tag_layer_row)
        self._add_component_filter()

        command_manager = getattr(self.viewmodel, "command_manager", None)
        visible_count = 0
        for component in self._selected_components(obj):
            if not self._component_matches_filter(component):
                continue
            plugin = self.plugin_registry.plugin_for(component)
            if plugin is None:
                fallback = QLabel(getattr(component, "type_name", type(component).__name__))
                fallback.setStyleSheet("color: #888888; padding: 6px;")
                self.layout_content.addWidget(fallback)
                continue
            widget = plugin.create_widget(
                component,
                command_manager,
                self._refresh_selected,
            )
            widget.setProperty("componentDisabled", not bool(getattr(component, "enabled", True)))
            widget.setToolTip("Clique com o botão direito para ações do componente")
            self._attach_component_context_menu(widget, obj, component)
            self.layout_content.addWidget(widget)
            self._capture_legacy_widget_alias(component, widget)
            visible_count += 1

        if visible_count == 0:
            empty_filter = QLabel("Nenhum componente encontrado pelo filtro.")
            empty_filter.setStyleSheet("color: #707070; padding: 6px;")
            self.layout_content.addWidget(empty_filter)

        btn_add = QPushButton("Adicionar Componente")
        btn_add.setStyleSheet("font-weight: bold; padding: 6px; margin-top: 8px;")
        self.layout_content.addWidget(btn_add)

        self._block_updates = False

    def _attach_component_context_menu(self, widget: QWidget, obj: GameObject, component: object) -> None:
        widget.setContextMenuPolicy(Qt.CustomContextMenu)
        widget.customContextMenuRequested.connect(
            lambda pos, w=widget, o=obj, c=component: self._show_component_context_menu(w, o, c, pos)
        )

    def _show_component_context_menu(self, widget: QWidget, obj: GameObject, component: object, pos) -> None:
        menu = QMenu(widget)
        type_name = getattr(component, "type_name", type(component).__name__)
        components = list(getattr(obj, "components", []))
        in_component_list = component in components
        is_required = bool(getattr(component, "required", False)) or component is getattr(obj, "transform", None)
        clipboard_type = None if self._component_clipboard is None else self._component_clipboard.get("type")

        act_reset = menu.addAction("Reset Component")
        act_copy = menu.addAction("Copy Component")
        act_paste = menu.addAction("Paste Component Values")
        menu.addSeparator()
        act_move_up = menu.addAction("Move Up")
        act_move_down = menu.addAction("Move Down")
        act_remove = menu.addAction("Remove Component")

        act_reset.setEnabled(hasattr(component, "deserialize_properties"))
        act_paste.setEnabled(clipboard_type == type_name and hasattr(component, "deserialize_properties"))
        act_move_up.setEnabled(in_component_list and components.index(component) > 0)
        act_move_down.setEnabled(in_component_list and components.index(component) < len(components) - 1)
        act_remove.setEnabled(in_component_list and not is_required)

        action = menu.exec(widget.mapToGlobal(pos))
        if action == act_reset:
            self._reset_component(component)
        elif action == act_copy:
            self._copy_component(component)
        elif action == act_paste:
            self._paste_component_values(component)
        elif action == act_move_up:
            self._move_component(obj, component, -1)
        elif action == act_move_down:
            self._move_component(obj, component, 1)
        elif action == act_remove:
            self._remove_component(obj, component)

    def _command_manager(self):
        return getattr(self.viewmodel, "command_manager", None) if self.viewmodel else None

    def _component_snapshot(self, component: object) -> dict[str, object]:
        if hasattr(component, "serialize"):
            serialized = deepcopy(component.serialize())
            return {
                "type": getattr(component, "type_name", type(component).__name__),
                "enabled": bool(serialized.get("enabled", getattr(component, "enabled", True))),
                "properties": deepcopy(serialized.get("properties", {})),
            }
        return {
            "type": getattr(component, "type_name", type(component).__name__),
            "enabled": bool(getattr(component, "enabled", True)),
            "properties": {},
        }

    def _apply_component_snapshot(self, component: object, snapshot: dict[str, object]) -> None:
        if hasattr(component, "enabled"):
            component.enabled = bool(snapshot.get("enabled", True))
        properties = deepcopy(snapshot.get("properties", {}))
        if hasattr(component, "deserialize_properties") and type(properties) is dict:
            component.deserialize_properties(properties)
        self._refresh_selected()

    def _copy_component(self, component: object) -> None:
        self._component_clipboard = self._component_snapshot(component)

    def _paste_component_values(self, component: object) -> None:
        if self._component_clipboard is None:
            return
        type_name = getattr(component, "type_name", type(component).__name__)
        if self._component_clipboard.get("type") != type_name:
            return
        old_snapshot = self._component_snapshot(component)
        new_snapshot = deepcopy(self._component_clipboard)
        if old_snapshot == new_snapshot:
            return

        def apply() -> None:
            self._apply_component_snapshot(component, new_snapshot)

        def undo() -> None:
            self._apply_component_snapshot(component, old_snapshot)

        command_manager = self._command_manager()
        if command_manager is None:
            apply()
        else:
            command_manager.execute(FunctionCommand(f"Paste {type_name} Values", apply, undo))

    def _reset_component(self, component: object) -> None:
        if not hasattr(component, "deserialize_properties"):
            return
        try:
            default_component = type(component)()
        except Exception:
            return
        old_snapshot = self._component_snapshot(component)
        new_snapshot = self._component_snapshot(default_component)
        if old_snapshot == new_snapshot:
            return

        def apply() -> None:
            self._apply_component_snapshot(component, new_snapshot)

        def undo() -> None:
            self._apply_component_snapshot(component, old_snapshot)

        command_manager = self._command_manager()
        if command_manager is None:
            apply()
        else:
            command_manager.execute(FunctionCommand(f"Reset {new_snapshot['type']}", apply, undo))

    def _move_component(self, obj: GameObject, component: object, direction: int) -> None:
        components = getattr(obj, "components", [])
        if component not in components:
            return
        old_index = components.index(component)
        new_index = old_index + int(direction)
        if new_index < 0 or new_index >= len(components):
            return

        def move_to(index: int) -> None:
            if component in components:
                components.remove(component)
            components.insert(index, component)
            self._refresh_selected()

        command_manager = self._command_manager()
        if command_manager is None:
            move_to(new_index)
        else:
            command_manager.execute(
                FunctionCommand(
                    f"Move {getattr(component, 'type_name', type(component).__name__)} Component",
                    lambda: move_to(new_index),
                    lambda: move_to(old_index),
                )
            )

    def _remove_component(self, obj: GameObject, component: object) -> None:
        components = getattr(obj, "components", [])
        if component not in components:
            return
        if component is getattr(obj, "transform", None) or getattr(component, "required", False):
            return
        index = components.index(component)

        def remove() -> None:
            if component in components:
                components.remove(component)
                component.game_object = None
            self._refresh_selected()

        def restore() -> None:
            if component not in components:
                component.game_object = obj
                components.insert(max(0, min(index, len(components))), component)
            self._refresh_selected()

        command_manager = self._command_manager()
        if command_manager is None:
            remove()
        else:
            command_manager.execute(
                FunctionCommand(
                    f"Remove {getattr(component, 'type_name', type(component).__name__)} Component",
                    remove,
                    restore,
                )
            )

    def _set_object_property(self, property_name: str, value: object, description: str | None = None) -> None:
        if not self.viewmodel or not self.viewmodel.selected_object:
            return
        obj = self.viewmodel.selected_object
        old_value = getattr(obj, property_name, None)
        if old_value == value:
            return

        def apply(next_value: object = value) -> None:
            setattr(obj, property_name, next_value)
            self._refresh_selected()

        def undo(previous_value: object = old_value) -> None:
            setattr(obj, property_name, previous_value)
            self._refresh_selected()

        command_manager = self._command_manager()
        if command_manager is None:
            apply()
        else:
            command_manager.execute(FunctionCommand(description or f"Set GameObject.{property_name}", apply, undo))

    def _capture_legacy_widget_alias(self, component: object, widget: QWidget) -> None:
        type_name = getattr(component, "type_name", type(component).__name__)
        if type_name == "Transform":
            self.transform_widget = widget
        elif type_name == "RigidBody":
            self.rb_widget = widget
        elif type_name in {"BoxCollider", "CircleCollider"}:
            self.col_widget = widget
        elif type_name == "Script":
            self.script_widget = widget

    @Slot()
    def on_name_edited(self) -> None:
        """Notifica o ViewModel sobre a mudança de nome do objeto."""
        if not self.viewmodel or not self.viewmodel.selected_object:
            return
        new_name = self.txt_name.text().strip()
        if not new_name:
            self.txt_name.setText(self.viewmodel.selected_object.name)
            return
        self.viewmodel.rename_object(self.viewmodel.selected_object, new_name)

    @Slot(bool)
    def on_active_toggled(self, checked: bool) -> None:
        self._set_object_property("active", bool(checked), "Set GameObject.active")

    @Slot(bool)
    def on_static_toggled(self, checked: bool) -> None:
        self._set_object_property("is_static", bool(checked), "Set GameObject.is_static")

    @Slot(str)
    def on_tag_changed(self, text: str) -> None:
        self._set_object_property("tag", text, "Set GameObject.tag")

    @Slot(str)
    def on_layer_changed(self, text: str) -> None:
        self._set_object_property("layer", text, "Set GameObject.layer")

    @Slot(str, str, object)
    def on_property_changed(self, component_name: str, property_name: str, value: object) -> None:
        """Chamado quando uma propriedade é alterada externamente (ex: sincroniza visual)."""
        if self._block_updates or not self.viewmodel or not self.viewmodel.selected_object:
            return
        obj = self.viewmodel.selected_object
        self.on_selection_changed(obj)


class _ScriptProxy:
    component_type = "Script"
    type_name = "Script"

    def __init__(self, owner: GameObject) -> None:
        self.game_object = owner

    @property
    def script_path(self) -> str:
        return str(getattr(self.game_object, "script_path", ""))

    @script_path.setter
    def script_path(self, value: str) -> None:
        self.game_object.script_path = value
