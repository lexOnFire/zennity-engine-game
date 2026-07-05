from PySide6.QtWidgets import (
    QWidget, QGridLayout, QHBoxLayout, QVBoxLayout, QLabel, QDoubleSpinBox,
    QSpinBox, QCheckBox, QFormLayout, QComboBox, QPushButton, QLineEdit
)
from PySide6.QtCore import Qt, Slot
import os
import re
from engine.game_object import GameObject
from engine.physics.rigidbody import RigidBody
from editor.viewmodels.scene_viewmodel import SceneViewModel


def create_spin_box(val: float, is_double: bool = True) -> QWidget:
    """Cria e formata um spin box escuro de alta precisão com localidade C neutra."""
    from PySide6.QtCore import QLocale
    if is_double:
        sb = QDoubleSpinBox()
        sb.setRange(-999999.0, 999999.0)
        sb.setSingleStep(1.0)
        sb.setDecimals(2)  # Exibe 2 casas decimais estilo Unity (0.00)
        sb.setValue(float(val))
    else:
        sb = QSpinBox()
        sb.setRange(-999999, 999999)
        sb.setSingleStep(1)
        sb.setValue(int(val))
        
    sb.setLocale(QLocale.c())
    sb.setStyleSheet(
        "background-color: #202020; border: 1px solid #151515; border-radius: 3px;"
        "padding: 3px 5px; color: #ffffff; selection-background-color: #2f5c8f;"
    )
    return sb


def validate_and_get_value(sb: QDoubleSpinBox | QSpinBox) -> float | int | None:
    """Valida a entrada do spinbox para evitar NaN/Inf ou texto vazio, revertendo para original_value em caso de erro."""
    import math
    try:
        text = sb.cleanText().strip()
        if text == "":
            sb.setValue(sb.original_value)
            return None
            
        cleaned_text = text.replace(",", ".")
        try:
            float(cleaned_text)
        except ValueError:
            sb.setValue(sb.original_value)
            return None
            
        val = sb.value()
        if math.isnan(val) or math.isinf(val):
            sb.setValue(sb.original_value)
            return None
            
        return val
    except Exception:
        if hasattr(sb, "original_value"):
            sb.setValue(sb.original_value)
        return None


