from PySide6.QtWidgets import (
    QDockWidget, QWidget, QVBoxLayout, QLabel, QScrollArea,
    QLineEdit, QHBoxLayout, QFrame, QCheckBox, QComboBox, QPushButton
)
from typing import Optional
from PySide6.QtCore import Qt, Slot
from engine.game_object import GameObject
from editor.viewmodels.scene_viewmodel import SceneViewModel
from editor.inspector import InspectorPluginRegistry, inspector_plugin_registry


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
        
        # 1. ScrollArea para rolar verticalmente quando houver muitos componentes
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        
        # Conteúdo interno principal
        self.main_content = QWidget()
        self.main_content.setObjectName("main_content")
        self.layout_content = QVBoxLayout(self.main_content)
        self.layout_content.setContentsMargins(10, 10, 10, 10)
        self.layout_content.setSpacing(10)
        self.layout_content.setAlignment(Qt.AlignTop)
        
        self.scroll.setWidget(self.main_content)
        self.setWidget(self.scroll)
        
        # Aplicar estilo unificado premium escuro (tipo Unity/Godot)
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
        """)
        
        # Widget padrão para exibição sem objeto selecionado
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
                # Limpa layouts recursivamente
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

    @Slot(object)
    def on_selection_changed(self, obj: Optional[GameObject]) -> None:
        """Reconstrói dinamicamente os widgets quando o objeto selecionado muda."""
        if not obj or not self.viewmodel:
            self.show_empty_state()
            return
            
        self._block_updates = True
        self.clear_layout()
        
        # ── Cabeçalho do Objeto (Ativo, Nome e Estático) ────────────────
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
        
        # ── Tag & Layer ────────────────
        tag_layer_row = QHBoxLayout()
        tag_layer_row.setContentsMargins(0, 0, 0, 8)
        tag_layer_row.setSpacing(8)
        
        # Tag
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
        
        # Layer
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
        
        command_manager = getattr(self.viewmodel, "command_manager", None)
        for component in self._selected_components(obj):
            plugin = self.plugin_registry.plugin_for(component)
            if plugin is None:
                fallback = QLabel(getattr(component, "type_name", type(component).__name__))
                fallback.setStyleSheet("color: #888888; padding: 6px;")
                self.layout_content.addWidget(fallback)
                continue
            widget = plugin.create_widget(
                component,
                command_manager,
                None,
            )
            self.layout_content.addWidget(widget)
            self._capture_legacy_widget_alias(component, widget)
        
        # ── Botão Adicionar Componente ───────────────────
        btn_add = QPushButton("Adicionar Componente")
        btn_add.setStyleSheet("font-weight: bold; padding: 6px; margin-top: 8px;")
        self.layout_content.addWidget(btn_add)
            
        self._block_updates = False

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
        new_name = self.txt_name.text()
        self.viewmodel.rename_object(self.viewmodel.selected_object, new_name)

    @Slot(bool)
    def on_active_toggled(self, checked: bool) -> None:
        if not self.viewmodel or not self.viewmodel.selected_object:
            return
        self.viewmodel.selected_object.active = checked

    @Slot(bool)
    def on_static_toggled(self, checked: bool) -> None:
        if not self.viewmodel or not self.viewmodel.selected_object:
            return
        self.viewmodel.selected_object.is_static = checked

    @Slot(str)
    def on_tag_changed(self, text: str) -> None:
        if not self.viewmodel or not self.viewmodel.selected_object:
            return
        self.viewmodel.selected_object.tag = text

    @Slot(str)
    def on_layer_changed(self, text: str) -> None:
        if not self.viewmodel or not self.viewmodel.selected_object:
            return
        self.viewmodel.selected_object.layer = text

    @Slot(str, str, object)
    def on_property_changed(self, component_name: str, property_name: str, value: object) -> None:
        """Chamado quando uma propriedade é alterada externamente (ex: sincroniza visual)."""
        if self._block_updates or not self.viewmodel or not self.viewmodel.selected_object:
            return
            
        # Atualiza a interface apenas se as propriedades mudarem fora do foco do spinbox
        # (ex: a escala mudou de forma indireta ao mudar o tamanho do colisor ou vice-versa)
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

