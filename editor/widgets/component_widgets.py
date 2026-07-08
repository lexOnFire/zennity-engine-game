from __future__ import annotations

import os
import re
from typing import Any

from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QCheckBox,
    QColorDialog,
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from engine.game_object import GameObject
from engine.physics.rigidbody import RigidBody
from editor.viewmodels.scene_viewmodel import SceneViewModel


# ---------------------------------------------------------------------------
# Helpers compartilhados
# ---------------------------------------------------------------------------

def create_spin_box(val: float, is_double: bool = True) -> QWidget:
    """Cria e formata um spin box escuro de alta precisão com localidade C neutra."""
    from PySide6.QtCore import QLocale
    if is_double:
        sb = QDoubleSpinBox()
        sb.setRange(-999999.0, 999999.0)
        sb.setSingleStep(1.0)
        sb.setDecimals(2)
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


def validate_and_get_value(sb) -> float | int | None:
    """Valida a entrada do spinbox, revertendo para original_value em caso de erro."""
    import math
    try:
        text = sb.cleanText().strip()
        if not text:
            sb.setValue(sb.original_value)
            return None
        try:
            float(text.replace(",", "."))
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


def _create_xyz_row(
    label_text: str,
    sb_x: QWidget,
    sb_y: QWidget,
    sb_z: QWidget | None = None,
) -> QHBoxLayout:
    """Linha X Y (Z opcional) com label à esquerda."""
    row = QHBoxLayout()
    row.setSpacing(6)
    lbl = QLabel(label_text)
    lbl.setFixedWidth(55)
    lbl.setStyleSheet("color: #8c8c8c; font-size: 11px;")
    row.addWidget(lbl)
    for axis_label, sb in (("X", sb_x), ("Y", sb_y), ("Z", sb_z)):
        if sb is None:
            continue
        lay = QHBoxLayout()
        lay.setSpacing(2)
        lbl_axis = QLabel(axis_label)
        lbl_axis.setStyleSheet("color: #808080; font-size: 10px;")
        lay.addWidget(lbl_axis)
        lay.addWidget(sb)
        row.addLayout(lay, 1)
    return row


# ---------------------------------------------------------------------------
# Transform
# ---------------------------------------------------------------------------

class TransformComponentWidget(QWidget):
    """Editor gráfico das propriedades do Transform (posição, rotação e escala)."""

    def __init__(self, viewmodel: SceneViewModel, parent: QWidget = None) -> None:
        super().__init__(parent)
        self.viewmodel = viewmodel
        self.obj = self.viewmodel.selected_object

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 4)
        layout.setSpacing(6)

        self.sb_pos_x = create_spin_box(self.obj.transform.position[0])
        self.sb_pos_y = create_spin_box(self.obj.transform.position[1])
        self.sb_pos_z = create_spin_box(self.obj.transform.position[2])
        self.sb_pos_z.setEnabled(False)
        layout.addLayout(_create_xyz_row("Posição", self.sb_pos_x, self.sb_pos_y, self.sb_pos_z))

        self.sb_rot_x = create_spin_box(self.obj.transform.rotation[0])
        self.sb_rot_x.setEnabled(False)
        self.sb_rot_y = create_spin_box(self.obj.transform.rotation[1])
        self.sb_rot_y.setEnabled(False)
        self.sb_rot_z = create_spin_box(self.obj.transform.rotation[2])
        layout.addLayout(_create_xyz_row("Rotação", self.sb_rot_x, self.sb_rot_y, self.sb_rot_z))

        self.sb_sc_x = create_spin_box(self.obj.transform.scale[0])
        self.sb_sc_y = create_spin_box(self.obj.transform.scale[1])
        self.sb_sc_z = create_spin_box(self.obj.transform.scale[2])
        self.sb_sc_z.setEnabled(False)
        layout.addLayout(_create_xyz_row("Escala", self.sb_sc_x, self.sb_sc_y, self.sb_sc_z))

        for attr, sb in [
            ("pos_x", self.sb_pos_x), ("pos_y", self.sb_pos_y), ("pos_z", self.sb_pos_z),
            ("rot_x", self.sb_rot_x), ("rot_y", self.sb_rot_y), ("rot_z", self.sb_rot_z),
            ("sc_x",  self.sb_sc_x),  ("sc_y",  self.sb_sc_y),  ("sc_z",  self.sb_sc_z),
        ]:
            prop, idx = ("position", 0) if attr.startswith("pos") else \
                        ("rotation", 0) if attr.startswith("rot") else ("scale", 0)
            idx = int(attr[-1].replace("x", "0").replace("y", "1").replace("z", "2"))
            prop = "position" if attr.startswith("pos") else \
                   "rotation" if attr.startswith("rot") else "scale"
            sb.original_value = float(getattr(self.obj.transform, prop)[idx])
            sb.valueChanged.connect(
                lambda val, p=prop, i=idx: self._on_value_changed(p, i, val)
            )
            sb.editingFinished.connect(
                lambda s=sb, p=prop, i=idx: self.commit_val(s, p, i)
            )
        self._block_original_sync = False

    def _on_value_changed(self, prop: str, idx: int, val: float) -> None:
        self._block_original_sync = True
        try:
            self.viewmodel.set_transform_property(prop, idx, val)
        finally:
            self._block_original_sync = False

    def commit_val(self, sb: QDoubleSpinBox, prop: str, idx: int) -> None:
        if not self.viewmodel or not self.viewmodel.selected_object:
            return
        val = validate_and_get_value(sb)
        if val is None:
            return
        new_val = float(val)
        old_val = float(getattr(sb, "original_value", new_val))
        if old_val != new_val:
            self.viewmodel.commit_transform_property(prop, idx, old_val, new_val)
            sb.original_value = new_val