class TransformComponentWidget(QWidget):
    """
    Editor gráfico das propriedades do Transform (posição, rotação e escala).
    Alinhado de forma horizontal compacta (X, Y, Z).
    """
    
    def __init__(self, viewmodel: SceneViewModel, parent: QWidget = None) -> None:
        super().__init__(parent)
        self.viewmodel = viewmodel
        self.obj = self.viewmodel.selected_object
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 4)
        layout.setSpacing(6)
        
        # 1. Posição
        self.sb_pos_x = create_spin_box(self.obj.transform.position[0])
        self.sb_pos_y = create_spin_box(self.obj.transform.position[1])
        self.sb_pos_z = create_spin_box(self.obj.transform.position[2])
        self.sb_pos_z.setEnabled(False) # 2D engine
        layout.addLayout(self._create_row("Posição", self.sb_pos_x, self.sb_pos_y, self.sb_pos_z))
        
        # 2. Rotação
        self.sb_rot_x = create_spin_box(self.obj.transform.rotation[0])
        self.sb_rot_x.setEnabled(False) # 2D engine
        self.sb_rot_y = create_spin_box(self.obj.transform.rotation[1])
        self.sb_rot_y.setEnabled(False) # 2D engine
        self.sb_rot_z = create_spin_box(self.obj.transform.rotation[2])
        layout.addLayout(self._create_row("Rotação", self.sb_rot_x, self.sb_rot_y, self.sb_rot_z))
        
        # 3. Escala
        self.sb_sc_x = create_spin_box(self.obj.transform.scale[0])
        self.sb_sc_y = create_spin_box(self.obj.transform.scale[1])
        self.sb_sc_z = create_spin_box(self.obj.transform.scale[2])
        self.sb_sc_z.setEnabled(False) # 2D engine
        layout.addLayout(self._create_row("Escala", self.sb_sc_x, self.sb_sc_y, self.sb_sc_z))
        
        # Armazena os valores originais para commit do histórico de undo
        self.sb_pos_x.original_value = float(self.obj.transform.position[0])
        self.sb_pos_y.original_value = float(self.obj.transform.position[1])
        self.sb_pos_z.original_value = float(self.obj.transform.position[2])
        
        self.sb_rot_x.original_value = float(self.obj.transform.rotation[0])
        self.sb_rot_y.original_value = float(self.obj.transform.rotation[1])
        self.sb_rot_z.original_value = float(self.obj.transform.rotation[2])
        
        self.sb_sc_x.original_value = float(self.obj.transform.scale[0])
        self.sb_sc_y.original_value = float(self.obj.transform.scale[1])
        self.sb_sc_z.original_value = float(self.obj.transform.scale[2])

        self._block_original_sync = False
        
        # Conexões interativas em tempo real (valueChanged)
        self.sb_pos_x.valueChanged.connect(lambda val: self._on_value_changed("position", 0, val))
        self.sb_pos_y.valueChanged.connect(lambda val: self._on_value_changed("position", 1, val))
        self.sb_pos_z.valueChanged.connect(lambda val: self._on_value_changed("position", 2, val))
        
        self.sb_rot_x.valueChanged.connect(lambda val: self._on_value_changed("rotation", 0, val))
        self.sb_rot_y.valueChanged.connect(lambda val: self._on_value_changed("rotation", 1, val))
        self.sb_rot_z.valueChanged.connect(lambda val: self._on_value_changed("rotation", 2, val))
        
        self.sb_sc_x.valueChanged.connect(lambda val: self._on_value_changed("scale", 0, val))
        self.sb_sc_y.valueChanged.connect(lambda val: self._on_value_changed("scale", 1, val))
        self.sb_sc_z.valueChanged.connect(lambda val: self._on_value_changed("scale", 2, val))

        # Conexões definitivas para gerar comandos de histórico (editingFinished)
        self.sb_pos_x.editingFinished.connect(lambda: self.commit_val(self.sb_pos_x, "position", 0))
        self.sb_pos_y.editingFinished.connect(lambda: self.commit_val(self.sb_pos_y, "position", 1))
        self.sb_pos_z.editingFinished.connect(lambda: self.commit_val(self.sb_pos_z, "position", 2))
        
        self.sb_rot_x.editingFinished.connect(lambda: self.commit_val(self.sb_rot_x, "rotation", 0))
        self.sb_rot_y.editingFinished.connect(lambda: self.commit_val(self.sb_rot_y, "rotation", 1))
        self.sb_rot_z.editingFinished.connect(lambda: self.commit_val(self.sb_rot_z, "rotation", 2))
        
        self.sb_sc_x.editingFinished.connect(lambda: self.commit_val(self.sb_sc_x, "scale", 0))
        self.sb_sc_y.editingFinished.connect(lambda: self.commit_val(self.sb_sc_y, "scale", 1))
        self.sb_sc_z.editingFinished.connect(lambda: self.commit_val(self.sb_sc_z, "scale", 2))

    def _create_row(self, label_text: str, sb_x: QWidget, sb_y: QWidget, sb_z: QWidget) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(6)
        
        lbl = QLabel(label_text)
        lbl.setFixedWidth(55)
        lbl.setStyleSheet("color: #8c8c8c; font-size: 11px;")
        row.addWidget(lbl)
        
        # X
        lay_x = QHBoxLayout(); lay_x.setSpacing(2)
        lbl_x = QLabel("X")
        lbl_x.setStyleSheet("color: #808080; font-size: 10px;")
        lay_x.addWidget(lbl_x); lay_x.addWidget(sb_x)
        row.addLayout(lay_x, 1)
        
        # Y
        lay_y = QHBoxLayout(); lay_y.setSpacing(2)
        lbl_y = QLabel("Y")
        lbl_y.setStyleSheet("color: #808080; font-size: 10px;")
        lay_y.addWidget(lbl_y); lay_y.addWidget(sb_y)
        row.addLayout(lay_y, 1)
        
        # Z
        lay_z = QHBoxLayout(); lay_z.setSpacing(2)
        lbl_z = QLabel("Z")
        lbl_z.setStyleSheet("color: #808080; font-size: 10px;")
        lay_z.addWidget(lbl_z); lay_z.addWidget(sb_z)
        row.addLayout(lay_z, 1)
        
        return row

    def _on_value_changed(self, prop_name: str, index: int, val: float) -> None:
        self._block_original_sync = True
        try:
            self.viewmodel.set_transform_property(prop_name, index, val)
        finally:
            self._block_original_sync = False

    def commit_val(self, sb: QDoubleSpinBox, prop_name: str, index: int) -> None:
        if not self.viewmodel or not self.viewmodel.selected_object:
            return
        val = validate_and_get_value(sb)
        if val is None:
            return
        new_val = float(val)
        old_val = float(getattr(sb, "original_value", new_val))
        if old_val != new_val:
            self.viewmodel.commit_transform_property(prop_name, index, old_val, new_val)
            sb.original_value = new_val


