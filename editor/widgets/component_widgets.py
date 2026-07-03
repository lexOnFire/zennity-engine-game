from PySide6.QtWidgets import (
    QWidget, QGridLayout, QHBoxLayout, QLabel, QDoubleSpinBox,
    QSpinBox, QCheckBox, QFormLayout, QComboBox, QPushButton
)
from PySide6.QtCore import Qt, Slot
from engine.game_object import GameObject
from engine.physics.rigidbody import RigidBody
from engine.physics.collider import BoxCollider, CircleCollider
from editor.viewmodels.scene_viewmodel import SceneViewModel


def create_spin_box(val: float, is_double: bool = True) -> QWidget:
    """Cria e formata um spin box escuro de alta precisão."""
    if is_double:
        sb = QDoubleSpinBox()
        sb.setRange(-999999.0, 999999.0)
        sb.setSingleStep(1.0)
        sb.setDecimals(1)
        sb.setValue(float(val))
    else:
        sb = QSpinBox()
        sb.setRange(-999999, 999999)
        sb.setSingleStep(1)
        sb.setValue(int(val))
        
    sb.setStyleSheet(
        "background-color: #111217; border: 1px solid #2d313f; border-radius: 4px;"
        "padding: 4px 6px; color: #cfd4de; selection-background-color: #409cff;"
    )
    return sb


class TransformComponentWidget(QWidget):
    """
    Editor gráfico das propriedades do Transform (posição, rotação e escala).
    """
    
    def __init__(self, viewmodel: SceneViewModel, parent: QWidget = None) -> None:
        super().__init__(parent)
        self.viewmodel = viewmodel
        self.obj = self.viewmodel.selected_object
        
        layout = QGridLayout(self)
        layout.setContentsMargins(0, 4, 0, 4)
        layout.setSpacing(6)
        
        # Cabeçalhos dos eixos
        layout.addWidget(QLabel(""), 0, 0)
        lbl_x = QLabel("X"); lbl_x.setAlignment(Qt.AlignCenter); lbl_x.setStyleSheet("color: #ff5c5c; font-weight: 600; font-size: 10px;")
        lbl_y = QLabel("Y"); lbl_y.setAlignment(Qt.AlignCenter); lbl_y.setStyleSheet("color: #4ade80; font-weight: 600; font-size: 10px;")
        lbl_z = QLabel("Z"); lbl_z.setAlignment(Qt.AlignCenter); lbl_z.setStyleSheet("color: #60a5fa; font-weight: 600; font-size: 10px;")
        
        layout.addWidget(lbl_x, 0, 1)
        layout.addWidget(lbl_y, 0, 2)
        layout.addWidget(lbl_z, 0, 3)
        
        # ── Posição ──────────────────────────
        layout.addWidget(QLabel("Posição:"), 1, 0)
        self.sb_pos_x = create_spin_box(self.obj.transform.position[0])
        self.sb_pos_y = create_spin_box(self.obj.transform.position[1])
        self.sb_pos_z = create_spin_box(self.obj.transform.position[2])
        
        layout.addWidget(self.sb_pos_x, 1, 1)
        layout.addWidget(self.sb_pos_y, 1, 2)
        layout.addWidget(self.sb_pos_z, 1, 3)
        
        # ── Rotação ──────────────────────────
        layout.addWidget(QLabel("Rotação:"), 2, 0)
        self.sb_rot_x = create_spin_box(self.obj.transform.rotation[0])
        self.sb_rot_y = create_spin_box(self.obj.transform.rotation[1])
        self.sb_rot_z = create_spin_box(self.obj.transform.rotation[2])
        
        layout.addWidget(self.sb_rot_x, 2, 1)
        layout.addWidget(self.sb_rot_y, 2, 2)
        layout.addWidget(self.sb_rot_z, 2, 3)
        
        # ── Escala ───────────────────────────
        layout.addWidget(QLabel("Escala:"), 3, 0)
        self.sb_sc_x = create_spin_box(self.obj.transform.scale[0])
        self.sb_sc_y = create_spin_box(self.obj.transform.scale[1])
        self.sb_sc_z = create_spin_box(self.obj.transform.scale[2])
        
        layout.addWidget(self.sb_sc_x, 3, 1)
        layout.addWidget(self.sb_sc_y, 3, 2)
        layout.addWidget(self.sb_sc_z, 3, 3)
        
        # Conexões de sinais
        self.sb_pos_x.valueChanged.connect(lambda val: self.viewmodel.set_transform_property("position", 0, val))
        self.sb_pos_y.valueChanged.connect(lambda val: self.viewmodel.set_transform_property("position", 1, val))
        self.sb_pos_z.valueChanged.connect(lambda val: self.viewmodel.set_transform_property("position", 2, val))
        
        self.sb_rot_x.valueChanged.connect(lambda val: self.viewmodel.set_transform_property("rotation", 0, val))
        self.sb_rot_y.valueChanged.connect(lambda val: self.viewmodel.set_transform_property("rotation", 1, val))
        self.sb_rot_z.valueChanged.connect(lambda val: self.viewmodel.set_transform_property("rotation", 2, val))
        
        self.sb_sc_x.valueChanged.connect(lambda val: self.viewmodel.set_transform_property("scale", 0, val))
        self.sb_sc_y.valueChanged.connect(lambda val: self.viewmodel.set_transform_property("scale", 1, val))
        self.sb_sc_z.valueChanged.connect(lambda val: self.viewmodel.set_transform_property("scale", 2, val))


