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
    _f,
)


_BADGE_STYLE = (
    "background:#1e2130; border:1px solid #374151; border-radius:4px;"
    "color:#6b7280; padding:1px 7px; font-size:10px; font-weight:600;"
)
_COMBO_STYLE = (
    "QComboBox{background:#0f1117;border:1px solid #2a2d3a;border-radius:4px;"
    "padding:2px 8px;color:#9ca3af;font-size:11px;}"
    "QComboBox::drop-down{border:none;}"
    "QComboBox QAbstractItemView{background:#1b1e27;color:#c9cdd6;}"
)
_ADD_STYLE = (
    "QPushButton{background:#1b1e27;border:1px solid #2a2d3a;border-radius:6px;"
    "color:#6b7280;padding:7px 0;font-size:12px;font-weight:600;}"
    "QPushButton:hover{background:#252839;color:#9ca3af;border-color:#374151;}"
    "QPushButton:pressed{background:#1e2130;}"
)


class InspectorDock(QDockWidget):
    """Inspector redesenhado – spinboxes reais, sem texto NumPy cru."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__("Inspector", parent)
        self.setObjectName("InspectorDock")
        self.setAllowedAreas(Qt.RightDockWidgetArea | Qt.LeftDockWidgetArea)

        self.viewmodel: Optional[SceneViewModel] = None
        self._block_updates = False

        # Scroll area
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.setStyleSheet("QScrollArea{background:#0d0f14;border:none;}")

        self.main_content = QWidget()
        self.main_content.setStyleSheet("background:#0d0f14;")
        self.lc = QVBoxLayout(self.main_content)
        self.lc.setContentsMargins(10, 10, 10, 12)
        self.lc.setSpacing(4)
        self.lc.setAlignment(Qt.AlignTop)

        self.scroll.setWidget(self.main_content)
        self.setWidget(self.scroll)
        self._show_empty()

    # ── public ──────────────────────────────────────────────────────────────

    def set_viewmodel(self, viewmodel: SceneViewModel) -> None:
        self.viewmodel = viewmodel
        viewmodel.selection_changed.connect(self.on_selection_changed)
        viewmodel.property_changed.connect(self.on_property_changed)

    # ── helpers ─────────────────────────────────────────────────────────────

    def _show_empty(self) -> None:
        self._clear()
        lbl = QLabel("Selecione um objeto para ver suas propriedades.")
        lbl.setStyleSheet("color:#374151;font-size:11px;")
        lbl.setWordWrap(True)
        lbl.setAlignment(Qt.AlignCenter)
        self.lc.addWidget(lbl)

    def _clear(self) -> None:
        while self.lc.count():
            item = self.lc.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    # keep old names for any external callers
    def show_empty_state(self) -> None:
        self._show_empty()

    def clear_layout(self) -> None:
        self._clear()

    # ── header ──────────────────────────────────────────────────────────────

    def _build_header(self, obj: GameObject) -> None:
        # Row 1 – checkbox + name + Estático badge
        r1 = QWidget(); r1.setStyleSheet("background:transparent;")
        h1 = QHBoxLayout(r1)
        h1.setContentsMargins(0, 0, 0, 2); h1.setSpacing(6)

        self.chk_active = QCheckBox()
        self.chk_active.setChecked(getattr(obj, "active", True))
        self.chk_active.setStyleSheet("QCheckBox{color:#9ca3af;}")

        self.txt_name = QLineEdit(obj.name)
        self.txt_name.setStyleSheet(
            "QLineEdit{font-weight:700;font-size:14px;color:#f3f4f6;"
            "background:transparent;border:none;padding:2px 0;}"
            "QLineEdit:focus{background:#1b1e27;border:1px solid #3b82f6;"
            "border-radius:4px;padding:2px 6px;}"
        )
        self.txt_name.editingFinished.connect(self._on_name_edited)

        lbl_static = QLabel("Estático")
        lbl_static.setStyleSheet(_BADGE_STYLE)

        h1.addWidget(self.chk_active)
        h1.addWidget(self.txt_name, 1)
        h1.addWidget(lbl_static)
        self.lc.addWidget(r1)

        # Row 2 – Tag / Layer
        r2 = QWidget(); r2.setStyleSheet("background:transparent;")
        h2 = QHBoxLayout(r2)
        h2.setContentsMargins(0, 0, 0, 6); h2.setSpacing(6)

        def _lbl(t):
            l = QLabel(t)
            l.setStyleSheet("color:#6b7280;font-size:11px;background:transparent;")
            return l

        h2.addWidget(_lbl("Tag"))
        cb_tag = QComboBox(); cb_tag.setStyleSheet(_COMBO_STYLE)
        cb_tag.addItems(["Untagged","Player","Enemy","Ground","Trigger"])
        tag_val = str(getattr(obj, "tag", "Untagged"))
        cb_tag.setCurrentIndex(max(0, cb_tag.findText(tag_val)))
        h2.addWidget(cb_tag)

        h2.addSpacing(10)
        h2.addWidget(_lbl("Layer"))
        cb_layer = QComboBox(); cb_layer.setStyleSheet(_COMBO_STYLE)
        cb_layer.addItems(["Default","UI","Background","Foreground","Player"])
        layer_val = str(getattr(obj, "layer", "Default"))
        cb_layer.setCurrentIndex(max(0, cb_layer.findText(layer_val)))
        h2.addWidget(cb_layer)
        h2.addStretch()
        self.lc.addWidget(r2)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("background:#1f2330;border:none;max-height:1px;margin:2px 0 6px 0;")
        self.lc.addWidget(sep)

    # ── section builder ─────────────────────────────────────────────────────

    def _section(self, title: str, widget: QWidget, icon: str = "") -> CollapsibleSection:
        sec = CollapsibleSection(title, icon=icon)
        sec.set_content_widget(widget)
        return sec

    # ── selection changed ────────────────────────────────────────────────────

    @Slot(object)
    def on_selection_changed(self, obj: Optional[GameObject]) -> None:
        if not obj or not self.viewmodel:
            self._show_empty()
            return

        self._block_updates = True
        self._clear()

        self._build_header(obj)

        # Transform
        self.transform_widget = TransformComponentWidget(self.viewmodel)
        self.lc.addWidget(self._section("Transform", self.transform_widget))

        # Mesh Renderer
        self.mesh_widget = MeshRendererWidget(self.viewmodel)
        self.lc.addWidget(self._section("Mesh Renderer", self.mesh_widget))

        # Collider
        bc = obj.get_component(BoxCollider)
        cc = obj.get_component(CircleCollider)
        if bc or cc:
            collider  = bc if bc else cc
            type_name = "Box Collider" if bc else "Circle Collider"
            self.col_widget = ColliderComponentWidget(self.viewmodel, collider)
            self.lc.addWidget(self._section(type_name, self.col_widget))

        # RigidBody
        rb = obj.get_component(RigidBody)
        if rb:
            self.rb_widget = RigidBodyComponentWidget(self.viewmodel, rb)
            self.lc.addWidget(self._section("RigidBody", self.rb_widget))

        # Script
        script_path = getattr(obj, "script_path", "") or ""
        label = script_path.split("/")[-1].replace(".py", "") if script_path else obj.name
        self.script_widget = ScriptComponentWidget(self.viewmodel)
        self.lc.addWidget(self._section(f"{label} (Script)", self.script_widget, icon="📄"))

        # Adicionar Componente
        self.btn_add = QPushButton("Adicionar Componente")
        self.btn_add.setStyleSheet(_ADD_STYLE)
        self.btn_add.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.lc.addSpacing(4)
        self.lc.addWidget(self.btn_add)

        self._block_updates = False

    # ── property_changed ─────────────────────────────────────────────────────

    @Slot(str, str, object)
    def on_property_changed(self, comp: str, prop: str, value: object) -> None:
        if self._block_updates or not self.viewmodel or not self.viewmodel.selected_object:
            return
        obj = self.viewmodel.selected_object

        if comp == "Transform" and hasattr(self, "transform_widget"):
            w = self.transform_widget
            w.blockSignals(True)
            w.sb_pos_x.setValue(_f(obj.transform.position[0]))
            w.sb_pos_y.setValue(_f(obj.transform.position[1]))
            w.sb_pos_z.setValue(_f(obj.transform.position[2]))
            w.sb_rot_x.setValue(_f(obj.transform.rotation[0]))
            w.sb_rot_y.setValue(_f(obj.transform.rotation[1]))
            w.sb_rot_z.setValue(_f(obj.transform.rotation[2]))
            w.sb_sc_x.setValue(_f(obj.transform.scale[0]))
            w.sb_sc_y.setValue(_f(obj.transform.scale[1]))
            w.sb_sc_z.setValue(_f(obj.transform.scale[2]))
            w.blockSignals(False)

        elif comp == "Collider" and hasattr(self, "col_widget"):
            cw = self.col_widget
            cw.blockSignals(True)
            bc2 = obj.get_component(BoxCollider)
            cc2 = obj.get_component(CircleCollider)
            if bc2 and hasattr(cw, "sb_w"):
                cw.sb_w.setValue(_f(bc2.width))
                cw.sb_h.setValue(_f(bc2.height))
            elif cc2 and hasattr(cw, "sb_r"):
                cw.sb_r.setValue(_f(cc2.radius))
            cw.blockSignals(False)

        elif comp == "Script" and hasattr(self, "script_widget"):
            self.script_widget.refresh_scripts_list()

    # backward-compat aliases
    def on_name_edited(self) -> None:
        self._on_name_edited()

    @Slot()
    def _on_name_edited(self) -> None:
        if self.viewmodel and self.viewmodel.selected_object:
            self.viewmodel.rename_object(
                self.viewmodel.selected_object, self.txt_name.text()
            )