class MeshRendererComponentWidget(QWidget):
    """
    Widget visual simulado para o Mesh Renderer estilo Unity/Godot.
    """
    
    def __init__(self, obj: GameObject, parent: QWidget = None) -> None:
        super().__init__(parent)
        self.obj = obj
        
        layout = QGridLayout(self)
        layout.setContentsMargins(0, 4, 0, 4)
        layout.setSpacing(6)
        
        # Mesh
        lbl_mesh = QLabel("Mesh")
        lbl_mesh.setStyleSheet("color: #8c8c8c;")
        layout.addWidget(lbl_mesh, 0, 0)
        
        mesh_container = QHBoxLayout()
        mesh_container.setSpacing(4)
        
        self.txt_mesh = QLineEdit(f"📄 {getattr(self.obj, 'mesh_type', 'Character')}.fbx")
        self.txt_mesh.setReadOnly(True)
        self.txt_mesh.setStyleSheet("background-color: #202020; color: #a0a0a0; padding: 4px; border: 1px solid #151515;")
        
        btn_mesh_locate = QPushButton("⚙️")
        btn_mesh_locate.setFixedWidth(20)
        btn_mesh_locate.setStyleSheet("padding: 2px; background-color: #2b2b2b;")
        
        mesh_container.addWidget(self.txt_mesh)
        mesh_container.addWidget(btn_mesh_locate)
        layout.addLayout(mesh_container, 0, 1)
        
        # Material
        lbl_mat = QLabel("Material")
        lbl_mat.setStyleSheet("color: #8c8c8c;")
        layout.addWidget(lbl_mat, 1, 0)
        
        mat_container = QHBoxLayout()
        mat_container.setSpacing(4)
        
        self.lbl_mat_preview = QLabel("⚪")
        self.lbl_mat_preview.setStyleSheet("font-size: 14px; border: none; padding-right: 4px;")
        
        self.cb_material = QComboBox()
        self.cb_material.addItem("Default_Material")
        self.cb_material.addItem("Metalic_Material")
        self.cb_material.addItem("Smooth_Material")
        
        btn_mat_settings = QPushButton("⚙️")
        btn_mat_settings.setFixedWidth(20)
        btn_mat_settings.setStyleSheet("padding: 2px; background-color: #2b2b2b;")
        
        mat_container.addWidget(self.lbl_mat_preview)
        mat_container.addWidget(self.cb_material, 1)
        mat_container.addWidget(btn_mat_settings)
        layout.addLayout(mat_container, 1, 1)


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
        
        # Armazena os valores originais para commit do histórico de undo
        self.sb_mass.original_value = float(self.rb.mass)
        self.sb_grav.original_value = float(self.rb.gravity_scale)
        self._block_original_sync = False
        
        # Conexões interativas em tempo real (valueChanged)
        self.sb_mass.valueChanged.connect(lambda val: self._on_value_changed("mass", val))
        self.sb_grav.valueChanged.connect(lambda val: self._on_value_changed("gravity_scale", val))
        
        # Conexões definitivas para gerar comandos de histórico (editingFinished / clicked)
        self.sb_mass.editingFinished.connect(lambda: self.commit_val(self.sb_mass, "mass"))
        self.sb_grav.editingFinished.connect(lambda: self.commit_val(self.sb_grav, "gravity_scale"))
        self.chk_kin.clicked.connect(self.commit_kinematic)

    def _on_value_changed(self, prop_name: str, val: float) -> None:
        self._block_original_sync = True
        try:
            self.viewmodel.set_rigidbody_property(prop_name, val)
        finally:
            self._block_original_sync = False

    def commit_val(self, sb: QDoubleSpinBox, prop_name: str) -> None:
        if not self.viewmodel or not self.viewmodel.selected_object:
            return
        val = validate_and_get_value(sb)
        if val is None:
            return
        new_val = float(val)
        old_val = float(getattr(sb, "original_value", new_val))
        if old_val != new_val:
            self.viewmodel.commit_rigidbody_property(prop_name, old_val, new_val)
            sb.original_value = new_val

    def commit_kinematic(self) -> None:
        if not self.viewmodel or not self.viewmodel.selected_object:
            return
        new_val = self.chk_kin.isChecked()
        old_val = not new_val
        self.viewmodel.commit_rigidbody_property("is_kinematic", old_val, new_val)