# ---------------------------------------------------------------------------
# MeshRenderer
# ---------------------------------------------------------------------------

class MeshRendererComponentWidget(QWidget):
    """Widget visual para o Mesh Renderer."""

    def __init__(self, obj: GameObject, parent: QWidget = None) -> None:
        super().__init__(parent)
        self.obj = obj
        layout = QGridLayout(self)
        layout.setContentsMargins(0, 4, 0, 4)
        layout.setSpacing(6)

        lbl_mesh = QLabel("Mesh")
        lbl_mesh.setStyleSheet("color: #8c8c8c;")
        layout.addWidget(lbl_mesh, 0, 0)

        mesh_row = QHBoxLayout()
        self.txt_mesh = QLineEdit(f"📄 {getattr(self.obj, 'mesh_type', 'Character')}.fbx")
        self.txt_mesh.setReadOnly(True)
        self.txt_mesh.setStyleSheet("background-color: #202020; color: #a0a0a0; padding: 4px; border: 1px solid #151515;")
        btn_locate = QPushButton("⚙️")
        btn_locate.setFixedWidth(20)
        btn_locate.setStyleSheet("padding: 2px; background-color: #2b2b2b;")
        mesh_row.addWidget(self.txt_mesh)
        mesh_row.addWidget(btn_locate)
        layout.addLayout(mesh_row, 0, 1)

        lbl_mat = QLabel("Material")
        lbl_mat.setStyleSheet("color: #8c8c8c;")
        layout.addWidget(lbl_mat, 1, 0)

        mat_row = QHBoxLayout()
        self.cb_material = QComboBox()
        self.cb_material.addItems(["Default_Material", "Metalic_Material", "Smooth_Material"])
        btn_mat = QPushButton("⚙️")
        btn_mat.setFixedWidth(20)
        btn_mat.setStyleSheet("padding: 2px; background-color: #2b2b2b;")
        mat_row.addWidget(self.cb_material, 1)
        mat_row.addWidget(btn_mat)
        layout.addLayout(mat_row, 1, 1)


# ---------------------------------------------------------------------------
# SpriteRenderer (refatorado com campos válidos)
# ---------------------------------------------------------------------------

