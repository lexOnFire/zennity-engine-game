from __future__ import annotations

__all__ = [
    "_section",
    "_float_field",
    "_axis_row",
    "_property_row",
    "_project_relative",
    "_available_script_paths",
    "_script_template",
    "_safe_script_name",
    "_safe_class_name",
    "COLLAPSED_STATES",
]

from pathlib import Path
from typing import Any

from PySide6.QtCore import QUrl, Qt
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QSpinBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from editor.inspector.plugin import InspectorPlugin
from editor.inspector.plugin_registry import inspector_plugin_registry
from editor.runtime.command_manager import CommandManager, FunctionCommand


# Dicionário para manter o estado de colapso de cada tópico/componente
COLLAPSED_STATES: dict[str, bool] = {}


def _section(title: str) -> tuple[QWidget, QVBoxLayout]:
    widget = QWidget()
    widget.setObjectName("InspectorComponentCard")
    layout = QVBoxLayout(widget)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(0)

    header_host = QWidget()
    header_host.setObjectName("InspectorComponentHeader")
    header_host.setCursor(Qt.PointingHandCursor)
    header_layout = QHBoxLayout(header_host)
    header_layout.setContentsMargins(6, 4, 6, 4)
    header_layout.setSpacing(6)

    foldout = QLabel("▾")
    foldout.setObjectName("InspectorFoldout")
    icon = QLabel("✦")
    icon.setObjectName("InspectorComponentIcon")
    header = QLabel(title)
    header.setObjectName("InspectorComponentTitle")
    header_layout.addWidget(foldout)
    header_layout.addWidget(icon)
    header_layout.addWidget(header, 1)
    header_layout.addWidget(QLabel("↻"))
    header_layout.addWidget(QLabel("⋮"))

    body = QWidget()
    body.setObjectName("InspectorComponentBody")
    body_layout = QVBoxLayout(body)
    body_layout.setContentsMargins(8, 6, 8, 8)
    body_layout.setSpacing(4)
    layout.addWidget(header_host)
    layout.addWidget(body)

    # Restaura o estado colapsado anterior se houver
    if COLLAPSED_STATES.get(title, False):
        body.setVisible(False)
        foldout.setText("▸")

    # Função para encolher/expandir o tópico
    def toggle_collapse(event):
        if body.isVisible():
            body.setVisible(False)
            foldout.setText("▸")
            COLLAPSED_STATES[title] = True
        else:
            body.setVisible(True)
            foldout.setText("▾")
            COLLAPSED_STATES[title] = False
    
    header_host.mousePressEvent = toggle_collapse

    return widget, body_layout


def _float_field(value: float, on_change: callable) -> QDoubleSpinBox:
    field = QDoubleSpinBox()
    field.setObjectName("InspectorNumberField")
    field.setButtonSymbols(QDoubleSpinBox.NoButtons)
    field.setRange(-999999.0, 999999.0)
    field.setDecimals(2)
    field.setSingleStep(0.1)
    field.setValue(float(value))
    field.valueChanged.connect(lambda next_value: on_change(float(next_value)))
    field.original_value = float(value)
    return field


def _axis_row(label: str, values: Any, on_change: callable) -> QWidget:
    row = QWidget()
    row.setObjectName("InspectorPropertyRow")
    layout = QHBoxLayout(row)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(4)
    title = QLabel(label)
    title.setObjectName("InspectorPropertyLabel")
    layout.addWidget(title)
    for index, axis in enumerate(("X", "Y", "Z")):
        axis_label = QLabel(axis)
        axis_label.setObjectName("InspectorAxisLabel")
        layout.addWidget(axis_label)
        layout.addWidget(_float_field(values[index], lambda value, idx=index: on_change(idx, value)), 1)
    return row


def _property_row(label: str, editor: QWidget) -> QWidget:
    row = QWidget()
    row.setObjectName("InspectorPropertyRow")
    layout = QHBoxLayout(row)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(6)
    title = QLabel(label)
    title.setObjectName("InspectorPropertyLabel")
    layout.addWidget(title)
    layout.addWidget(editor, 1)
    return row


def _project_relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(Path.cwd().resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _available_script_paths() -> list[str]:
    scripts_root = Path.cwd() / "Assets" / "Scripts"
    if not scripts_root.exists():
        return []
    return [
        _project_relative(path)
        for path in sorted(scripts_root.rglob("*.py"), key=lambda item: item.as_posix().lower())
        if not path.name.endswith(".meta")
    ]


def _script_template(class_name: str) -> str:
    return (
        "from engine.runtime import Input, ScriptBehaviour\n\n\n"
        f"class {class_name}(ScriptBehaviour):\n"
        "    def on_start(self):\n"
        "        pass\n\n"
        "    def on_update(self, delta_time):\n"
        "        if Input.is_key_down(\"Space\"):\n"
        "            self.transform.position[0] += 120.0 * delta_time\n\n"
        "    def on_destroy(self):\n"
        "        pass\n"
    )


def _safe_script_name(name: str) -> str:
    cleaned = "".join(ch.lower() if ch.isalnum() else "_" for ch in name).strip("_")
    return cleaned or "game_object"


def _safe_class_name(name: str) -> str:
    parts = [part for part in _safe_script_name(name).split("_") if part]
    return "".join(part.capitalize() for part in parts) + "Behaviour"