class ColliderComponentWidget(QWidget):
    """
    Editor para colisores 2D (BoxCollider e CircleCollider).
    Formatado com exibição compacta Centro/Tamanho X, Y, Z.
    """
    
    def __init__(self, viewmodel: SceneViewModel, collider, parent: QWidget = None) -> None:
        super().__init__(parent)
        self.viewmodel = viewmodel
        self.collider = collider
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 4)
        layout.setSpacing(6)
        
        # Editar Collider & Trigger checkbox row
        top_row = QHBoxLayout()
        self.chk_edit = QCheckBox("Editar Collider")
        self.chk_edit.setChecked(True)
        
        self.chk_trigger = QCheckBox("Is Trigger")
        self.chk_trigger.setChecked(self.collider.is_trigger)
        self.chk_trigger.clicked.connect(self.commit_trigger)
        
        top_row.addWidget(self.chk_edit)
        top_row.addWidget(self.chk_trigger)
        layout.addLayout(top_row)
        
        self._block_original_sync = False
        
        # Centro (Simulado com X=0, Y=0, Z=0)
        self.sb_offset_x = create_spin_box(0.0)
        self.sb_offset_x.setEnabled(False)
        self.sb_offset_y = create_spin_box(0.0)
        self.sb_offset_y.setEnabled(False)
        self.sb_offset_z = create_spin_box(0.0)
        self.sb_offset_z.setEnabled(False)
        layout.addLayout(self._create_row("Centro", self.sb_offset_x, self.sb_offset_y, self.sb_offset_z))
        
        if type(self.collider).__name__ == "BoxCollider":
            # Tamanho (X=width, Y=height, Z=0.60)
            self.sb_w = create_spin_box(self.collider.width, is_double=False)
            self.sb_w.setRange(1, 9999)
            self.sb_w.original_value = int(self.collider.width)
            self.sb_w.valueChanged.connect(lambda val: self._on_value_changed("width", val))
            self.sb_w.editingFinished.connect(lambda: self.commit_val(self.sb_w, "width"))
            
            self.sb_h = create_spin_box(self.collider.height, is_double=False)
            self.sb_h.setRange(1, 9999)
            self.sb_h.original_value = int(self.collider.height)
            self.sb_h.valueChanged.connect(lambda val: self._on_value_changed("height", val))
            self.sb_h.editingFinished.connect(lambda: self.commit_val(self.sb_h, "height"))
            
            self.sb_z = create_spin_box(0.60)
            self.sb_z.setEnabled(False)
            
            layout.addLayout(self._create_row("Tamanho", self.sb_w, self.sb_h, self.sb_z))
            
        elif type(self.collider).__name__ == "CircleCollider":
            # Tamanho/Raio (X=radius, Y=radius, Z=1.00)
            self.sb_r = create_spin_box(self.collider.radius, is_double=False)
            self.sb_r.setRange(1, 9999)
            self.sb_r.original_value = int(self.collider.radius)
            self.sb_r.valueChanged.connect(lambda val: self._on_value_changed("radius", val))
            self.sb_r.editingFinished.connect(lambda: self.commit_val(self.sb_r, "radius"))
            
            self.sb_r_y = create_spin_box(self.collider.radius, is_double=False)
            self.sb_r_y.setEnabled(False)
            
            self.sb_z = create_spin_box(1.00)
            self.sb_z.setEnabled(False)
            
            layout.addLayout(self._create_row("Tamanho", self.sb_r, self.sb_r_y, self.sb_z))

    def _create_row(self, label_text: str, sb_x: QWidget, sb_y: QWidget, sb_z: QWidget) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(6)
        
        lbl = QLabel(label_text)
        lbl.setFixedWidth(55)
        lbl.setStyleSheet("color: #8c8c8c; font-size: 11px;")
        row.addWidget(lbl)
        
        # X
        lay_x = QHBoxLayout(); lay_x.setSpacing(2)
        lbl_x = QLabel("X")
        lbl_x.setStyleSheet("color: #808080; font-size: 10px;")
        lay_x.addWidget(lbl_x); lay_x.addWidget(sb_x)
        row.addLayout(lay_x, 1)
        
        # Y
        lay_y = QHBoxLayout(); lay_y.setSpacing(2)
        lbl_y = QLabel("Y")
        lbl_y.setStyleSheet("color: #808080; font-size: 10px;")
        lay_y.addWidget(lbl_y); lay_y.addWidget(sb_y)
        row.addLayout(lay_y, 1)
        
        # Z
        lay_z = QHBoxLayout(); lay_z.setSpacing(2)
        lbl_z = QLabel("Z")
        lbl_z.setStyleSheet("color: #808080; font-size: 10px;")
        lay_z.addWidget(lbl_z); lay_z.addWidget(sb_z)
        row.addLayout(lay_z, 1)
        
        return row

    def _on_value_changed(self, prop_name: str, val: float) -> None:
        self._block_original_sync = True
        try:
            self.viewmodel.set_collider_property(prop_name, val)
        finally:
            self._block_original_sync = False

    def commit_val(self, sb: QSpinBox | QDoubleSpinBox, prop_name: str) -> None:
        if not self.viewmodel or not self.viewmodel.selected_object:
            return
        val = validate_and_get_value(sb)
        if val is None:
            return
        new_val = int(val)
        old_val = int(getattr(sb, "original_value", new_val))
        if old_val != new_val:
            self.viewmodel.commit_collider_property(prop_name, old_val, new_val)
            sb.original_value = new_val

    def commit_trigger(self) -> None:
        if not self.viewmodel or not self.viewmodel.selected_object:
            return
        new_val = self.chk_trigger.isChecked()
        old_val = not new_val
        self.viewmodel.commit_collider_property("is_trigger", old_val, new_val)


