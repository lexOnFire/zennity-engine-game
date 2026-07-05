from PySide6.QtWidgets import (
    QDockWidget, QWidget, QVBoxLayout, QLabel, QScrollArea,
    QLineEdit, QHBoxLayout, QFrame
)
from typing import Optional
from PySide6.QtCore import Qt, Slot
from engine.game_object import GameObject
from editor.viewmodels.scene_viewmodel import SceneViewModel

# Importa os Widgets de Componentes
from editor.widgets.collapsible_section import CollapsibleSection
from editor.widgets.component_widgets import (
    TransformComponentWidget, RigidBodyComponentWidget, ColliderComponentWidget,
    ScriptComponentWidget
)


class InspectorDock(QDockWidget):
    """
    Painel acoplável do Inspetor de Propriedades (Inspector).
    Componente 'View' na arquitetura MVVM do editor.
    """
    
    def __init__(self, parent: QWidget = None) -> None:
        super().__init__("Inspector", parent)
        self.setObjectName("InspectorDock")
        self.setAllowedAreas(Qt.RightDockWidgetArea | Qt.LeftDockWidgetArea)
        
        self.viewmodel: Optional[SceneViewModel] = None
        self._block_updates = False
        
        # 1. ScrollArea para rolar verticalmente quando houver muitos componentes
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        
        # Conteúdo interno principal
        self.main_content = QWidget()
        self.layout_content = QVBoxLayout(self.main_content)
        self.layout_content.setContentsMargins(10, 10, 10, 10)
        self.layout_content.setSpacing(12)
        self.layout_content.setAlignment(Qt.AlignTop)
        
        self.scroll.setWidget(self.main_content)
        self.setWidget(self.scroll)
        
        # Widget padrão para exibição sem objeto selecionado
        self.show_empty_state()

    def set_viewmodel(self, viewmodel: SceneViewModel) -> None:
        """Conecta o Inspector ao ViewModel da cena."""
        self.viewmodel = viewmodel
        self.viewmodel.selection_changed.connect(self.on_selection_changed)
        self.viewmodel.property_changed.connect(self.on_property_changed)

    def show_empty_state(self) -> None:
        """Exibe tela vazia padrão."""
        self.clear_layout()
        lbl = QLabel("Selecione um objeto para visualizar suas propriedades.")
        lbl.setStyleSheet("color: #484e5f;")
        lbl.setWordWrap(True)
        lbl.setAlignment(Qt.AlignCenter)
        self.layout_content.addWidget(lbl)

    def clear_layout(self) -> None:
        """Remove todos os widgets da área de exibição."""
        while self.layout_content.count():
            item = self.layout_content.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    @Slot(object)
    def on_selection_changed(self, obj: Optional[GameObject]) -> None:
        """Recontrói dinamicamente os widgets quando o objeto selecionado muda."""
        if not obj or not self.viewmodel:
            self.show_empty_state()
            return
            
        self._block_updates = True
        self.clear_layout()
        
        # ── Cabeçalho do Objeto (Nome e Tag) ────────────────
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 6)
        
        self.txt_name = QLineEdit(obj.name)
        self.txt_name.setStyleSheet(
            "font-weight: 600; font-size: 16px; color: #5db0ff; background: #111217; border: 1px solid #2d313f; border-radius: 6px; padding: 4px 8px;"
        )
        self.txt_name.editingFinished.connect(self.on_name_edited)
        
        lbl_type = QLabel(f" ({obj.mesh_type or 'GameObject'})")
        lbl_type.setStyleSheet("color: #828a9b; font-size: 11px;")
        
        header_layout.addWidget(self.txt_name)
        header_layout.addWidget(lbl_type)
        self.layout_content.addWidget(header_widget)
        
        # ── 1. Componente: Transform ────────────────────────
        sec_transform = CollapsibleSection("Transform")
        self.transform_widget = TransformComponentWidget(self.viewmodel)
        sec_transform.set_content_widget(self.transform_widget)
        self.layout_content.addWidget(sec_transform)
        
        # ── 2. Componente: RigidBody (se existir) ───────────
        from engine.physics.rigidbody import RigidBody
        rb = obj.get_component(RigidBody)
        if rb:
            sec_rb = CollapsibleSection("RigidBody (Física)")
            self.rb_widget = RigidBodyComponentWidget(self.viewmodel, rb)
            sec_rb.set_content_widget(self.rb_widget)
            self.layout_content.addWidget(sec_rb)
            
        # ── 3. Componente: Collider (se existir) ────────────
        from engine.physics.collider import BoxCollider, CircleCollider
        bc = obj.get_component(BoxCollider)
        cc = obj.get_component(CircleCollider)
        if bc or cc:
            collider = bc if bc else cc
            type_name = "Box" if bc else "Circle"
            sec_col = CollapsibleSection(f"{type_name} Collider (Colisor)")
            self.col_widget = ColliderComponentWidget(self.viewmodel, collider)
            sec_col.set_content_widget(self.col_widget)
            self.layout_content.addWidget(sec_col)
            
        # ── 4. Componente: Script (Comportamento) ───────────
        sec_script = CollapsibleSection("Script (Comportamento)")
        self.script_widget = ScriptComponentWidget(self.viewmodel)
        sec_script.set_content_widget(self.script_widget)
        self.layout_content.addWidget(sec_script)
            
        self._block_updates = False

    @Slot()
    def on_name_edited(self) -> None:
        """Notifica o ViewModel sobre a mudança de nome do objeto."""
        if not self.viewmodel or not self.viewmodel.selected_object:
            return
        new_name = self.txt_name.text()
        self.viewmodel.rename_object(self.viewmodel.selected_object, new_name)

    @Slot(str, str, object)
    def on_property_changed(self, component_name: str, property_name: str, value: object) -> None:
        """Chamado quando uma propriedade é alterada externamente (ex: sincroniza visual)."""
        if self._block_updates or not self.viewmodel or not self.viewmodel.selected_object:
            return
            
        # Atualiza a interface apenas se as propriedades mudarem fora do foco do spinbox
        # (ex: a escala mudou de forma indireta ao mudar o tamanho do colisor ou vice-versa)
        obj = self.viewmodel.selected_object
        
        if component_name == "Transform" and hasattr(self, "transform_widget"):
            tw = self.transform_widget
            tw.blockSignals(True)
            tw.sb_pos_x.setValue(obj.transform.position[0])
            tw.sb_pos_y.setValue(obj.transform.position[1])
            tw.sb_pos_z.setValue(obj.transform.position[2])
            tw.sb_sc_x.setValue(obj.transform.scale[0])
            tw.sb_sc_y.setValue(obj.transform.scale[1])
            tw.sb_sc_z.setValue(obj.transform.scale[2])
            tw.sb_rot_x.setValue(obj.transform.rotation[0])
            tw.sb_rot_y.setValue(obj.transform.rotation[1])
            tw.sb_rot_z.setValue(obj.transform.rotation[2])
            
            # Sincroniza os valores originais para a próxima edição do inspetor (apenas se a mudança veio de fora, ex: viewport/undo)
            if not getattr(tw, "_block_original_sync", False):
                tw.sb_pos_x.original_value = float(obj.transform.position[0])
                tw.sb_pos_y.original_value = float(obj.transform.position[1])
                tw.sb_pos_z.original_value = float(obj.transform.position[2])
                tw.sb_rot_x.original_value = float(obj.transform.rotation[0])
                tw.sb_rot_y.original_value = float(obj.transform.rotation[1])
                tw.sb_rot_z.original_value = float(obj.transform.rotation[2])
                tw.sb_sc_x.original_value = float(obj.transform.scale[0])
                tw.sb_sc_y.original_value = float(obj.transform.scale[1])
                tw.sb_sc_z.original_value = float(obj.transform.scale[2])
            
            tw.blockSignals(False)
            
        elif component_name == "RigidBody" and hasattr(self, "rb_widget"):
            from engine.physics.rigidbody import RigidBody
            rb = obj.get_component(RigidBody)
            if rb:
                self.rb_widget.blockSignals(True)
                self.rb_widget.sb_mass.setValue(rb.mass)
                self.rb_widget.sb_grav.setValue(rb.gravity_scale)
                self.rb_widget.chk_kin.setChecked(rb.is_kinematic)
                
                # Sincroniza original_value para a próxima edição do inspetor (apenas se a mudança veio de fora, ex: viewport/undo)
                if not getattr(self.rb_widget, "_block_original_sync", False):
                    self.rb_widget.sb_mass.original_value = float(rb.mass)
                    self.rb_widget.sb_grav.original_value = float(rb.gravity_scale)
                self.rb_widget.blockSignals(False)

        elif component_name == "Collider" and hasattr(self, "col_widget"):
            self.col_widget.blockSignals(True)
            from engine.physics.collider import BoxCollider, CircleCollider
            bc = obj.get_component(BoxCollider)
            cc = obj.get_component(CircleCollider)
            col = bc if bc else cc
            if col:
                self.col_widget.chk_trigger.setChecked(col.is_trigger)
            if bc and hasattr(self.col_widget, "sb_w"):
                self.col_widget.sb_w.setValue(bc.width)
                self.col_widget.sb_h.setValue(bc.height)
                if not getattr(self.col_widget, "_block_original_sync", False):
                    self.col_widget.sb_w.original_value = int(bc.width)
                    self.col_widget.sb_h.original_value = int(bc.height)
            elif cc and hasattr(self.col_widget, "sb_r"):
                self.col_widget.sb_r.setValue(cc.radius)
                if not getattr(self.col_widget, "_block_original_sync", False):
                    self.col_widget.sb_r.original_value = int(cc.radius)
            self.col_widget.blockSignals(False)
            
        elif component_name == "Script" and hasattr(self, "script_widget"):
            self.script_widget.blockSignals(True)
            self.script_widget.refresh_scripts_list()
            current_script = getattr(obj, "script_path", "")
            idx = self.script_widget.cb_scripts.findText(current_script)
            if idx >= 0:
                self.script_widget.cb_scripts.setCurrentIndex(idx)
            self.script_widget.btn_edit.setEnabled(bool(current_script and current_script != "Nenhum"))
            self.script_widget.blockSignals(False)