class SpriteRendererComponentWidget(QWidget):
    """Editor do SpriteRenderer 2D.

    Campos:
    - Source Sprite (asset UUID drag-drop ou seleção)
    - Color (RGBA via picker)
    - Flip X / Flip Y
    - Sorting Layer
    - Order in Layer
    """

    def __init__(
        self,
        component: Any,
        command_manager: Any,
        refresh_cb,
        parent: QWidget = None,
    ) -> None:
        super().__init__(parent)
        self._comp = component
        self._cm = command_manager
        self._refresh = refresh_cb

        layout = QFormLayout(self)
        layout.setContentsMargins(0, 4, 0, 4)
        layout.setSpacing(6)

        # Source Sprite
        sprite_row = QHBoxLayout()
        self._txt_sprite = QLineEdit(str(getattr(component, "sprite_path", "") or ""))
        self._txt_sprite.setPlaceholderText("Arraste um sprite aqui...")
        self._txt_sprite.setAcceptDrops(True)
        self._txt_sprite.editingFinished.connect(self._on_sprite_changed)
        btn_pick_sprite = QPushButton("📂")
        btn_pick_sprite.setFixedWidth(24)
        btn_pick_sprite.setStyleSheet("padding: 2px; background-color: #2b2b2b;")
        btn_pick_sprite.clicked.connect(self._pick_sprite)
        sprite_row.addWidget(self._txt_sprite, 1)
        sprite_row.addWidget(btn_pick_sprite)
        layout.addRow("Source Sprite", sprite_row)

        # Color
        color_row = QHBoxLayout()
        rgba = getattr(component, "color", (255, 255, 255, 255))
        if not isinstance(rgba, (list, tuple)) or len(rgba) < 3:
            rgba = (255, 255, 255, 255)
        self._color = list(rgba) + [255] * (4 - len(rgba))
        self._btn_color = QPushButton()
        self._btn_color.setFixedSize(24, 20)
        self._btn_color.setStyleSheet(
            f"background-color: rgba({self._color[0]},{self._color[1]},{self._color[2]},{self._color[3]});"
            " border: 1px solid #444;"
        )
        self._btn_color.clicked.connect(self._pick_color)
        color_row.addWidget(self._btn_color)
        for i, ch in enumerate(("R", "G", "B", "A")):
            sb = QSpinBox()
            sb.setRange(0, 255)
            sb.setValue(int(self._color[i]))
            sb.setFixedWidth(46)
            sb.valueChanged.connect(lambda v, idx=i: self._on_channel_changed(idx, v))
            color_row.addWidget(QLabel(ch))
            color_row.addWidget(sb)
        layout.addRow("Color", color_row)

        # Flip X / Y
        flip_row = QHBoxLayout()
        self._chk_flip_x = QCheckBox("X")
        self._chk_flip_x.setChecked(bool(getattr(component, "flip_x", False)))
        self._chk_flip_x.clicked.connect(lambda v: self._set_prop("flip_x", v))
        self._chk_flip_y = QCheckBox("Y")
        self._chk_flip_y.setChecked(bool(getattr(component, "flip_y", False)))
        self._chk_flip_y.clicked.connect(lambda v: self._set_prop("flip_y", v))
        flip_row.addWidget(self._chk_flip_x)
        flip_row.addWidget(self._chk_flip_y)
        flip_row.addStretch()
        layout.addRow("Flip", flip_row)

        # Sorting Layer
        self._cb_sort_layer = QComboBox()
        self._cb_sort_layer.addItems(["Default", "Background", "Midground", "Foreground", "UI"])
        self._cb_sort_layer.setCurrentText(
            str(getattr(component, "sorting_layer", "Default"))
        )
        self._cb_sort_layer.currentTextChanged.connect(
            lambda v: self._set_prop("sorting_layer", v)
        )
        layout.addRow("Sorting Layer", self._cb_sort_layer)

        # Order in Layer
        self._sb_order = create_spin_box(getattr(component, "order_in_layer", 0), is_double=False)
        self._sb_order.original_value = int(getattr(component, "order_in_layer", 0))
        self._sb_order.editingFinished.connect(self._commit_order)
        layout.addRow("Order in Layer", self._sb_order)

    def _set_prop(self, name: str, value: Any) -> None:
        old = getattr(self._comp, name, None)
        if old == value:
            return
        def apply(v=value): setattr(self._comp, name, v)
        def undo(v=old): setattr(self._comp, name, v)
        if self._cm:
            from editor.runtime.command_manager import FunctionCommand
            self._cm.execute(FunctionCommand(f"SpriteRenderer.{name}", apply, undo))
        else:
            apply()

    def _on_sprite_changed(self) -> None:
        self._set_prop("sprite_path", self._txt_sprite.text().strip())

    def _pick_sprite(self) -> None:
        from PySide6.QtWidgets import QFileDialog
        path, _ = QFileDialog.getOpenFileName(
            self, "Selecionar Sprite", "",
            "Imagens (*.png *.jpg *.jpeg *.bmp *.gif)"
        )
        if path:
            self._txt_sprite.setText(path)
            self._set_prop("sprite_path", path)

    def _on_channel_changed(self, idx: int, val: int) -> None:
        self._color[idx] = val
        self._btn_color.setStyleSheet(
            f"background-color: rgba({self._color[0]},{self._color[1]},{self._color[2]},{self._color[3]});"
            " border: 1px solid #444;"
        )
        self._set_prop("color", tuple(self._color))

    def _pick_color(self) -> None:
        initial = QColor(*self._color[:4])
        picked = QColorDialog.getColor(initial, self, "Cor do Sprite", QColorDialog.ShowAlphaChannel)
        if picked.isValid():
            self._color = [picked.red(), picked.green(), picked.blue(), picked.alpha()]
            self._btn_color.setStyleSheet(
                f"background-color: rgba({self._color[0]},{self._color[1]},{self._color[2]},{self._color[3]});"
                " border: 1px solid #444;"
            )
            self._set_prop("color", tuple(self._color))

    def _commit_order(self) -> None:
        val = validate_and_get_value(self._sb_order)
        if val is None:
            return
        new_val = int(val)
        old_val = int(getattr(self._sb_order, "original_value", new_val))
        if old_val != new_val:
            self._set_prop("order_in_layer", new_val)
            self._sb_order.original_value = new_val