from editor.core.script_manager import ScriptManager

class ScriptComponentWidget(QWidget):
    """
    Editor para associar e editar scripts de comportamento nos GameObjects.
    Exibe propriedades do script de forma dinâmica.
    """
    
    def __init__(self, viewmodel: SceneViewModel, parent: QWidget = None) -> None:
        super().__init__(parent)
        self.viewmodel = viewmodel
        self.obj = self.viewmodel.selected_object
        
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 4, 0, 4)
        self.main_layout.setSpacing(6)
        
        # 1. Linha do arquivo de Script
        script_row = QHBoxLayout()
        lbl_script = QLabel("Script")
        lbl_script.setFixedWidth(55)
        lbl_script.setStyleSheet("color: #8c8c8c;")
        
        self.cb_scripts = QComboBox()
        self.refresh_scripts_list()
        
        current_script = getattr(self.obj, "script_path", "")
        if current_script:
            idx = self.cb_scripts.findText(current_script)
            if idx >= 0:
                self.cb_scripts.setCurrentIndex(idx)
            else:
                self.cb_scripts.addItem(current_script)
                self.cb_scripts.setCurrentIndex(self.cb_scripts.count() - 1)
                
        self.cb_scripts.activated.connect(self.on_script_activated)
        
        self.btn_edit = QPushButton("📄")
        self.btn_edit.setFixedWidth(20)
        self.btn_edit.setStyleSheet("padding: 2px; background-color: #2b2b2b;")
        self.btn_edit.clicked.connect(self.edit_script)
        self.btn_edit.setEnabled(bool(current_script and current_script != "Nenhum"))
        
        script_row.addWidget(lbl_script)
        script_row.addWidget(self.cb_scripts, 1)
        script_row.addWidget(self.btn_edit)
        self.main_layout.addLayout(script_row)
        
        # 2. Variáveis dinâmicas do Script
        self.vars_container = QWidget()
        self.vars_layout = QFormLayout(self.vars_container)
        self.vars_layout.setContentsMargins(0, 4, 0, 4)
        self.vars_layout.setSpacing(6)
        
        self.main_layout.addWidget(self.vars_container)
        self.update_dynamic_variables()
        
        # 3. Botão para Criar Novo Script
        self.btn_create = QPushButton("Criar Novo Script")
        self.btn_create.setStyleSheet("background-color: #2b2b2b; color: #a0a0a0; padding: 4px;")
        self.btn_create.clicked.connect(self.create_script)
        self.main_layout.addWidget(self.btn_create)

    def refresh_scripts_list(self) -> None:
        self.cb_scripts.clear()
        scripts = ScriptManager.list_scripts()
        self.cb_scripts.addItems(scripts)

    def update_dynamic_variables(self) -> None:
        # Limpa layout antigo
        while self.vars_layout.count():
            item = self.vars_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
                
        script_path = getattr(self.obj, "script_path", "")
        if not script_path or script_path == "Nenhum" or not os.path.exists(script_path):
            return
            
        try:
            with open(script_path, "r", encoding="utf-8") as f:
                content = f.read()
                
            # Procura por padrões tipo: self.velocidade = 5.0 ou obj.velocidade = 5.0
            matches = re.findall(r"(?:self|obj)\.([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*(-?[0-9]+(?:\.[0-9]+)?)", content)
            
            seen = set()
            for var_name, var_val in matches:
                if var_name in seen or var_name in ["script_time", "script_module", "script_path"]:
                    continue
                seen.add(var_name)
                
                # Se o valor já existe no objeto, usa o valor atual; senão usa o padrão do script
                current_val = getattr(self.obj, var_name, float(var_val))
                setattr(self.obj, var_name, current_val)
                
                sb = create_spin_box(current_val)
                sb.setSingleStep(0.1)
                sb.valueChanged.connect(lambda val, name=var_name: setattr(self.obj, name, val))
                
                display_name = var_name.capitalize()
                self.vars_layout.addRow(f"{display_name}:", sb)
        except Exception as e:
            print(f"[Inspector] Erro ao analisar variáveis do script: {e}")

    def on_script_activated(self, index: int) -> None:
        if not self.viewmodel or not self.viewmodel.selected_object:
            return
        script = self.cb_scripts.currentText()
        old_val = getattr(self.obj, "script_path", "")
        new_val = "" if script == "Nenhum" else script
        
        if old_val != new_val:
            self.viewmodel.commit_script_property(old_val, new_val)
            self.btn_edit.setEnabled(bool(new_val))
            self.update_dynamic_variables()

    def edit_script(self) -> None:
        script = getattr(self.obj, "script_path", "")
        if script and script != "Nenhum":
            win = self.window()
            if win and hasattr(win, "dock_code_editor"):
                win.dock_code_editor.open_file(script)

    def create_script(self) -> None:
        if not self.obj:
            return
            
        path = ScriptManager.create_template(self.obj)
        self.refresh_scripts_list()
        
        idx = self.cb_scripts.findText(path)
        if idx >= 0:
            self.cb_scripts.setCurrentIndex(idx)
            old_val = getattr(self.obj, "script_path", "")
            self.viewmodel.commit_script_property(old_val, path)
            self.btn_edit.setEnabled(True)
            self.update_dynamic_variables()
            
        self.edit_script()
