from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt, Slot
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QDoubleSpinBox, QFormLayout,
    QGridLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QSizePolicy, QSpinBox, QWidget,
)

from engine.game_object import GameObject
from engine.physics.rigidbody import RigidBody
from engine.physics.collider import BoxCollider, CircleCollider
from editor.viewmodels.scene_viewmodel import SceneViewModel


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

_SB_STYLE = (
    "QDoubleSpinBox, QSpinBox {"
    "  background-color: #0f1117;"
    "  border: 1px solid #2a2d3a;"
    "  border-radius: 4px;"
    "  padding: 3px 6px;"
    "  color: #c9cdd6;"
    "  min-width: 56px;"
    "}"
    "QDoubleSpinBox:focus, QSpinBox:focus {"
    "  border-color: #3b82f6;"
    "}"
)

_LABEL_X = "color: #f87171; font-weight: 700; font-size: 10px;"
_LABEL_Y = "color: #4ade80; font-weight: 700; font-size: 10px;"
_LABEL_Z = "color: #60a5fa; font-weight: 700; font-size: 10px;"
_LABEL_ROW = "color: #9ca3af; font-size: 11px; min-width: 60px;"


def _dsb(val: float, step: float = 0.01, decimals: int = 2) -> QDoubleSpinBox:
    sb = QDoubleSpinBox()
    sb.setRange(-999999.0, 999999.0)
    sb.setSingleStep(step)
    sb.setDecimals(decimals)
    sb.setValue(float(val))
    sb.setStyleSheet(_SB_STYLE)
    sb.setButtonSymbols(QDoubleSpinBox.NoButtons)
    return sb


def _isb(val: int) -> QSpinBox:
    sb = QSpinBox()
    sb.setRange(-999999, 999999)
    sb.setValue(int(val))
    sb.setStyleSheet(_SB_STYLE)
    sb.setButtonSymbols(QSpinBox.NoButtons)
    return sb


def _xyz_header(layout: QGridLayout, col_offset: int = 1) -> None:
    for col, txt, style in (
        (col_offset,     "X", _LABEL_X),
        (col_offset + 1, "Y", _LABEL_Y),
        (col_offset + 2, "Z", _LABEL_Z),
    ):
        lbl = QLabel(txt)
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setStyleSheet(style)
        layout.addWidget(lbl, 0, col)