# ---------------------------------------------------------------------------
# Image (componente UI)
# ---------------------------------------------------------------------------

class ImageComponentWidget(QWidget):
    """Editor do componente Image (UI Canvas).

    Campos:
    - Source Image (asset UUID / path)
    - Color (RGBA)
    - Raycast Target
    - Preserve Aspect
    """

    def __init__(
        self,
        component: Any,
        command_manager: Any,
        refresh_cb,
        parent: QWidget = None,
    ) -> None:
        super().__init__(parent)
        self._comp = component
        self._cm = command_manager
        self._refresh = refresh_cb

        layout = QFormLayout(self)
        layout.setContentsMargins(0, 4, 0, 4)
        layout.setSpacing(6)

        # Source Image
        img_row = QHBoxLayout()
        self._txt_image = QLineEdit(str(getattr(component, "source_image", "") or ""))
        self._txt_image.setPlaceholderText("Arraste uma imagem aqui...")
        self._txt_image.editingFinished.connect(
            lambda: self._set_prop("source_image", self._txt_image.text().strip())
        )
        btn_pick = QPushButton("📂")
        btn_pick.setFixedWidth(24)
        btn_pick.setStyleSheet("padding: 2px; background-color: #2b2b2b;")
        btn_pick.clicked.connect(self._pick_image)
        img_row.addWidget(self._txt_image, 1)
        img_row.addWidget(btn_pick)
        layout.addRow("Source Image", img_row)

        # Color
        color_row = QHBoxLayout()
        rgba = getattr(component, "color", (255, 255, 255, 255))
        if not isinstance(rgba, (list, tuple)) or len(rgba) < 3:
            rgba = (255, 255, 255, 255)
        self._color = list(rgba) + [255] * (4 - len(rgba))
        self._btn_color = QPushButton()
        self._btn_color.setFixedSize(24, 20)
        self._btn_color.setStyleSheet(
            f"background-color: rgba({self._color[0]},{self._color[1]},{self._color[2]},{self._color[3]});"
            " border: 1px solid #444;"
        )
        self._btn_color.clicked.connect(self._pick_color)
        color_row.addWidget(self._btn_color)
        for i, ch in enumerate(("R", "G", "B", "A")):
            sb = QSpinBox()
            sb.setRange(0, 255)
            sb.setValue(int(self._color[i]))
            sb.setFixedWidth(46)
            sb.valueChanged.connect(lambda v, idx=i: self._on_channel_changed(idx, v))
            color_row.addWidget(QLabel(ch))
            color_row.addWidget(sb)
        layout.addRow("Color", color_row)

        # Raycast Target
        self._chk_raycast = QCheckBox()
        self._chk_raycast.setChecked(bool(getattr(component, "raycast_target", True)))
        self._chk_raycast.clicked.connect(
            lambda v: self._set_prop("raycast_target", v)
        )
        layout.addRow("Raycast Target", self._chk_raycast)

        # Preserve Aspect
        self._chk_aspect = QCheckBox()
        self._chk_aspect.setChecked(bool(getattr(component, "preserve_aspect", False)))
        self._chk_aspect.clicked.connect(
            lambda v: self._set_prop("preserve_aspect", v)
        )
        layout.addRow("Preserve Aspect", self._chk_aspect)

    def _set_prop(self, name: str, value: Any) -> None:
        old = getattr(self._comp, name, None)
        if old == value:
            return
        def apply(v=value): setattr(self._comp, name, v)
        def undo(v=old): setattr(self._comp, name, v)
        if self._cm:
            from editor.runtime.command_manager import FunctionCommand
            self._cm.execute(FunctionCommand(f"Image.{name}", apply, undo))
        else:
            apply()

    def _pick_image(self) -> None:
        from PySide6.QtWidgets import QFileDialog
        path, _ = QFileDialog.getOpenFileName(
            self, "Selecionar Imagem", "",
            "Imagens (*.png *.jpg *.jpeg *.bmp *.gif *.svg)"
        )
        if path:
            self._txt_image.setText(path)
            self._set_prop("source_image", path)

    def _on_channel_changed(self, idx: int, val: int) -> None:
        self._color[idx] = val
        self._btn_color.setStyleSheet(
            f"background-color: rgba({self._color[0]},{self._color[1]},{self._color[2]},{self._color[3]});"
            " border: 1px solid #444;"
        )
        self._set_prop("color", tuple(self._color))

    def _pick_color(self) -> None:
        initial = QColor(*self._color[:4])
        picked = QColorDialog.getColor(initial, self, "Cor da Imagem", QColorDialog.ShowAlphaChannel)
        if picked.isValid():
            self._color = [picked.red(), picked.green(), picked.blue(), picked.alpha()]
            self._btn_color.setStyleSheet(
                f"background-color: rgba({self._color[0]},{self._color[1]},{self._color[2]},{self._color[3]});"
                " border: 1px solid #444;"
            )
            self._set_prop("color", tuple(self._color))


