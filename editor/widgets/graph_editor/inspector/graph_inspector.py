"""Graph Node Inspector — Item 3: Graph ↔ Inspector Sync.

Quando o usuário seleciona um nó no canvas, este widget:
  1. Exibe nome, categoria e descrição do nó (da NodeDefinition)
  2. Lista todos os pinos de INPUT com seus tipos e valores default editáveis
  3. Lista todos os pinos de OUTPUT (somente leitura) com tipo e label
  4. Exibe o ID único da instância (útil para debug)
  5. Emite value_changed(node_id, pin_id, new_value) ao editar qualquer campo

Quando nenhum nó está selecionado, exibe o estado "vazio" com instrução.
"""
from __future__ import annotations

from typing import Optional, Any

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QFrame,
    QFormLayout, QLineEdit, QDoubleSpinBox, QCheckBox,
    QScrollArea, QSizePolicy,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QPalette, QFont

from engine.localization.manager import tr


# ─────────────────────────────────────────────────────────────────────────────
#  Paleta de cores por data-type (espelha port_item.py)
# ─────────────────────────────────────────────────────────────────────────────
PIN_TYPE_COLORS: dict[str, str] = {
    "exec":    "#d9dde7",
    "number":  "#58a6ff",
    "float":   "#58a6ff",
    "int":     "#58a6ff",
    "bool":    "#50c878",
    "string":  "#e6b85c",
    "object":  "#47b8c8",
    "movement":"#ff8c69",
    "any":     "#ae7df0",
    "vector2": "#e07a5f",
    "vector3": "#e07a5f",
    "color":   "#d66ba0",
}

CATEGORY_COLORS: dict[str, str] = {
    "events":    "#d66ba0",
    "movement":  "#4c9aff",
    "position":  "#3fb6a8",
    "action":    "#ae7df0",
    "logic":     "#f0a64b",
    "condition": "#50c878",
    "objects":   "#47b8c8",
    "variables": "#d5b84b",
    "subgraphs": "#b48ead",
    "math":      "#e07a5f",
    "text":      "#81b29a",
    "ai":        "#cf6679",
    "audio":     "#76b7d5",
    "animation": "#a9c96c",
    "ui":        "#c9a9e0",
    "physics":   "#f4a460",
    "transform": "#3fb6a8",
}


def _color_dot(hex_color: str) -> str:
    return f'<span style="color:{hex_color};">●</span>'


class _SectionHeader(QLabel):
    """Cabeçalho colorido de seção do inspector."""
    def __init__(self, text: str, color: str = "#4c9aff", parent=None):
        super().__init__(text, parent)
        self.setStyleSheet(
            f"color: {color}; font-weight: bold; font-size: 10px;"
            " text-transform: uppercase; letter-spacing: 1px;"
            " padding: 6px 0 2px 0; border-bottom: 1px solid #2e3240;"
        )


class _Divider(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.HLine)
        self.setStyleSheet("border: none; border-top: 1px solid #2e3240; margin: 4px 0;")


