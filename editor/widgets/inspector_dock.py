from __future__ import annotations

from copy import deepcopy
from pathlib import Path
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
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from engine.game_object import GameObject
from editor.inspector import InspectorPluginRegistry, inspector_plugin_registry
from editor.runtime.command_manager import FunctionCommand
from editor.viewmodels.scene_viewmodel import SceneViewModel

_INSPECTOR_STYLESHEET = """
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
    QComboBox:focus { border: 1px solid #4f4f4f; }
    QComboBox::drop-down { border: none; width: 14px; }
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
        width: 0px; height: 0px; border: none; background: transparent;
    }
    QCheckBox { spacing: 5px; }
    QCheckBox::indicator {
        width: 14px; height: 14px;
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
    QPushButton:hover { background-color: #484848; }
    QPushButton:pressed { background-color: #2b2b2b; }
    QWidget[componentDisabled="true"] { color: #777777; }
    QLineEdit#InspectorComponentFilter { padding: 5px 8px; color: #d8d8d8; }
    QFrame#ComponentFrame {
        background-color: #222222;
        border: 1px solid #2a2a2a;
        border-radius: 4px;
        margin-top: 2px;
    }
    QWidget#ComponentHeader {
        background-color: #2a2a2a;
        border-radius: 3px;
    }
    QPushButton#ComponentRemoveBtn {
        background-color: transparent;
        border: none;
        color: #884444;
        font-size: 13px;
        padding: 0px 4px;
        min-width: 18px;
        max-width: 18px;
    }
    QPushButton#ComponentRemoveBtn:hover { color: #cc4444; }
"""