class RigidBodyComponentWidget(QWidget):
    """
    Editor das propriedades de física do RigidBody.
    """
    
    def __init__(self, viewmodel: SceneViewModel, rb: RigidBody, parent: QWidget = None) -> None:
        super().__init__(parent)
        self.viewmodel = viewmodel
        self.rb = rb
        
        layout = QFormLayout(self)
        layout.setContentsMargins(0, 4, 0, 4)
        layout.setSpacing(6)
        
        self.sb_mass = create_spin_box(self.rb.mass)
        self.sb_mass.setSingleStep(0.1)
        self.sb_mass.setRange(0.01, 1000.0)
        
        self.sb_grav = create_spin_box(self.rb.gravity_scale)
        self.sb_grav.setSingleStep(0.1)
        
        self.chk_kin = QCheckBox()
        self.chk_kin.setChecked(self.rb.is_kinematic)
        
        layout.addRow("Massa:", self.sb_mass)
        layout.addRow("Escala Gravidade:", self.sb_grav)
        layout.addRow("Cinemático (Estático):", self.chk_kin)
        
        # Conexões
        self.sb_mass.valueChanged.connect(lambda val: self.viewmodel.set_rigidbody_property("mass", val))
        self.sb_grav.valueChanged.connect(lambda val: self.viewmodel.set_rigidbody_property("gravity_scale", val))
        self.chk_kin.toggled.connect(lambda val: self.viewmodel.set_rigidbody_property("is_kinematic", val))


class ColliderComponentWidget(QWidget):
    """
    Editor para colisores 2D (BoxCollider e CircleCollider).
    """
    
    def __init__(self, viewmodel: SceneViewModel, collider, parent: QWidget = None) -> None:
        super().__init__(parent)
        self.viewmodel = viewmodel
        self.collider = collider
        
        layout = QFormLayout(self)
        layout.setContentsMargins(0, 4, 0, 4)
        layout.setSpacing(6)
        
        self.chk_trigger = QCheckBox()
        self.chk_trigger.setChecked(self.collider.is_trigger)
        self.chk_trigger.toggled.connect(lambda val: self.viewmodel.set_collider_property("is_trigger", val))
        
        if isinstance(self.collider, BoxCollider):
            self.sb_w = create_spin_box(self.collider.width, is_double=False)
            self.sb_w.setRange(1, 9999)
            self.sb_w.valueChanged.connect(lambda val: self.viewmodel.set_collider_property("width", val))
            
            self.sb_h = create_spin_box(self.collider.height, is_double=False)
            self.sb_h.setRange(1, 9999)
            self.sb_h.valueChanged.connect(lambda val: self.viewmodel.set_collider_property("height", val))
            
            layout.addRow("Largura (W):", self.sb_w)
            layout.addRow("Altura (H):", self.sb_h)
        elif isinstance(self.collider, CircleCollider):
            self.sb_r = create_spin_box(self.collider.radius, is_double=False)
            self.sb_r.setRange(1, 9999)
            self.sb_r.valueChanged.connect(lambda val: self.viewmodel.set_collider_property("radius", val))
            
            layout.addRow("Raio (R):", self.sb_r)
            
        layout.addRow("Is Trigger:", self.chk_trigger)


