from __future__ import annotations

from copy import deepcopy
from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMenu,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from editor.inspector import InspectorPluginRegistry, inspector_plugin_registry
from editor.premium_editor import InspectorPanel
from editor.premium_panel_base import Panel
from editor.runtime.command_manager import CommandManager, FunctionCommand
from editor.runtime.component_commands import AddComponentCommand, RemoveComponentCommand
from engine.core.component_registry import ComponentRegistry, component_registry


class RealInspectorPanel(InspectorPanel):
    def __init__(self) -> None:
        super().__init__()
        self.command_manager: CommandManager | None = None
        self.component_registry: ComponentRegistry = component_registry
        self.inspector_plugin_registry: InspectorPluginRegistry = inspector_plugin_registry
        self.current_object: Any | None = None
        self.component_clipboard: dict[str, Any] | None = None
        sections = [label for label in self.findChildren(QLabel) if label.objectName() == "InspectorSection"]
        for section in sections:
            section.setVisible(False)
        self.transform_label = QLabel("")
        self.transform_label.setObjectName("InspectorSection")
        self.transform_label.setVisible(False)
        self.renderer_label = QLabel("Components\n  Sem componentes")
        self.renderer_label.setObjectName("InspectorSection")
        self.renderer_label.setVisible(False)
        self.header = QWidget()
        self.header.setObjectName("InspectorObjectHeader")
        header_layout = QVBoxLayout(self.header)
        header_layout.setContentsMargins(6, 6, 6, 6)
        header_layout.setSpacing(5)
        title_row = QWidget()
        title_layout = QHBoxLayout(title_row)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(6)
        self.object_enabled = QCheckBox()
        self.object_enabled.setObjectName("InspectorCheckBox")
        self.object_name = QLineEdit()
        self.object_name.setObjectName("InspectorObjectName")
        self.object_static = QCheckBox("Estático")
        self.object_static.setObjectName("InspectorCheckBox")
        title_layout.addWidget(self.object_enabled)
        title_layout.addWidget(self.object_name, 1)
        title_layout.addWidget(self.object_static)
        meta_row = QWidget()
        meta_layout = QHBoxLayout(meta_row)
        meta_layout.setContentsMargins(0, 0, 0, 0)
        meta_layout.setSpacing(6)
        self.object_tag = QComboBox()
        self.object_tag.setObjectName("InspectorCombo")
        self.object_tag.setEditable(True)
        self.object_tag.setInsertPolicy(QComboBox.InsertAtBottom)
        self.object_tag.addItems(["Untagged", "Player", "Enemy", "Food", "Item", "Collectible", "+ Criar Nova Tag..."])
        self.object_tag.currentTextChanged.connect(self._on_tag_changed)
        self.object_layer = QComboBox()
        self.object_layer.setObjectName("InspectorCombo")
        self.object_layer.addItems(["Default", "UI", "World"])
        meta_layout.addWidget(QLabel("Tag"))
        meta_layout.addWidget(self.object_tag, 1)
        meta_layout.addWidget(QLabel("Layer"))
        meta_layout.addWidget(self.object_layer, 1)
        header_layout.addWidget(title_row)
        header_layout.addWidget(meta_row)
        self.component_filter = QLineEdit()
        self.component_filter.setObjectName("InspectorComponentFilter")
        self.component_filter.setPlaceholderText("Filtrar componentes...")
        self.component_filter.textChanged.connect(self.apply_component_filter)
        self.component_list = QWidget()
        self.component_list.setObjectName("InspectorComponentList")
        self.component_list_layout = QVBoxLayout(self.component_list)
        self.component_list_layout.setContentsMargins(4, 4, 4, 4)
        self.component_list_layout.setSpacing(6)
        self.status_label = QLabel("")
        self.status_label.setObjectName("InspectorStatus")
        self.add_component_button = QPushButton("Adicionar Componente")
        self.add_component_button.setObjectName("InspectorAddComponentButton")
        self.add_component_button.clicked.connect(self.open_add_component_menu)
        self.layout.insertWidget(max(0, self.layout.count() - 1), self.header)
        self.layout.insertWidget(max(0, self.layout.count() - 1), self.component_filter)
        self.layout.insertWidget(max(0, self.layout.count() - 1), self.component_list)
        self.layout.insertWidget(max(0, self.layout.count() - 1), self.status_label)
        self.layout.insertWidget(max(0, self.layout.count() - 1), self.add_component_button)

    def set_command_manager(self, command_manager: CommandManager) -> None:
        self.command_manager = command_manager

    def set_component_registry(self, registry: ComponentRegistry) -> None:
        self.component_registry = registry

    def set_inspector_plugin_registry(self, registry: InspectorPluginRegistry) -> None:
        self.inspector_plugin_registry = registry

    def load_objects(self, objects: list[Any]) -> None:
        """Carrega múltiplos objetos para edição em lote (Multi-Selection)."""
        self.current_objects = objects or []
        if len(self.current_objects) == 1:
            self.load_object(self.current_objects[0])
        elif len(self.current_objects) > 1:
            self.current_object = self.current_objects[0]
            self.header.setEnabled(True)
            self.object_name.setText(f"-- {len(self.current_objects)} Objetos Selecionados --")
            if hasattr(self, "name"):
                self.name.setText(f"{len(self.current_objects)} Objetos")
            self._render_component_controls(self.current_object)
        else:
            self.load_object(None)

    def load_object(self, obj: Any) -> None:
        self.current_object = obj
        self.current_objects = [obj] if obj is not None else []
        self.status_label.setText("")
        self.add_component_button.setEnabled(obj is not None)
        self.component_filter.setEnabled(obj is not None)

        if obj is None:
            self.header.setEnabled(False)
            self.object_name.setText("")
            if hasattr(self, "name"):
                self.name.setText("Nenhum objeto selecionado")
            self.component_filter.clear()
            self.renderer_label.setText("Components\n  Sem componentes")
            self.transform_label.setText("Transform\n  X: 0    Y: 0    Z: 0")
            self._clear_component_controls()
            return

        self._is_loading_object = True
        try:
            display_name = getattr(obj, "name", str(obj))
            self.header.setEnabled(True)
            self.object_name.setText(display_name)
            if hasattr(self, "name"):
                self.name.setText(display_name)
            self.object_enabled.setChecked(bool(getattr(obj, "active", True)))
            self.object_static.setChecked(bool(getattr(obj, "is_static", False)))

            current_tag = str(getattr(obj, "tag", "Untagged") if not isinstance(obj, dict) else obj.get("tag", "Untagged"))
            
            self.object_tag.blockSignals(True)
            if self.object_tag.findText(current_tag) == -1:
                self.object_tag.addItem(current_tag)
            self.object_tag.setCurrentText(current_tag)
            self.object_tag.blockSignals(False)

            current_layer = str(getattr(obj, "layer", "Default") if not isinstance(obj, dict) else obj.get("layer", "Default"))
            self.object_layer.blockSignals(True)
            if self.object_layer.findText(current_layer) == -1:
                self.object_layer.addItem(current_layer)
            self.object_layer.setCurrentText(current_layer)
            self.object_layer.blockSignals(False)
        finally:
            self._is_loading_object = False

        # --- FASE 8.1: Integração com PropertyBindingGroup & EventBus ---
        from editor.core.property_binding import PropertyBindingGroup
        self.binding_group = PropertyBindingGroup(obj, command_manager=self.command_manager)
        
        # Binding do Nome
        self.binding_group.bind(
            "name",
            label="Nome do Objeto",
            on_changed=lambda new_val: self._on_property_changed_notify("name", new_val)
        )
        # Binding do estado Ativo
        self.binding_group.bind(
            "active",
            label="Estado Ativo",
            on_changed=lambda new_val: self._on_property_changed_notify("active", new_val)
        )

        self._update_legacy_labels(obj, getattr(obj, "components", []))

        # --- RUNTIME INSPECTOR DUAL: Divisão limpa Persistente vs Runtime ---
        self._render_runtime_inspector_section(obj)
        self._render_component_controls(obj)

    def _render_runtime_inspector_section(self, obj: Any) -> None:
        """Renderiza a seção dividida de Dados de Runtime em Tempo Real no Inspector Dual."""
        runtime_group = QWidget()
        runtime_layout = QVBoxLayout(runtime_group)
        runtime_layout.setContentsMargins(4, 4, 4, 4)

        header_label = QLabel("⚡ DADOS DE RUNTIME (TEMPO REAL)")
        header_label.setStyleSheet("font-weight: bold; color: #ff8c69; font-size: 10px;")
        runtime_layout.addWidget(header_label)

        # Dados voláteis de execução
        state = getattr(obj, "state", "PLAYING / IDLE")
        vel = getattr(obj, "velocity", [0.0, 0.0])
        grounded = getattr(obj, "is_grounded", True)
        hp = getattr(obj, "health", 100.0)

        info_label = QLabel(
            f"  Velocidade: ({vel[0]:.1f}, {vel[1]:.1f}) | Grounded: {grounded}\n"
            f"  Estado de IA: {state} | Vida: {hp:.0f} HP\n"
            f"  Blackboard: [target = Player, alert_level = 0.0]"
        )
        info_label.setStyleSheet("color: #7ee787; font-family: Consolas; font-size: 10px;")
        runtime_layout.addWidget(info_label)

        self.component_list_layout.addWidget(runtime_group)

    def _on_tag_changed(self, new_tag: str) -> None:
        if getattr(self, "_is_loading_object", False) or not self.current_object:
            return
        tag_str = str(new_tag).strip()
        if tag_str == "+ Criar Nova Tag...":
            from PySide6.QtWidgets import QInputDialog
            custom_tag, ok = QInputDialog.getText(self, "Criar Nova Tag", "Digite o nome da nova Tag:")
            if ok and custom_tag.strip():
                tag_str = custom_tag.strip()
            else:
                curr = self.current_object.get("tag") if isinstance(self.current_object, dict) else getattr(self.current_object, "tag", "Untagged")
                self.object_tag.blockSignals(True)
                self.object_tag.setCurrentText(str(curr or "Untagged"))
                self.object_tag.blockSignals(False)
                return

        if not tag_str:
            tag_str = "Untagged"

        curr_tag = self.current_object.get("tag") if isinstance(self.current_object, dict) else getattr(self.current_object, "tag", None)
        if curr_tag == tag_str:
            return

        if self.object_tag.findText(tag_str) == -1:
            idx = max(0, self.object_tag.count() - 1)
            self.object_tag.insertItem(idx, tag_str)

        self.object_tag.blockSignals(True)
        self.object_tag.setCurrentText(tag_str)
        self.object_tag.blockSignals(False)

        if isinstance(self.current_object, dict):
            self.current_object["tag"] = tag_str
        else:
            setattr(self.current_object, "tag", tag_str)
        self._on_property_changed_notify("tag", tag_str)

    def _on_property_changed_notify(self, prop_name: str, new_val: Any) -> None:
        """Notifica alterações via EventBus no domínio Scene.*"""
        try:
            from editor.core.event_bus import EventBus, EVENT_OBJECT_MODIFIED
            EventBus.emit(EVENT_OBJECT_MODIFIED, object=self.current_object, property=prop_name, value=new_val)
        except Exception:
            pass

    def _update_legacy_labels(self, obj: Any, components: list[Any]) -> None:
        component_names = [self._component_type(comp) for comp in components if not getattr(comp, "required", False)]
        text = ", ".join(component_names) if component_names else "Sem componentes"
        self.renderer_label.setText("Components\n  " + text)

        # Usa obj.transform como fonte primária — o transform nativo do
        # GameObject vive em obj.transform, fora da lista de componentes.
        # Fallback para componente 'Transform' em components preservado
        # para compatibilidade com GameObjects que usam o modelo antigo.
        transform = getattr(obj, "transform", None)
        if transform is not None:
            pos = getattr(transform, "position", [0, 0, 0])
            rot = getattr(transform, "rotation", [0, 0, 0])
            scale = getattr(transform, "scale", [1, 1, 1])
            self.transform_label.setText(
                "Transform\n"
                f"  Position: X {float(pos[0]):.1f} | Y {float(pos[1]):.1f} | Z {float(pos[2]) if len(pos) > 2 else 0:.1f}\n"
                f"  Rotation: {list(rot)}\n"
                f"  Scale: {list(scale)}"
            )
            return

        # Fallback: procura componente Transform na lista de componentes
        for component in components:
            if self._component_type(component) != "Transform":
                continue
            pos = getattr(component, "position", [0, 0, 0])
            rot = getattr(component, "rotation", [0, 0, 0])
            scale = getattr(component, "scale", [1, 1, 1])
            self.transform_label.setText(
                "Transform\n"
                f"  Position: X {float(pos[0]):.1f} | Y {float(pos[1]):.1f} | Z {float(pos[2]) if len(pos) > 2 else 0:.1f}\n"
                f"  Rotation: {list(rot)}\n"
                f"  Scale: {list(scale)}"
            )
            return

    def _clear_component_controls(self) -> None:
        while self.component_list_layout.count():
            item = self.component_list_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def _render_component_controls(self, obj: Any) -> None:
        self._clear_component_controls()
        for component in getattr(obj, "components", []):
            if not self._component_matches_filter(component):
                continue
            plugin = self.inspector_plugin_registry.plugin_for(component)
            if plugin is None:
                widget = QLabel(self._component_type(component))
                widget.setObjectName("InspectorSection")
            else:
                widget = plugin.create_widget(component, self.command_manager, lambda obj=obj: self.load_object(obj))
            widget.setContextMenuPolicy(Qt.CustomContextMenu)
            widget.customContextMenuRequested.connect(
                lambda pos, comp=component, w=widget: self.open_component_context_menu(comp, w.mapToGlobal(pos))
            )
            # Connect the 3-dots button if the widget is a FoldoutWidget
            if hasattr(widget, "options_btn"):
                widget.options_btn.clicked.connect(
                    lambda checked=False, comp=component, w=widget: self.open_component_context_menu(
                        comp, w.options_btn.mapToGlobal(w.options_btn.rect().bottomLeft())
                    )
                )
            self.component_list_layout.addWidget(widget)

    def _component_type(self, component: Any) -> str:
        return str(getattr(component, "type_name", type(component).__name__))

    def _component_matches_filter(self, component: Any) -> bool:
        query = self.component_filter.text().strip().lower()
        return True if not query else query in self._component_type(component).lower()

    def apply_component_filter(self, _text: str = "") -> None:
        if self.current_object is not None:
            self._render_component_controls(self.current_object)

    def open_component_context_menu(self, component: Any, global_pos) -> None:
        menu = QMenu(self)
        reset = menu.addAction("Reset")
        copy = menu.addAction("Copy")
        paste = menu.addAction("Paste Values")
        remove = menu.addAction("Remove")
        menu.addSeparator()
        move_up = menu.addAction("Move Up")
        move_down = menu.addAction("Move Down")
        paste.setEnabled(self.can_paste_component_values(component))
        remove.setEnabled(not getattr(component, "required", False))
        action = menu.exec(global_pos)
        if action is reset:
            self.reset_component(component)
        elif action is copy:
            self.copy_component(component)
        elif action is paste:
            self.paste_component_values(component)
        elif action is remove:
            self.remove_component_from_selected(component)
        elif action is move_up:
            self.move_component_visual(component, -1)
        elif action is move_down:
            self.move_component_visual(component, 1)

    def copy_component(self, component: Any) -> dict[str, Any] | None:
        if not hasattr(component, "serialize"):
            return None
        self.component_clipboard = deepcopy(component.serialize())
        return self.component_clipboard

    def can_paste_component_values(self, component: Any) -> bool:
        return self.component_clipboard is not None and self.component_clipboard.get("type") == self._component_type(component)

    def paste_component_values(self, component: Any) -> bool:
        if not self.can_paste_component_values(component):
            return False
        before = deepcopy(component.serialize())
        after = deepcopy(self.component_clipboard)
        after["id"] = getattr(component, "id", after.get("id"))
        self._execute_component_ux_command(
            f"Paste {self._component_type(component)} Values",
            lambda: self._apply_component_snapshot_and_reload(component, after),
            lambda: self._apply_component_snapshot_and_reload(component, before),
        )
        return True

    def reset_component(self, component: Any) -> bool:
        component_class = self.component_registry.resolve(self._component_type(component)) or type(component)
        try:
            default_component = component_class()
        except Exception:
            return False
        before = deepcopy(component.serialize())
        after = deepcopy(default_component.serialize())
        after["id"] = getattr(component, "id", after.get("id"))
        self._execute_component_ux_command(
            f"Reset {self._component_type(component)}",
            lambda: self._apply_component_snapshot_and_reload(component, after),
            lambda: self._apply_component_snapshot_and_reload(component, before),
        )
        return True

    def move_component_visual(self, component: Any, offset: int) -> bool:
        if self.current_object is None or component not in getattr(self.current_object, "components", []):
            return False
        components = self.current_object.components
        old_index = components.index(component)
        new_index = max(0, min(len(components) - 1, old_index + offset))
        if old_index == new_index:
            return False

        def move(src: int, dst: int) -> None:
            item = components.pop(src)
            components.insert(dst, item)
            self.load_object(self.current_object)

        self._execute_component_ux_command(
            f"Move {self._component_type(component)}",
            lambda: move(old_index, new_index),
            lambda: move(new_index, old_index),
        )
        return True

    def _apply_component_snapshot_and_reload(self, component: Any, data: dict[str, Any]) -> None:
        if hasattr(component, "deserialize"):
            component.deserialize(deepcopy(data))
        else:
            if "enabled" in data:
                component.enabled = bool(data.get("enabled", True))
            if data.get("id"):
                component.id = str(data["id"])
            properties = data.get("properties", {})
            if isinstance(properties, dict) and hasattr(component, "deserialize_properties"):
                component.deserialize_properties(deepcopy(properties))
        if getattr(component, "game_object", None) is not None:
            self.load_object(component.game_object)

    def _execute_component_ux_command(self, description: str, apply, undo) -> None:
        if self.command_manager is None:
            apply()
            return
        self.command_manager.execute(FunctionCommand(description, apply, undo))

    def available_component_names(self, include_unavailable: bool = False) -> list[str]:
        if self.current_object is None:
            return []
        names: list[str] = []
        for component_type in self.component_registry.available_components():
            name = str(getattr(component_type, "component_type", component_type.__name__))
            if name == "Component" or getattr(component_type, "required", False):
                continue
            if not include_unavailable and not self.can_add_component(name):
                continue
            names.append(name)
        return names

    def can_add_component(self, component_type: str) -> bool:
        if self.current_object is None:
            return False
        component_class = self.component_registry.resolve(component_type)
        if component_class is None:
            return False
        if str(getattr(component_class, "component_type", component_class.__name__)) == "Component" or getattr(component_class, "required", False):
            return False
        if getattr(component_class, "UNIQUE", False):
            return self.current_object.get_component(component_class) is None
        return True

    def open_add_component_menu(self) -> None:
        if self.current_object is None:
            return
        menu = QMenu(self)
        available = self.available_component_names()
        if not available:
            action = menu.addAction("Nenhum componente disponivel")
            action.setEnabled(False)
        for name in available:
            menu.addAction(name, lambda checked=False, value=name: self.add_component_to_selected(value))
        menu.exec(self.add_component_button.mapToGlobal(self.add_component_button.rect().bottomLeft()))

    def add_component_to_selected(self, component_type: str) -> Any:
        if self.current_object is None:
            return None
        command = AddComponentCommand(self.current_object, component_type, self.component_registry)
        if self.command_manager is None:
            command.execute()
        else:
            self.command_manager.execute(command)
        self.load_object(self.current_object)
        return command.component

    def remove_component_from_selected(self, component: Any) -> bool:
        if self.current_object is None:
            self.status_label.setText("Nenhum objeto selecionado.")
            return False
        if component is getattr(self.current_object, "transform", None) or getattr(component, "required", False):
            self.status_label.setText("Transform nao pode ser removido.")
            return False
        command = RemoveComponentCommand(self.current_object, component)
        if self.command_manager is None:
            command.execute()
        else:
            self.command_manager.execute(command)
        self.load_object(self.current_object)
        return True

    def set_component_property(self, component: Any, property_name: str, value: Any) -> None:
        plugin = self.inspector_plugin_registry.plugin_for(component)
        if plugin is not None:
            plugin.set_property(component, property_name, value, self.command_manager, lambda: self.load_object(component.game_object) if getattr(component, "game_object", None) is not None else None)
            return
        old_value = getattr(component, property_name)
        self._execute_component_ux_command(
            f"Set {self._component_type(component)}.{property_name}",
            lambda: setattr(component, property_name, value),
            lambda: setattr(component, property_name, old_value),
        )