def _row_label(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet(_LABEL_ROW)
    return lbl


# ─────────────────────────────────────────────────────────────────────────────
# Transform
# ─────────────────────────────────────────────────────────────────────────────

class TransformComponentWidget(QWidget):
    def __init__(self, viewmodel: SceneViewModel, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.viewmodel = viewmodel
        obj = viewmodel.selected_object

        g = QGridLayout(self)
        g.setContentsMargins(0, 4, 0, 4)
        g.setSpacing(5)
        g.setColumnStretch(0, 0)
        for c in (1, 2, 3):
            g.setColumnStretch(c, 1)

        _xyz_header(g)

        # Posição
        g.addWidget(_row_label("Posição"), 1, 0)
        self.sb_pos_x = _dsb(obj.transform.position[0])
        self.sb_pos_y = _dsb(obj.transform.position[1])
        self.sb_pos_z = _dsb(obj.transform.position[2])
        g.addWidget(self.sb_pos_x, 1, 1)
        g.addWidget(self.sb_pos_y, 1, 2)
        g.addWidget(self.sb_pos_z, 1, 3)

        # Rotação
        g.addWidget(_row_label("Rotação"), 2, 0)
        self.sb_rot_x = _dsb(obj.transform.rotation[0])
        self.sb_rot_y = _dsb(obj.transform.rotation[1])
        self.sb_rot_z = _dsb(obj.transform.rotation[2])
        g.addWidget(self.sb_rot_x, 2, 1)
        g.addWidget(self.sb_rot_y, 2, 2)
        g.addWidget(self.sb_rot_z, 2, 3)

        # Escala
        g.addWidget(_row_label("Escala"), 3, 0)
        self.sb_sc_x = _dsb(obj.transform.scale[0])
        self.sb_sc_y = _dsb(obj.transform.scale[1])
        self.sb_sc_z = _dsb(obj.transform.scale[2])
        g.addWidget(self.sb_sc_x, 3, 1)
        g.addWidget(self.sb_sc_y, 3, 2)
        g.addWidget(self.sb_sc_z, 3, 3)

        self.sb_pos_x.valueChanged.connect(lambda v: viewmodel.set_transform_property("position", 0, v))
        self.sb_pos_y.valueChanged.connect(lambda v: viewmodel.set_transform_property("position", 1, v))
        self.sb_pos_z.valueChanged.connect(lambda v: viewmodel.set_transform_property("position", 2, v))
        self.sb_rot_x.valueChanged.connect(lambda v: viewmodel.set_transform_property("rotation", 0, v))
        self.sb_rot_y.valueChanged.connect(lambda v: viewmodel.set_transform_property("rotation", 1, v))
        self.sb_rot_z.valueChanged.connect(lambda v: viewmodel.set_transform_property("rotation", 2, v))
        self.sb_sc_x.valueChanged.connect(lambda v: viewmodel.set_transform_property("scale", 0, v))
        self.sb_sc_y.valueChanged.connect(lambda v: viewmodel.set_transform_property("scale", 1, v))
        self.sb_sc_z.valueChanged.connect(lambda v: viewmodel.set_transform_property("scale", 2, v))


# ─────────────────────────────────────────────────────────────────────────────
# Mesh Renderer
# ─────────────────────────────────────────────────────────────────────────────

_FIELD_STYLE = (
    "QLineEdit {"
    "  background: #0f1117;"
    "  border: 1px solid #2a2d3a;"
    "  border-radius: 4px;"
    "  padding: 3px 8px;"
    "  color: #c9cdd6;"
    "  font-size: 11px;"
    "}"
)


class MeshRendererWidget(QWidget):
    """Widget para o componente Mesh Renderer."""

    def __init__(self, viewmodel: SceneViewModel, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.viewmodel = viewmodel
        obj = viewmodel.selected_object
        mesh_name = getattr(obj, "mesh_path", None) or getattr(obj, "mesh_type", "") or "Character.fbx"
        material_name = getattr(obj, "material", None) or "Default_Material"

        form = QFormLayout(self)
        form.setContentsMargins(0, 4, 0, 4)
        form.setSpacing(8)
        form.setLabelAlignment(Qt.AlignLeft)

        # Mesh
        mesh_row = QHBoxLayout()
        mesh_row.setSpacing(4)
        self.txt_mesh = QLineEdit(str(mesh_name))
        self.txt_mesh.setStyleSheet(_FIELD_STYLE)
        self.txt_mesh.setReadOnly(True)
        lbl_mesh_icon = QLabel("📁")
        lbl_mesh_icon.setStyleSheet("border: none; font-size: 13px;")
        mesh_row.addWidget(self.txt_mesh)
        mesh_row.addWidget(lbl_mesh_icon)
        mesh_widget = QWidget()
        mesh_widget.setLayout(mesh_row)
        lbl_mesh = _row_label("Mesh")
        form.addRow(lbl_mesh, mesh_widget)

        # Material
        mat_row = QHBoxLayout()
        mat_row.setSpacing(4)
        self.cb_material = QComboBox()
        self.cb_material.setStyleSheet(
            "QComboBox {"
            "  background: #0f1117; border: 1px solid #2a2d3a;"
            "  border-radius: 4px; padding: 3px 8px; color: #c9cdd6; font-size: 11px;"
            "}"
            "QComboBox::drop-down { border: none; }"
        )
        self.cb_material.addItems(["Default_Material", "Unlit_Material", "Transparent_Material"])
        idx = self.cb_material.findText(str(material_name))
        if idx >= 0:
            self.cb_material.setCurrentIndex(idx)
        lbl_color = QLabel("⬤")
        lbl_color.setStyleSheet("border: none; color: #6b7280; font-size: 13px;")
        mat_row.addWidget(self.cb_material)
        mat_row.addWidget(lbl_color)
        mat_widget = QWidget()
        mat_widget.setLayout(mat_row)
        form.addRow(_row_label("Material"), mat_widget)


# ─────────────────────────────────────────────────────────────────────────────
# Box / Circle Collider
# ─────────────────────────────────────────────────────────────────────────────

class ColliderComponentWidget(QWidget):
    """Editor para BoxCollider e CircleCollider."""

    def __init__(self, viewmodel: SceneViewModel, collider, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.viewmodel = viewmodel
        self.collider = collider

        vbox = QGridLayout(self)
        vbox.setContentsMargins(0, 4, 0, 4)
        vbox.setSpacing(6)
        vbox.setColumnStretch(0, 0)
        for c in (1, 2, 3):
            vbox.setColumnStretch(c, 1)

        row = 0

        # Checkbox "Editar Collider"
        self.chk_edit = QCheckBox("Editar Collider")
        self.chk_edit.setStyleSheet("color: #9ca3af; font-size: 11px;")
        self.chk_edit.setChecked(False)
        vbox.addWidget(self.chk_edit, row, 0, 1, 4)
        row += 1

        if isinstance(collider, BoxCollider):
            # Centro X Y Z
            _xyz_header(vbox, col_offset=1)
            # (reutiliza row 0 do header via row já incrementado)
            # Ajusta: o _xyz_header usa row=0 internamente mas estamos na row certa
            # Precisamos de um grid separado para o header
            # Alternativa: reiniciar com QWidget interno
            pass

            # Cabeçalho XYZ inline
            for col, txt, style in ((1, "X", _LABEL_X), (2, "Y", _LABEL_Y), (3, "Z", _LABEL_Z)):
                lbl = QLabel(txt)
                lbl.setAlignment(Qt.AlignCenter)
                lbl.setStyleSheet(style)
                vbox.addWidget(lbl, row, col)
            row += 1

            # Centro
            cx = getattr(collider, "offset_x", 0.0)
            cy = getattr(collider, "offset_y", 0.9)
            cz = 0.0
            vbox.addWidget(_row_label("Centro"), row, 0)
            self.sb_cx = _dsb(cx)
            self.sb_cy = _dsb(cy)
            self.sb_cz = _dsb(cz)
            vbox.addWidget(self.sb_cx, row, 1)
            vbox.addWidget(self.sb_cy, row, 2)
            vbox.addWidget(self.sb_cz, row, 3)
            row += 1

            # Tamanho
            vbox.addWidget(_row_label("Tamanho"), row, 0)
            self.sb_w = _dsb(float(getattr(collider, "width", 1.0)))
            self.sb_h = _dsb(float(getattr(collider, "height", 1.8)))
            self.sb_d = _dsb(0.6)
            vbox.addWidget(self.sb_w, row, 1)
            vbox.addWidget(self.sb_h, row, 2)
            vbox.addWidget(self.sb_d, row, 3)

            self.sb_w.valueChanged.connect(lambda v: viewmodel.set_collider_property("width", v))
            self.sb_h.valueChanged.connect(lambda v: viewmodel.set_collider_property("height", v))

        elif isinstance(collider, CircleCollider):
            form = QFormLayout()
            form.setContentsMargins(0, 0, 0, 0)
            form.setSpacing(6)
            self.sb_r = _dsb(float(getattr(collider, "radius", 0.5)))
            form.addRow(_row_label("Raio"), self.sb_r)
            self.sb_r.valueChanged.connect(lambda v: viewmodel.set_collider_property("radius", v))
            vbox.addLayout(form, row, 0, 1, 4)

        # Is Trigger (oculto mas mantido para compatibilidade)
        self.chk_trigger = QCheckBox()
        self.chk_trigger.setChecked(getattr(collider, "is_trigger", False))
        self.chk_trigger.setVisible(False)
        self.chk_trigger.toggled.connect(lambda v: viewmodel.set_collider_property("is_trigger", v))


# ─────────────────────────────────────────────────────────────────────────────
# RigidBody
# ─────────────────────────────────────────────────────────────────────────────

class RigidBodyComponentWidget(QWidget):
    def __init__(self, viewmodel: SceneViewModel, rb: RigidBody, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.viewmodel = viewmodel
        self.rb = rb

        form = QFormLayout(self)
        form.setContentsMargins(0, 4, 0, 4)
        form.setSpacing(8)

        self.sb_mass = _dsb(self.rb.mass, step=0.1)
        self.sb_grav = _dsb(self.rb.gravity_scale, step=0.1)
        self.chk_kin = QCheckBox()
        self.chk_kin.setChecked(self.rb.is_kinematic)
        self.chk_kin.setStyleSheet("color: #9ca3af; font-size: 11px;")

        form.addRow(_row_label("Massa"), self.sb_mass)
        form.addRow(_row_label("Escala Gravidade"), self.sb_grav)
        form.addRow(_row_label("Cinemático"), self.chk_kin)

        self.sb_mass.valueChanged.connect(lambda v: viewmodel.set_rigidbody_property("mass", v))
        self.sb_grav.valueChanged.connect(lambda v: viewmodel.set_rigidbody_property("gravity_scale", v))
        self.chk_kin.toggled.connect(lambda v: viewmodel.set_rigidbody_property("is_kinematic", v))


# ─────────────────────────────────────────────────────────────────────────────
# Script
# ─────────────────────────────────────────────────────────────────────────────

class ScriptComponentWidget(QWidget):
    """Exibe o script e propriedades customizadas exportadas."""

    def __init__(self, viewmodel: SceneViewModel, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.viewmodel = viewmodel
        self.obj = viewmodel.selected_object

        form = QFormLayout(self)
        form.setContentsMargins(0, 4, 0, 4)
        form.setSpacing(8)
        form.setLabelAlignment(Qt.AlignLeft)

        # Campo de script (somente leitura + ícone)
        script_row = QHBoxLayout()
        script_row.setSpacing(4)
        current_script = getattr(self.obj, "script_path", "") or ""
        script_display = current_script.split("/")[-1] if current_script else "Nenhum"
        self.lbl_script_file = QLineEdit(script_display)
        self.lbl_script_file.setReadOnly(True)
        self.lbl_script_file.setStyleSheet(_FIELD_STYLE)
        lbl_icon = QLabel("📄")
        lbl_icon.setStyleSheet("border: none; font-size: 13px;")
        script_row.addWidget(self.lbl_script_file)
        script_row.addWidget(lbl_icon)
        script_widget = QWidget()
        script_widget.setLayout(script_row)
        form.addRow(_row_label("Script"), script_widget)

        # Propriedades customizadas exportadas
        exported = getattr(self.obj, "exported_properties", {}) or {}
        if not exported and current_script:
            # Valores de demonstração baseados em nomes comuns
            exported = {"Velocidade": 5.0, "Pulo": 10.0}

        self._prop_spinboxes: dict[str, QDoubleSpinBox] = {}
        for prop_name, prop_val in exported.items():
            try:
                sb = _dsb(float(prop_val), step=0.5, decimals=2)
            except (TypeError, ValueError):
                continue
            lbl = _row_label(prop_name)
            form.addRow(lbl, sb)
            self._prop_spinboxes[prop_name] = sb

        # Botões
        btn_row = QHBoxLayout()
        btn_row.setSpacing(6)
        self.btn_edit = QPushButton("Editar Script")
        self.btn_edit.setEnabled(bool(current_script and current_script != "Nenhum"))
        self.btn_edit.setStyleSheet(
            "QPushButton { background: #1e2130; border: 1px solid #2a2d3a; "
            "border-radius: 4px; color: #9ca3af; padding: 4px 10px; font-size: 11px; }"
            "QPushButton:hover { background: #252839; color: #d1d5db; }"
        )
        self.btn_edit.clicked.connect(self._edit_script)
        btn_row.addWidget(self.btn_edit)
        btn_row.addStretch()
        form.addRow("", btn_row)

    def refresh_scripts_list(self) -> None:
        pass  # Kept for backward-compat with inspector_dock

    def _edit_script(self) -> None:
        script = getattr(self.obj, "script_path", "")
        if not script or script == "Nenhum":
            return
        win = self.window()
        if win and hasattr(win, "dock_code_editor"):
            win.dock_code_editor.open_file(script)