from editor_legacy.script_manager import ScriptManager

class ScriptComponentWidget(QWidget):
    """
    Editor para associar e editar scripts de comportamento nos GameObjects.
    """
    
    def __init__(self, viewmodel: SceneViewModel, parent: QWidget = None) -> None:
        super().__init__(parent)
        self.viewmodel = viewmodel
        self.obj = self.viewmodel.selected_object
        
        layout = QFormLayout(self)
        layout.setContentsMargins(0, 4, 0, 4)
        layout.setSpacing(6)
        
        # 1. Combo box de scripts
        self.cb_scripts = QComboBox()
        self.refresh_scripts_list()
        
        # Seleciona o script atual se houver
        current_script = getattr(self.obj, "script_path", "")
        if current_script:
            idx = self.cb_scripts.findText(current_script)
            if idx >= 0:
                self.cb_scripts.setCurrentIndex(idx)
            else:
                self.cb_scripts.addItem(current_script)
                self.cb_scripts.setCurrentIndex(self.cb_scripts.count() - 1)
                
        self.cb_scripts.currentIndexChanged.connect(self.on_script_changed)
        layout.addRow("Arquivo Script:", self.cb_scripts)
        
        # 2. Botões de ação
        btn_layout = QHBoxLayout()
        self.btn_edit = QPushButton("Editar Code")
        self.btn_edit.clicked.connect(self.edit_script)
        self.btn_edit.setEnabled(bool(current_script and current_script != "Nenhum"))
        
        self.btn_create = QPushButton("Novo Script")
        self.btn_create.clicked.connect(self.create_script)
        
        btn_layout.addWidget(self.btn_edit)
        btn_layout.addWidget(self.btn_create)
        layout.addRow("", btn_layout)

    def refresh_scripts_list(self) -> None:
        self.cb_scripts.clear()
        scripts = ScriptManager.list_scripts()
        self.cb_scripts.addItems(scripts)

    def on_script_changed(self, index: int) -> None:
        script = self.cb_scripts.currentText()
        if script == "Nenhum":
            self.obj.script_path = ""
            self.btn_edit.setEnabled(False)
        else:
            self.obj.script_path = script
            self.btn_edit.setEnabled(True)
            
        # Publica alteração no EventBus
        try:
            from editor.core.event_bus import EventBus, EVENT_PROPERTY_CHANGED
            EventBus.emit(
                EVENT_PROPERTY_CHANGED,
                component_name="Script",
                property_name="script_path",
                value=self.obj.script_path
            )
        except Exception:
            pass

    def edit_script(self) -> None:
        script = getattr(self.obj, "script_path", "")
        if script and script != "Nenhum":
            # Procura pela MainWindow no parent tree e abre o CodeEditorDock
            win = self.window()
            if win and hasattr(win, "dock_code_editor"):
                win.dock_code_editor.open_file(script)

    def create_script(self) -> None:
        if not self.obj:
            return
            
        path = ScriptManager.create_template(self.obj)
        self.refresh_scripts_list()
        
        # Seleciona o novo script no combo box
        idx = self.cb_scripts.findText(path)
        if idx >= 0:
            self.cb_scripts.setCurrentIndex(idx)
            
        # Abre o editor de código automaticamente
        self.edit_script()