# ---------------------------------------------------------------------------
# Animator
# ---------------------------------------------------------------------------

class AnimatorComponentWidget(QWidget):
    """Editor do componente Animator.

    Campos:
    - Controller (asset UUID / path do AnimatorController)
    - Apply Root Motion
    - Update Mode (Normal / Animate Physics / Unscaled Time)
    - Parâmetros (nome, tipo, valor padrão)
    """

    _UPDATE_MODES = ["Normal", "Animate Physics", "Unscaled Time"]

    def __init__(
        self,
        component: Any,
        command_manager: Any,
        refresh_cb,
        parent: QWidget = None,
    ) -> None:
        super().__init__(parent)
        self._comp = component
        self._cm = command_manager
        self._refresh = refresh_cb

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 4)
        layout.setSpacing(6)

        form = QFormLayout()
        form.setSpacing(6)

        # Controller
        ctrl_row = QHBoxLayout()
        self._txt_ctrl = QLineEdit(
            str(getattr(component, "controller_path", "") or "")
        )
        self._txt_ctrl.setPlaceholderText("Arraste um AnimatorController...")
        self._txt_ctrl.editingFinished.connect(
            lambda: self._set_prop("controller_path", self._txt_ctrl.text().strip())
        )
        btn_pick_ctrl = QPushButton("📂")
        btn_pick_ctrl.setFixedWidth(24)
        btn_pick_ctrl.setStyleSheet("padding: 2px; background-color: #2b2b2b;")
        btn_pick_ctrl.clicked.connect(self._pick_controller)
        ctrl_row.addWidget(self._txt_ctrl, 1)
        ctrl_row.addWidget(btn_pick_ctrl)
        form.addRow("Controller", ctrl_row)

        # Apply Root Motion
        self._chk_root_motion = QCheckBox()
        self._chk_root_motion.setChecked(
            bool(getattr(component, "apply_root_motion", False))
        )
        self._chk_root_motion.clicked.connect(
            lambda v: self._set_prop("apply_root_motion", v)
        )
        form.addRow("Apply Root Motion", self._chk_root_motion)

        # Update Mode
        self._cb_update = QComboBox()
        self._cb_update.addItems(self._UPDATE_MODES)
        self._cb_update.setCurrentText(
            str(getattr(component, "update_mode", "Normal"))
        )
        self._cb_update.currentTextChanged.connect(
            lambda v: self._set_prop("update_mode", v)
        )
        form.addRow("Update Mode", self._cb_update)

        layout.addLayout(form)

        # Seção de parâmetros
        lbl_params = QLabel("Parâmetros")
        lbl_params.setStyleSheet("color: #8c8c8c; font-size: 10px; margin-top: 4px;")
        layout.addWidget(lbl_params)

        self._params_container = QWidget()
        self._params_layout = QVBoxLayout(self._params_container)
        self._params_layout.setContentsMargins(0, 0, 0, 0)
        self._params_layout.setSpacing(3)
        layout.addWidget(self._params_container)
        self._rebuild_params()

        btn_add_param = QPushButton("+ Parâmetro")
        btn_add_param.setStyleSheet(
            "background-color: #2b2b2b; font-size: 10px; padding: 3px;"
        )
        btn_add_param.clicked.connect(self._add_param)
        layout.addWidget(btn_add_param)

    def _set_prop(self, name: str, value: Any) -> None:
        old = getattr(self._comp, name, None)
        if old == value:
            return
        def apply(v=value): setattr(self._comp, name, v)
        def undo(v=old): setattr(self._comp, name, v)
        if self._cm:
            from editor.runtime.command_manager import FunctionCommand
            self._cm.execute(FunctionCommand(f"Animator.{name}", apply, undo))
        else:
            apply()

    def _pick_controller(self) -> None:
        from PySide6.QtWidgets import QFileDialog
        path, _ = QFileDialog.getOpenFileName(
            self, "Selecionar AnimatorController", "",
            "Animator Controller (*.anim *.json *.yaml *.yml)"
        )
        if path:
            self._txt_ctrl.setText(path)
            self._set_prop("controller_path", path)

    def _get_params(self) -> list[dict]:
        return list(getattr(self._comp, "parameters", []) or [])

    def _rebuild_params(self) -> None:
        while self._params_layout.count():
            item = self._params_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for i, param in enumerate(self._get_params()):
            row = QHBoxLayout()
            row.setSpacing(4)

            name_edit = QLineEdit(str(param.get("name", f"param{i}")))
            name_edit.setFixedWidth(80)
            name_edit.setStyleSheet("background-color: #202020; color: #ccc; padding: 2px; font-size: 10px;")
            name_edit.editingFinished.connect(
                lambda idx=i, w=name_edit: self._update_param_name(idx, w.text())
            )

            type_cb = QComboBox()
            type_cb.addItems(["Float", "Int", "Bool", "Trigger"])
            type_cb.setCurrentText(str(param.get("type", "Float")))
            type_cb.setFixedWidth(60)
            type_cb.currentTextChanged.connect(
                lambda v, idx=i: self._update_param_type(idx, v)
            )

            val_edit = QLineEdit(str(param.get("value", "0")))
            val_edit.setFixedWidth(50)
            val_edit.setStyleSheet("background-color: #202020; color: #ccc; padding: 2px; font-size: 10px;")
            val_edit.editingFinished.connect(
                lambda idx=i, w=val_edit: self._update_param_value(idx, w.text())
            )

            btn_del = QPushButton("×")
            btn_del.setFixedSize(18, 18)
            btn_del.setStyleSheet("color: #884444; background: transparent; border: none; font-size: 12px;")
            btn_del.clicked.connect(lambda _, idx=i: self._remove_param(idx))

            row.addWidget(name_edit)
            row.addWidget(type_cb)
            row.addWidget(val_edit)
            row.addWidget(btn_del)

            row_widget = QWidget()
            row_widget.setLayout(row)
            self._params_layout.addWidget(row_widget)

    def _update_param_name(self, idx: int, name: str) -> None:
        params = self._get_params()
        if idx < len(params):
            params[idx] = {**params[idx], "name": name}
            self._set_prop("parameters", params)

    def _update_param_type(self, idx: int, ptype: str) -> None:
        params = self._get_params()
        if idx < len(params):
            params[idx] = {**params[idx], "type": ptype}
            self._set_prop("parameters", params)

    def _update_param_value(self, idx: int, val: str) -> None:
        params = self._get_params()
        if idx < len(params):
            params[idx] = {**params[idx], "value": val}
            self._set_prop("parameters", params)

    def _add_param(self) -> None:
        params = self._get_params()
        params.append({"name": f"param{len(params)}", "type": "Float", "value": "0"})
        self._set_prop("parameters", params)
        self._rebuild_params()

    def _remove_param(self, idx: int) -> None:
        params = self._get_params()
        if idx < len(params):
            params.pop(idx)
            self._set_prop("parameters", params)
            self._rebuild_params()