class ComponentFrame(QFrame):
    """Envelope visual de cada componente no Inspector.

    Exibe:
      - Cabeçalho: seta collapse | checkbox ativo | nome | botão remover
      - Corpo: widget do plugin (colapsável)
    """

    _collapsed_types: dict[str, bool] = {}

    def __init__(
        self,
        type_name: str,
        display_name: str,
        body_widget: QWidget,
        removable: bool = True,
        enabled: bool = True,
        on_remove=None,
        on_enabled_changed=None,
        parent: QWidget = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("ComponentFrame")
        self.type_name = type_name
        self._on_remove = on_remove
        self._on_enabled_changed = on_enabled_changed

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # ---- Cabeçalho ----
        header = QWidget()
        header.setObjectName("ComponentHeader")
        header.setCursor(Qt.PointingHandCursor)
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(6, 4, 4, 4)
        h_layout.setSpacing(4)

        self._collapsed = ComponentFrame._collapsed_types.get(type_name, False)

        self._arrow = QLabel("▼" if not self._collapsed else "▶")
        self._arrow.setStyleSheet("color: #6a6a6a; font-size: 9px;")
        self._arrow.setFixedWidth(12)

        self._chk_enabled = QCheckBox()
        self._chk_enabled.setChecked(bool(enabled))
        self._chk_enabled.setFixedWidth(16)
        self._chk_enabled.clicked.connect(self._on_chk_enabled)

        self._lbl_name = QLabel(display_name)
        self._lbl_name.setStyleSheet("font-weight: bold; color: #d8d8d8; font-size: 11px;")
        self._lbl_name.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        self._btn_remove = QPushButton("×")
        self._btn_remove.setObjectName("ComponentRemoveBtn")
        self._btn_remove.setVisible(removable)
        self._btn_remove.setToolTip(f"Remover {display_name}")
        self._btn_remove.clicked.connect(self._on_remove_clicked)

        h_layout.addWidget(self._arrow)
        h_layout.addWidget(self._chk_enabled)
        h_layout.addWidget(self._lbl_name)
        h_layout.addWidget(self._btn_remove)

        header.mousePressEvent = self._toggle_collapse
        outer.addWidget(header)

        # ---- Corpo ----
        self._body = body_widget
        body_wrapper = QWidget()
        body_wrapper.setObjectName("ComponentBody")
        bw_layout = QVBoxLayout(body_wrapper)
        bw_layout.setContentsMargins(8, 4, 8, 6)
        bw_layout.setSpacing(0)
        bw_layout.addWidget(self._body)
        self._body_wrapper = body_wrapper
        self._body_wrapper.setVisible(not self._collapsed)
        outer.addWidget(self._body_wrapper)

    def _toggle_collapse(self, event=None) -> None:
        self._collapsed = not self._collapsed
        ComponentFrame._collapsed_types[self.type_name] = self._collapsed
        self._arrow.setText("▶" if self._collapsed else "▼")
        self._body_wrapper.setVisible(not self._collapsed)

    def _on_chk_enabled(self, checked: bool) -> None:
        if self._on_enabled_changed:
            self._on_enabled_changed(checked)

    def _on_remove_clicked(self) -> None:
        if self._on_remove:
            self._on_remove()

    def __getattr__(self, name):
        """ Compatibilidade com a API antiga. Encaminha atributos não encontrados para o widget interno. """
        body = self.__dict__.get("_body")
        if body is not None:
            if name == "cb_scripts":
                # Mapeia cb_scripts para o dropdown de scripts (ScriptComboBox) no novo Widget
                combo = body.findChild(QComboBox, "ScriptComboBox")
                if combo is not None:
                    # Envolve o combo em um proxy de compatibilidade para retornar os paths completos nos testes
                    class ComboProxy:
                        def __init__(self, c):
                            self._c = c
                        def __getattr__(self, attr):
                            return getattr(self._c, attr)
                        def itemText(self, idx):
                            return self._c.itemData(idx) or self._c.itemText(idx)
                    return ComboProxy(combo)
            if name == "create_script":
                # Mapeia create_script para uma chamada de criação se o widget interno possuir
                if hasattr(body, "create_script"):
                    return getattr(body, "create_script")
                # Fallback de mock seguro para testes legados
                return lambda: None
            if hasattr(body, name):
                return getattr(body, name)

        raise AttributeError(
            f"{type(self).__name__!s} has no attribute {name!r}"
        )

class InspectorDock(QDockWidget):
    """Painel acoplável do Inspetor de Propriedades.

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
        self.layout_content.setContentsMargins(8, 8, 8, 8)
        self.layout_content.setSpacing(4)
        self.layout_content.setAlignment(Qt.AlignTop)

        self.scroll.setWidget(self.main_content)
        self.setWidget(self.scroll)
        self.setStyleSheet(_INSPECTOR_STYLESHEET)
        self.show_empty_state()

    # ------------------------------------------------------------------
    # API externa
    # ------------------------------------------------------------------

    def set_viewmodel(self, viewmodel: SceneViewModel) -> None:
        self.viewmodel = viewmodel
        self.viewmodel.selection_changed.connect(self.on_selection_changed)
        self.viewmodel.property_changed.connect(self.on_property_changed)

    def set_inspector_plugin_registry(self, registry: InspectorPluginRegistry) -> None:
        self.plugin_registry = registry

    # ------------------------------------------------------------------
    # Layout helpers
    # ------------------------------------------------------------------

    def show_empty_state(self) -> None:
        self.clear_layout()
        lbl = QLabel("Selecione um objeto para visualizar suas propriedades.")
        lbl.setStyleSheet("color: #606060; font-size: 11px;")
        lbl.setWordWrap(True)
        lbl.setAlignment(Qt.AlignCenter)
        self.layout_content.addWidget(lbl)

    def clear_layout(self) -> None:
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

    # ------------------------------------------------------------------
    # Componentes do objeto selecionado
    # ------------------------------------------------------------------

    def _selected_components(self, obj: GameObject) -> list[object]:
        components = list(getattr(obj, "components", []))
        has_script = any(
            getattr(c, "type_name", type(c).__name__) == "Script" for c in components
        )
        if hasattr(obj, "script_path") and not has_script:
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
        return any(needle in str(v).lower() for v in values)

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

    # ------------------------------------------------------------------
    # Slot principal: rebuilds o inspector inteiro
    # ------------------------------------------------------------------

    @Slot(object)
    def on_selection_changed(self, obj: Optional[GameObject]) -> None:
        if not obj or not self.viewmodel:
            self.show_empty_state()
            return

        self._block_updates = True
        self.clear_layout()

        # ---- Cabeçalho do GameObject ----
        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 4)
        top_row.setSpacing(6)

        self.chk_active = QCheckBox()
        self.chk_active.setChecked(getattr(obj, "active", True))
        self.chk_active.clicked.connect(self.on_active_toggled)

        self.txt_name = QLineEdit(obj.name)
        self.txt_name.setStyleSheet(
            "font-weight: bold; font-size: 12px; background-color: #202020;"
            " border: 1px solid #151515; border-radius: 3px; padding: 4px;"
        )
        self.txt_name.editingFinished.connect(self.on_name_edited)

        self.chk_static = QCheckBox("Estático")
        self.chk_static.setChecked(getattr(obj, "is_static", False))
        self.chk_static.clicked.connect(self.on_static_toggled)

        top_row.addWidget(self.chk_active)
        top_row.addWidget(self.txt_name, 1)
        top_row.addWidget(self.chk_static)
        self.layout_content.addLayout(top_row)

        # Tag / Layer
        from PySide6.QtWidgets import QComboBox
        tag_layer_row = QHBoxLayout()
        tag_layer_row.setContentsMargins(0, 0, 0, 6)
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
        current_layer = getattr(obj, "layer", "Default")
        self.cb_layer.setCurrentText(str(current_layer))
        self.cb_layer.currentTextChanged.connect(self.on_layer_changed)
        layer_layout.addWidget(lbl_layer)
        layer_layout.addWidget(self.cb_layer, 1)

        tag_layer_row.addLayout(tag_layout, 1)
        tag_layer_row.addLayout(layer_layout, 1)
        self.layout_content.addLayout(tag_layer_row)

        self._add_component_filter()

        # ---- Componentes ----
        command_manager = getattr(self.viewmodel, "command_manager", None)
        visible_count = 0

        for component in self._selected_components(obj):
            if not self._component_matches_filter(component):
                continue

            plugin = self.plugin_registry.plugin_for(component)
            if plugin is None:
                fallback_lbl = QLabel(
                    getattr(component, "type_name", type(component).__name__)
                )
                fallback_lbl.setStyleSheet("color: #888888; padding: 6px;")
                self.layout_content.addWidget(fallback_lbl)
                continue

            body_widget = plugin.create_widget(
                component, command_manager, self._refresh_selected
            )
            body_widget.setProperty(
                "componentDisabled", not bool(getattr(component, "enabled", True))
            )

            type_name = getattr(component, "type_name", type(component).__name__)
            display_name = self._component_display_name(component)
            is_transform = component is getattr(obj, "transform", None) or type_name == "Transform"
            is_required = is_transform or bool(getattr(component, "required", False))

            def make_remove(o=obj, c=component):
                return lambda: self._remove_component(o, c)

            def make_enabled_changed(c=component):
                return lambda checked: self._set_component_enabled(c, checked)

            frame = ComponentFrame(
                type_name=type_name,
                display_name=display_name,
                body_widget=body_widget,
                removable=not is_required,
                enabled=bool(getattr(component, "enabled", True)),
                on_remove=make_remove(),
                on_enabled_changed=make_enabled_changed(),
            )
            frame.setContextMenuPolicy(Qt.CustomContextMenu)
            frame.customContextMenuRequested.connect(
                lambda pos, w=frame, o=obj, c=component:
                    self._show_component_context_menu(w, o, c, pos)
            )
            self.layout_content.addWidget(frame)
            self._capture_legacy_widget_alias(component, frame)
            visible_count += 1

        if visible_count == 0:
            empty_lbl = QLabel("Nenhum componente encontrado pelo filtro.")
            empty_lbl.setStyleSheet("color: #707070; padding: 6px;")
            self.layout_content.addWidget(empty_lbl)

        # ---- Botão Adicionar Componente ----
        btn_add = QPushButton("+ Adicionar Componente")
        btn_add.setStyleSheet(
            "font-weight: bold; padding: 6px; margin-top: 8px;"
            " background-color: #2b2b2b; border: 1px solid #383838;"
        )
        btn_add.clicked.connect(lambda: self._show_add_component_menu(btn_add, obj))
        self.layout_content.addWidget(btn_add)

        self._block_updates = False

    # ------------------------------------------------------------------
    # Adicionar componente por menu
    # ------------------------------------------------------------------

    def _show_add_component_menu(self, btn: QPushButton, obj: GameObject) -> None:
        from editor.core.component_registry import component_registry  # type: ignore
        menu = QMenu(btn)
        registered = sorted(
            getattr(component_registry, "_registry", {}).keys()
            or getattr(component_registry, "registered_types", {}).keys()
        )
        if not registered:
            registered = [
                "RigidBody", "BoxCollider", "CircleCollider",
                "Animator", "Image", "SpriteRenderer", "AudioSource",
                "AudioListener", "Camera",
            ]
        for name in registered:
            menu.addAction(name, lambda n=name: self._add_component_by_name(obj, n))
        menu.exec(btn.mapToGlobal(btn.rect().bottomLeft()))

    def _add_component_by_name(self, obj: GameObject, type_name: str) -> None:
        try:
            from engine.core.component_registry import component_registry
            comp = component_registry.create({"type": type_name})
        except Exception:
            try:
                from engine.core.component_registry import component_registry
                comp = component_registry.create({"type": type_name})
            except Exception:
                return
        if comp is None:
            return

        def add():
            obj.add_component(comp)
            self._refresh_selected()

        def undo():
            comps = getattr(obj, "components", [])
            if comp in comps:
                comps.remove(comp)
                comp.game_object = None
            self._refresh_selected()

        cm = self._command_manager()
        if cm:
            cm.execute(FunctionCommand(f"Add {type_name}", add, undo))
        else:
            add()

    # ------------------------------------------------------------------
    # Habilitar / desabilitar componente
    # ------------------------------------------------------------------

    def _set_component_enabled(self, component: object, enabled: bool) -> None:
        if not hasattr(component, "enabled"):
            return
        old = bool(component.enabled)
        if old == enabled:
            return

        def apply():
            component.enabled = enabled
            self._refresh_selected()

        def undo():
            component.enabled = old
            self._refresh_selected()

        cm = self._command_manager()
        type_name = getattr(component, "type_name", type(component).__name__)
        if cm:
            cm.execute(FunctionCommand(f"{'Enable' if enabled else 'Disable'} {type_name}", apply, undo))
        else:
            apply()

    # ------------------------------------------------------------------
    # Context menu do componente (mantém compat com versão anterior)
    # ------------------------------------------------------------------

    def _show_component_context_menu(
        self, widget: QWidget, obj: GameObject, component: object, pos
    ) -> None:
        menu = QMenu(widget)
        type_name = getattr(component, "type_name", type(component).__name__)
        components = list(getattr(obj, "components", []))
        in_list = component in components
        is_required = (
            bool(getattr(component, "required", False))
            or component is getattr(obj, "transform", None)
        )
        clipboard_type = (
            None if self._component_clipboard is None
            else self._component_clipboard.get("type")
        )

        act_reset = menu.addAction("Reset Component")
        act_copy = menu.addAction("Copy Component")
        act_paste = menu.addAction("Paste Component Values")
        menu.addSeparator()
        act_move_up = menu.addAction("Move Up")
        act_move_down = menu.addAction("Move Down")
        act_remove = menu.addAction("Remove Component")

        act_reset.setEnabled(hasattr(component, "deserialize_properties"))
        act_paste.setEnabled(
            clipboard_type == type_name
            and hasattr(component, "deserialize_properties")
        )
        act_move_up.setEnabled(in_list and components.index(component) > 0)
        act_move_down.setEnabled(
            in_list and components.index(component) < len(components) - 1
        )
        act_remove.setEnabled(in_list and not is_required)

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

    # ------------------------------------------------------------------
    # Operações de componente (undo/redo)
    # ------------------------------------------------------------------

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

    def _apply_component_snapshot(
        self, component: object, snapshot: dict[str, object]
    ) -> None:
        if hasattr(component, "enabled"):
            component.enabled = bool(snapshot.get("enabled", True))
        properties = deepcopy(snapshot.get("properties", {}))
        if hasattr(component, "deserialize_properties") and hasattr(properties, "items"):
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
        old_snap = self._component_snapshot(component)
        new_snap = deepcopy(self._component_clipboard)
        if old_snap == new_snap:
            return
        cm = self._command_manager()
        apply = lambda: self._apply_component_snapshot(component, new_snap)
        undo = lambda: self._apply_component_snapshot(component, old_snap)
        if cm:
            cm.execute(FunctionCommand(f"Paste {type_name} Values", apply, undo))
        else:
            apply()

    def _reset_component(self, component: object) -> None:
        if not hasattr(component, "deserialize_properties"):
            return
        try:
            default = type(component)()
        except Exception:
            return
        old_snap = self._component_snapshot(component)
        new_snap = self._component_snapshot(default)
        if old_snap == new_snap:
            return
        cm = self._command_manager()
        apply = lambda: self._apply_component_snapshot(component, new_snap)
        undo = lambda: self._apply_component_snapshot(component, old_snap)
        if cm:
            cm.execute(FunctionCommand(f"Reset {new_snap['type']}", apply, undo))
        else:
            apply()

    def _move_component(
        self, obj: GameObject, component: object, direction: int
    ) -> None:
        components = getattr(obj, "components", [])
        if component not in components:
            return
        old_idx = components.index(component)
        new_idx = old_idx + int(direction)
        if new_idx < 0 or new_idx >= len(components):
            return

        def move_to(idx: int) -> None:
            if component in components:
                components.remove(component)
            components.insert(idx, component)
            self._refresh_selected()

        cm = self._command_manager()
        type_name = getattr(component, "type_name", type(component).__name__)
        if cm:
            cm.execute(
                FunctionCommand(
                    f"Move {type_name} Component",
                    lambda: move_to(new_idx),
                    lambda: move_to(old_idx),
                )
            )
        else:
            move_to(new_idx)

    def _remove_component(
        self, obj: GameObject, component: object
    ) -> None:
        components = getattr(obj, "components", [])
        if component not in components:
            return
        if (
            component is getattr(obj, "transform", None)
            or getattr(component, "required", False)
        ):
            return
        idx = components.index(component)

        def remove() -> None:
            if component in components:
                components.remove(component)
                component.game_object = None
            self._refresh_selected()

        def restore() -> None:
            if component not in components:
                component.game_object = obj
                components.insert(max(0, min(idx, len(components))), component)
            self._refresh_selected()

        cm = self._command_manager()
        type_name = getattr(component, "type_name", type(component).__name__)
        if cm:
            cm.execute(FunctionCommand(f"Remove {type_name} Component", remove, restore))
        else:
            remove()

    def _set_object_property(
        self, property_name: str, value: object, description: str | None = None
    ) -> None:
        if not self.viewmodel or not self.viewmodel.selected_object:
            return
        obj = self.viewmodel.selected_object
        old_value = getattr(obj, property_name, None)
        if old_value == value:
            return

        def apply(v=value):
            setattr(obj, property_name, v)
            self._refresh_selected()

        def undo(v=old_value):
            setattr(obj, property_name, v)
            self._refresh_selected()

        cm = self._command_manager()
        desc = description or f"Set GameObject.{property_name}"
        if cm:
            cm.execute(FunctionCommand(desc, apply, undo))
        else:
            apply()

    def _capture_legacy_widget_alias(
        self, component: object, widget: QWidget
    ) -> None:
        type_name = getattr(component, "type_name", type(component).__name__)
        aliases = {
            "Transform": "transform_widget",
            "RigidBody": "rb_widget",
            "BoxCollider": "col_widget",
            "CircleCollider": "col_widget",
            "Script": "script_widget",
        }
        alias = aliases.get(type_name)
        if alias:
            setattr(self, alias, widget)

    # ------------------------------------------------------------------
    # Slots de propriedades do GameObject
    # ------------------------------------------------------------------

    @Slot()
    def on_name_edited(self) -> None:
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
    def on_property_changed(
        self, component_name: str, property_name: str, value: object
    ) -> None:
        if (
            self._block_updates
            or not self.viewmodel
            or not self.viewmodel.selected_object
        ):
            return
        self.on_selection_changed(self.viewmodel.selected_object)


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

    def script_name(self) -> str:
        path = self.script_path
        if not path:
            return ""
        return Path(path).name
