from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt, Slot
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QDockWidget, QFrame, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QScrollArea, QSizePolicy,
    QVBoxLayout, QWidget,
)

from engine.game_object import GameObject
from engine.physics.rigidbody import RigidBody
from engine.physics.collider import BoxCollider, CircleCollider
from editor.viewmodels.scene_viewmodel import SceneViewModel
from editor.widgets.collapsible_section import CollapsibleSection
from editor.widgets.component_widgets import (
    ColliderComponentWidget,
    MeshRendererWidget,
    RigidBodyComponentWidget,
    ScriptComponentWidget,
    TransformComponentWidget,
)


_BADGE_STYLE = (
    "background: #1e2130; border: 1px solid #374151; border-radius: 4px;"
    "color: #6b7280; padding: 1px 7px; font-size: 10px; font-weight: 600;"
)

_COMBO_STYLE = (
    "QComboBox {"
    "  background: #0f1117; border: 1px solid #2a2d3a;"
    "  border-radius: 4px; padding: 2px 8px; color: #9ca3af; font-size: 11px;"
    "}"
    "QComboBox::drop-down { border: none; }"
    "QComboBox QAbstractItemView { background: #1b1e27; color: #c9cdd6; }"
)

_ADD_BTN_STYLE = (
    "QPushButton {"
    "  background: #1b1e27; border: 1px solid #2a2d3a; border-radius: 6px;"
    "  color: #6b7280; padding: 7px 0; font-size: 12px; font-weight: 600;"
    "}"
    "QPushButton:hover { background: #252839; color: #9ca3af; border-color: #374151; }"
    "QPushButton:pressed { background: #1e2130; }"
)