# ---------------------------------------------------------------------------
# RigidBody
# ---------------------------------------------------------------------------

class RigidBodyComponentWidget(QWidget):
    """Editor das propriedades de física do RigidBody."""

    def __init__(
        self, viewmodel: SceneViewModel, rb: RigidBody, parent: QWidget = None
    ) -> None:
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

        self.sb_mass.original_value = float(self.rb.mass)
        self.sb_grav.original_value = float(self.rb.gravity_scale)
        self._block_original_sync = False

        self.sb_mass.valueChanged.connect(lambda val: self._on_value_changed("mass", val))
        self.sb_grav.valueChanged.connect(lambda val: self._on_value_changed("gravity_scale", val))
        self.sb_mass.editingFinished.connect(lambda: self.commit_val(self.sb_mass, "mass"))
        self.sb_grav.editingFinished.connect(lambda: self.commit_val(self.sb_grav, "gravity_scale"))
        self.chk_kin.clicked.connect(self.commit_kinematic)

    def _on_value_changed(self, prop: str, val: float) -> None:
        self._block_original_sync = True
        try:
            self.viewmodel.set_rigidbody_property(prop, val)
        finally:
            self._block_original_sync = False

    def commit_val(self, sb: QDoubleSpinBox, prop: str) -> None:
        if not self.viewmodel or not self.viewmodel.selected_object:
            return
        val = validate_and_get_value(sb)
        if val is None:
            return
        new_val = float(val)
        old_val = float(getattr(sb, "original_value", new_val))
        if old_val != new_val:
            self.viewmodel.commit_rigidbody_property(prop, old_val, new_val)
            sb.original_value = new_val

    def commit_kinematic(self) -> None:
        if not self.viewmodel or not self.viewmodel.selected_object:
            return
        new_val = self.chk_kin.isChecked()
        self.viewmodel.commit_rigidbody_property("is_kinematic", not new_val, new_val)