class GraphNodeInspector(QWidget):
    """Inspector de propriedades para nós do grafo visual."""

    value_changed = Signal(str, str, object)  # (node_id, pin_id, new_value)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_node_id: Optional[str] = None
        self._current_instance_data: Optional[dict] = None

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # Scroll area para conteúdo longo
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        root_layout.addWidget(scroll)

        self._container = QWidget()
        self._container.setStyleSheet("background: #181b22;")
        scroll.setWidget(self._container)

        self._layout = QVBoxLayout(self._container)
        self._layout.setContentsMargins(10, 10, 10, 10)
        self._layout.setSpacing(4)
        self._layout.setAlignment(Qt.AlignTop)

        self._show_empty_state()

    # ─────────────────────────────────────────────────────────────────────────
    #  Public API
    # ─────────────────────────────────────────────────────────────────────────
    def inspect_node(self, node_item) -> None:
        """Popula o inspector com as propriedades do nó selecionado.

        Args:
            node_item: GraphNodeItem ou None (quando nada está selecionado).
        """
        self._clear()

        if node_item is None:
            self._show_empty_state()
            return

        node_def = getattr(node_item, "node_def", None)
        instance_data = getattr(node_item, "instance_data", {})

        if node_def is None:
            self._show_empty_state()
            return

        self._current_node_id = str(instance_data.get("id", ""))
        self._current_instance_data = instance_data

        self._build_header(node_def, instance_data)
        self._build_inputs(node_def, instance_data)
        self._build_outputs(node_def)
        self._build_meta(instance_data)

        self._layout.addStretch()

    def inspect_node_by_id(self, node_id: str) -> None:
        """Inspeciona um nó pelo ID de definição (para uso pelo inspector externo)."""
        self._clear()
        self._show_empty_state()

    # ─────────────────────────────────────────────────────────────────────────
    #  Builder methods
    # ─────────────────────────────────────────────────────────────────────────
    def _build_header(self, node_def, instance_data: dict) -> None:
        cat_key = str(getattr(node_def, "category_key", "") or getattr(node_def, "category", "logic")).lower()
        # Extract last segment (e.g. "logic.category.events" → "events")
        cat_simple = cat_key.split(".")[-1]
        cat_color = CATEGORY_COLORS.get(cat_simple, "#7f8b9c")

        # Node name + category badge
        name_text = tr(getattr(node_def, "name_key", node_def.id), fallback=node_def.id)
        name_label = QLabel(f"<b>{name_text}</b>")
        name_label.setStyleSheet("color: #f2f4f8; font-size: 13px; padding: 2px 0;")

        cat_label = QLabel(f"{_color_dot(cat_color)} {cat_simple.upper()}")
        cat_label.setStyleSheet(f"color: {cat_color}; font-size: 10px; letter-spacing: 1px;")
        cat_label.setTextFormat(Qt.RichText)

        desc_text = getattr(node_def, "description", "") or ""
        desc_label = QLabel(desc_text)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #6e7a8a; font-size: 10px; padding: 4px 0 6px 0;")

        self._layout.addWidget(name_label)
        self._layout.addWidget(cat_label)
        if desc_text:
            self._layout.addWidget(desc_label)
        self._layout.addWidget(_Divider())

    def _build_inputs(self, node_def, instance_data: dict) -> None:
        inputs = getattr(node_def, "inputs", [])
        if not inputs:
            return

        self._layout.addWidget(_SectionHeader("Inputs", "#4c9aff"))
        form = QFormLayout()
        form.setContentsMargins(0, 4, 0, 4)
        form.setHorizontalSpacing(8)
        form.setVerticalSpacing(6)
        form.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)

        saved_props: dict = instance_data.get("properties", {})

        for pin in inputs:
            pin_id = str(pin.id)
            pin_type_str = str(pin.pin_type).lower().replace("pintype.", "")
            label_text = tr(pin.label_key, fallback=pin_id)
            color = PIN_TYPE_COLORS.get(pin_type_str, "#ae7df0")

            # Label
            lbl = QLabel(f'{_color_dot(color)} {label_text}')
            lbl.setTextFormat(Qt.RichText)
            lbl.setStyleSheet("color: #aeb6c5; font-size: 10px;")
            lbl.setToolTip(f"Type: {pin_type_str}")

            # Editor widget based on type
            current_val = saved_props.get(pin_id, getattr(pin, "default_value", None))
            editor = self._make_editor(pin_id, pin_type_str, current_val, instance_data)

            form.addRow(lbl, editor)

        form_widget = QWidget()
        form_widget.setLayout(form)
        self._layout.addWidget(form_widget)
        self._layout.addWidget(_Divider())

    def _build_outputs(self, node_def) -> None:
        outputs = getattr(node_def, "outputs", [])
        if not outputs:
            return

        self._layout.addWidget(_SectionHeader("Outputs", "#50c878"))
        for pin in outputs:
            pin_type_str = str(pin.pin_type).lower().replace("pintype.", "")
            label_text = tr(pin.label_key, fallback=str(pin.id))
            color = PIN_TYPE_COLORS.get(pin_type_str, "#ae7df0")

            row = QLabel(f'{_color_dot(color)} {label_text}  <span style="color:#444d5e;">[{pin_type_str}]</span>')
            row.setTextFormat(Qt.RichText)
            row.setStyleSheet("color: #aeb6c5; font-size: 10px; padding: 1px 0;")
            self._layout.addWidget(row)

        self._layout.addWidget(_Divider())

    def _build_meta(self, instance_data: dict) -> None:
        node_id = str(instance_data.get("id", ""))
        if not node_id:
            return

        self._layout.addWidget(_SectionHeader("Debug Info", "#555e70"))
        id_label = QLabel(f'<span style="color:#555e70;">ID: {node_id[:8]}…</span>')
        id_label.setTextFormat(Qt.RichText)
        id_label.setStyleSheet("font-size: 9px; padding: 0;")
        id_label.setToolTip(node_id)
        self._layout.addWidget(id_label)

    # ─────────────────────────────────────────────────────────────────────────
    #  Editor Widget Factory
    # ─────────────────────────────────────────────────────────────────────────
    def _make_editor(self, pin_id: str, pin_type: str, current_val: Any, instance_data: dict) -> QWidget:
        node_id = str(instance_data.get("id", ""))

        if pin_type in ("bool",):
            w = QCheckBox()
            w.setChecked(bool(current_val))
            w.setStyleSheet("color: #f2f4f8;")
            w.stateChanged.connect(
                lambda state, pid=pin_id, nd=node_id, d=instance_data:
                    self._on_value_changed(nd, pid, bool(state), d)
            )
            return w

        if pin_type in ("float", "number", "int"):
            w = QDoubleSpinBox()
            w.setDecimals(0 if pin_type == "int" else 3)
            w.setRange(-1_000_000, 1_000_000)
            w.setSingleStep(1.0 if pin_type == "int" else 0.1)
            w.setStyleSheet(
                "QDoubleSpinBox { background: #1e2128; color: #f2f4f8; border: 1px solid #333; border-radius: 3px; padding: 2px 4px; }"
            )
            try:
                w.setValue(float(current_val) if current_val is not None else 0.0)
            except (TypeError, ValueError):
                w.setValue(0.0)
            w.valueChanged.connect(
                lambda val, pid=pin_id, nd=node_id, d=instance_data:
                    self._on_value_changed(nd, pid, val, d)
            )
            return w

        # string / exec / object / any → QLineEdit
        w = QLineEdit()
        w.setStyleSheet(
            "QLineEdit { background: #1e2128; color: #f2f4f8; border: 1px solid #333; border-radius: 3px; padding: 2px 6px; }"
        )
        if pin_type == "exec":
            w.setPlaceholderText("— exec —")
            w.setReadOnly(True)
            w.setStyleSheet(w.styleSheet() + " color: #555e70;")
        else:
            w.setText(str(current_val) if current_val is not None else "")
            w.editingFinished.connect(
                lambda pid=pin_id, nd=node_id, widget=w, d=instance_data:
                    self._on_value_changed(nd, pid, widget.text(), d)
            )
        return w

    # ─────────────────────────────────────────────────────────────────────────
    #  Internal helpers
    # ─────────────────────────────────────────────────────────────────────────
    def _on_value_changed(self, node_id: str, pin_id: str, value: Any, instance_data: dict) -> None:
        props = instance_data.setdefault("properties", {})
        props[pin_id] = value
        self.value_changed.emit(node_id, pin_id, value)

    def _show_empty_state(self) -> None:
        placeholder = QLabel("Select a node\nto inspect its properties.")
        placeholder.setAlignment(Qt.AlignCenter)
        placeholder.setStyleSheet("color: #3d4556; font-size: 12px; padding: 40px 0;")
        self._layout.addWidget(placeholder)

    def _clear(self) -> None:
        while self._layout.count():
            item = self._layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._current_node_id = None
        self._current_instance_data = None


# ─────────────────────────────────────────────────────────────────────────────
#  Backwards-compat alias (old GraphInspector name)
# ─────────────────────────────────────────────────────────────────────────────
GraphInspector = GraphNodeInspector