class InspectorDock(QDockWidget):
    """Painel Inspector redesenhado conforme referência visual."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__("Inspector", parent)
        self.setObjectName("InspectorDock")
        self.setAllowedAreas(Qt.RightDockWidgetArea | Qt.LeftDockWidgetArea)

        self.viewmodel: Optional[SceneViewModel] = None
        self._block_updates = False

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.setStyleSheet("QScrollArea { background: #0d0f14; border: none; }")

        self.main_content = QWidget()
        self.main_content.setStyleSheet("background: #0d0f14;")
        self.layout_content = QVBoxLayout(self.main_content)
        self.layout_content.setContentsMargins(10, 10, 10, 10)
        self.layout_content.setSpacing(4)
        self.layout_content.setAlignment(Qt.AlignTop)

        self.scroll.setWidget(self.main_content)
        self.setWidget(self.scroll)

        self.show_empty_state()

    def set_viewmodel(self, viewmodel: SceneViewModel) -> None:
        self.viewmodel = viewmodel
        self.viewmodel.selection_changed.connect(self.on_selection_changed)
        self.viewmodel.property_changed.connect(self.on_property_changed)

    def show_empty_state(self) -> None:
        self.clear_layout()
        lbl = QLabel("Selecione um objeto para ver suas propriedades.")
        lbl.setStyleSheet("color: #374151; font-size: 11px;")
        lbl.setWordWrap(True)
        lbl.setAlignment(Qt.AlignCenter)
        self.layout_content.addWidget(lbl)

    def clear_layout(self) -> None:
        while self.layout_content.count():
            item = self.layout_content.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    # ─────────────────────────────────────────────────────────────────────────
    # Header
    # ─────────────────────────────────────────────────────────────────────────

    def _build_header(self, obj: GameObject) -> None:
        """Linha 1: checkbox ativo + nome + badge Estático | Linha 2: Tag / Layer."""

        # ── Linha 1 ──────────────────────────────────────────────────
        row1 = QWidget()
        row1.setStyleSheet("background: transparent;")
        h1 = QHBoxLayout(row1)
        h1.setContentsMargins(0, 0, 0, 2)
        h1.setSpacing(6)

        self.chk_active = QCheckBox()
        self.chk_active.setChecked(getattr(obj, "active", True))
        self.chk_active.setStyleSheet("QCheckBox { color: #9ca3af; }")

        self.txt_name = QLineEdit(obj.name)
        self.txt_name.setStyleSheet(
            "QLineEdit {"
            "  font-weight: 700; font-size: 14px; color: #f3f4f6;"
            "  background: transparent; border: none; padding: 2px 0;"
            "}"
            "QLineEdit:focus {"
            "  background: #1b1e27; border: 1px solid #3b82f6;"
            "  border-radius: 4px; padding: 2px 6px;"
            "}"
        )
        self.txt_name.editingFinished.connect(self._on_name_edited)

        lbl_static = QLabel("Estático")
        lbl_static.setStyleSheet(_BADGE_STYLE)

        h1.addWidget(self.chk_active)
        h1.addWidget(self.txt_name, 1)
        h1.addWidget(lbl_static)

        self.layout_content.addWidget(row1)

        # ── Linha 2: Tag / Layer ─────────────────────────────────────
        row2 = QWidget()
        row2.setStyleSheet("background: transparent;")
        h2 = QHBoxLayout(row2)
        h2.setContentsMargins(0, 0, 0, 6)
        h2.setSpacing(8)

        h2.addWidget(QLabel("Tag"))
        cb_tag = QComboBox()
        cb_tag.setStyleSheet(_COMBO_STYLE)
        cb_tag.addItems(["Untagged", "Player", "Enemy", "Ground", "Trigger"])
        tag_val = getattr(obj, "tag", "Player")
        idx = cb_tag.findText(str(tag_val))
        cb_tag.setCurrentIndex(idx if idx >= 0 else 0)
        h2.addWidget(cb_tag)

        h2.addSpacing(12)
        h2.addWidget(QLabel("Layer"))
        cb_layer = QComboBox()
        cb_layer.setStyleSheet(_COMBO_STYLE)
        cb_layer.addItems(["Default", "UI", "Background", "Foreground", "Player"])
        layer_val = getattr(obj, "layer", "Default")
        l_idx = cb_layer.findText(str(layer_val))
        cb_layer.setCurrentIndex(l_idx if l_idx >= 0 else 0)
        h2.addWidget(cb_layer)
        h2.addStretch()

        for lbl in row2.findChildren(QLabel):
            lbl.setStyleSheet("color: #6b7280; font-size: 11px; background: transparent;")

        self.layout_content.addWidget(row2)

        # Separador
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("background: #1f2330; border: none; max-height: 1px; margin: 2px 0 6px 0;")
        self.layout_content.addWidget(sep)

    # ─────────────────────────────────────────────────────────────────────────
    # Selection changed – rebuild all sections
    # ─────────────────────────────────────────────────────────────────────────

    @Slot(object)
    def on_selection_changed(self, obj: Optional[GameObject]) -> None:
        if not obj or not self.viewmodel:
            self.show_empty_state()
            return

        self._block_updates = True
        self.clear_layout()

        # Cabeçalho
        self._build_header(obj)

        # ── Transform ────────────────────────────────────────────────
        sec_tf = CollapsibleSection("Transform")
        self.transform_widget = TransformComponentWidget(self.viewmodel)
        sec_tf.set_content_widget(self.transform_widget)
        self.layout_content.addWidget(sec_tf)

        # ── Mesh Renderer ─────────────────────────────────────────────
        sec_mesh = CollapsibleSection("Mesh Renderer")
        self.mesh_widget = MeshRendererWidget(self.viewmodel)
        sec_mesh.set_content_widget(self.mesh_widget)
        self.layout_content.addWidget(sec_mesh)

        # ── Box / Circle Collider ─────────────────────────────────────
        bc = obj.get_component(BoxCollider)
        cc = obj.get_component(CircleCollider)
        if bc or cc:
            collider = bc if bc else cc
            type_name = "Box Collider" if bc else "Circle Collider"
            sec_col = CollapsibleSection(type_name)
            self.col_widget = ColliderComponentWidget(self.viewmodel, collider)
            sec_col.set_content_widget(self.col_widget)
            self.layout_content.addWidget(sec_col)

        # ── RigidBody ─────────────────────────────────────────────────
        rb = obj.get_component(RigidBody)
        if rb:
            sec_rb = CollapsibleSection("RigidBody")
            self.rb_widget = RigidBodyComponentWidget(self.viewmodel, rb)
            sec_rb.set_content_widget(self.rb_widget)
            self.layout_content.addWidget(sec_rb)

        # ── Script ────────────────────────────────────────────────────
        script_path = getattr(obj, "script_path", "") or ""
        script_label = obj.name
        if script_path:
            script_label = script_path.split("/")[-1].replace(".py", "")
        sec_script = CollapsibleSection(f"{script_label} (Script)", icon="📄")
        self.script_widget = ScriptComponentWidget(self.viewmodel)
        sec_script.set_content_widget(self.script_widget)
        self.layout_content.addWidget(sec_script)

        # ── Botão Adicionar Componente ────────────────────────────────
        self.btn_add = QPushButton("Adicionar Componente")
        self.btn_add.setStyleSheet(_ADD_BTN_STYLE)
        self.btn_add.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.layout_content.addSpacing(4)
        self.layout_content.addWidget(self.btn_add)

        self._block_updates = False

    # ─────────────────────────────────────────────────────────────────────────
    # Slots
    # ─────────────────────────────────────────────────────────────────────────

    @Slot()
    def _on_name_edited(self) -> None:
        if not self.viewmodel or not self.viewmodel.selected_object:
            return
        self.viewmodel.rename_object(self.viewmodel.selected_object, self.txt_name.text())

    # keep old name for backward-compat
    def on_name_edited(self) -> None:
        self._on_name_edited()

    @Slot(str, str, object)
    def on_property_changed(self, component_name: str, property_name: str, value: object) -> None:
        if self._block_updates or not self.viewmodel or not self.viewmodel.selected_object:
            return
        obj = self.viewmodel.selected_object

        if component_name == "Transform" and hasattr(self, "transform_widget"):
            w = self.transform_widget
            w.blockSignals(True)
            w.sb_pos_x.setValue(obj.transform.position[0])
            w.sb_pos_y.setValue(obj.transform.position[1])
            w.sb_pos_z.setValue(obj.transform.position[2])
            w.sb_rot_x.setValue(obj.transform.rotation[0])
            w.sb_rot_y.setValue(obj.transform.rotation[1])
            w.sb_rot_z.setValue(obj.transform.rotation[2])
            w.sb_sc_x.setValue(obj.transform.scale[0])
            w.sb_sc_y.setValue(obj.transform.scale[1])
            w.sb_sc_z.setValue(obj.transform.scale[2])
            w.blockSignals(False)

        elif component_name == "Collider" and hasattr(self, "col_widget"):
            cw = self.col_widget
            cw.blockSignals(True)
            bc = obj.get_component(BoxCollider)
            cc = obj.get_component(CircleCollider)
            if bc and hasattr(cw, "sb_w"):
                cw.sb_w.setValue(float(bc.width))
                cw.sb_h.setValue(float(bc.height))
            elif cc and hasattr(cw, "sb_r"):
                cw.sb_r.setValue(float(cc.radius))
            cw.blockSignals(False)

        elif component_name == "Script" and hasattr(self, "script_widget"):
            self.script_widget.refresh_scripts_list()