# ---------------------------------------------------------------------------
# Collider
# ---------------------------------------------------------------------------

class ColliderComponentWidget(QWidget):
    """Editor para colisores 2D (BoxCollider e CircleCollider)."""

    def __init__(
        self, viewmodel: SceneViewModel, collider, parent: QWidget = None
    ) -> None:
        super().__init__(parent)
        self.viewmodel = viewmodel
        self.collider = collider

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 4)
        layout.setSpacing(6)

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

        self.sb_offset_x = create_spin_box(0.0)
        self.sb_offset_x.setEnabled(False)
        self.sb_offset_y = create_spin_box(0.0)
        self.sb_offset_y.setEnabled(False)
        self.sb_offset_z = create_spin_box(0.0)
        self.sb_offset_z.setEnabled(False)
        layout.addLayout(_create_xyz_row("Centro", self.sb_offset_x, self.sb_offset_y, self.sb_offset_z))

        if type(self.collider).__name__ == "BoxCollider":
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
            layout.addLayout(_create_xyz_row("Tamanho", self.sb_w, self.sb_h, self.sb_z))

        elif type(self.collider).__name__ == "CircleCollider":
            self.sb_r = create_spin_box(self.collider.radius, is_double=False)
            self.sb_r.setRange(1, 9999)
            self.sb_r.original_value = int(self.collider.radius)
            self.sb_r.valueChanged.connect(lambda val: self._on_value_changed("radius", val))
            self.sb_r.editingFinished.connect(lambda: self.commit_val(self.sb_r, "radius"))

            self.sb_r_y = create_spin_box(self.collider.radius, is_double=False)
            self.sb_r_y.setEnabled(False)
            self.sb_z = create_spin_box(1.00)
            self.sb_z.setEnabled(False)
            layout.addLayout(_create_xyz_row("Tamanho", self.sb_r, self.sb_r_y, self.sb_z))

    def _on_value_changed(self, prop: str, val: float) -> None:
        self._block_original_sync = True
        try:
            self.viewmodel.set_collider_property(prop, val)
        finally:
            self._block_original_sync = False

    def commit_val(self, sb, prop: str) -> None:
        if not self.viewmodel or not self.viewmodel.selected_object:
            return
        val = validate_and_get_value(sb)
        if val is None:
            return
        new_val = int(val)
        old_val = int(getattr(sb, "original_value", new_val))
        if old_val != new_val:
            self.viewmodel.commit_collider_property(prop, old_val, new_val)
            sb.original_value = new_val

    def commit_trigger(self) -> None:
        if not self.viewmodel or not self.viewmodel.selected_object:
            return
        new_val = self.chk_trigger.isChecked()
        self.viewmodel.commit_collider_property("is_trigger", not new_val, new_val)


# ---------------------------------------------------------------------------
# Script
# ---------------------------------------------------------------------------

from editor.core.script_manager import ScriptManager


class ScriptComponentWidget(QWidget):
    """Editor para associar e editar scripts de comportamento nos GameObjects."""

    def __init__(self, viewmodel: SceneViewModel, parent: QWidget = None) -> None:
        super().__init__(parent)
        self.viewmodel = viewmodel
        self.obj = self.viewmodel.selected_object

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 4, 0, 4)
        self.main_layout.setSpacing(6)

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

        self.vars_container = QWidget()
        self.vars_layout = QFormLayout(self.vars_container)
        self.vars_layout.setContentsMargins(0, 4, 0, 4)
        self.vars_layout.setSpacing(6)
        self.main_layout.addWidget(self.vars_container)
        self.update_dynamic_variables()

        self.btn_create = QPushButton("Criar Novo Script")
        self.btn_create.setStyleSheet("background-color: #2b2b2b; color: #a0a0a0; padding: 4px;")
        self.btn_create.clicked.connect(self.create_script)
        self.main_layout.addWidget(self.btn_create)

    def refresh_scripts_list(self) -> None:
        self.cb_scripts.clear()
        self.cb_scripts.addItems(ScriptManager.list_scripts())

    def update_dynamic_variables(self) -> None:
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
            matches = re.findall(
                r"(?:self|obj)\.([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*(-?[0-9]+(?:\.[0-9]+)?)",
                content,
            )
            seen: set[str] = set()
            for var_name, var_val in matches:
                if var_name in seen or var_name in {
                    "script_time", "script_module", "script_path"
                }:
                    continue
                seen.add(var_name)
                current_val = getattr(self.obj, var_name, float(var_val))
                setattr(self.obj, var_name, current_val)
                sb = create_spin_box(current_val)
                sb.setSingleStep(0.1)
                sb.valueChanged.connect(lambda val, name=var_name: setattr(self.obj, name, val))
                self.vars_layout.addRow(f"{var_name.capitalize()}:", sb)
        except Exception as exc:
            print(f"[Inspector] Erro ao analisar variáveis do script: {exc}")

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
