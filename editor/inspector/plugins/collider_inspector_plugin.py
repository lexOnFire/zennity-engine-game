from __future__ import annotations
from typing import Any
from PySide6.QtWidgets import QCheckBox, QDoubleSpinBox, QWidget
from editor.inspector.plugin import InspectorPlugin
from editor.runtime.command_manager import CommandManager, FunctionCommand
from editor.inspector.plugin_ui_utils import *


class ColliderInspectorPlugin(InspectorPlugin):
    component_type = "Collider"

    def supports(self, component: Any) -> bool:
        return getattr(component, "type_name", type(component).__name__) in {"BoxCollider", "CircleCollider"}

    def create_widget(
        self,
        component: Any,
        command_manager: CommandManager | None,
        refresh: callable | None = None,
    ) -> QWidget:
        type_name = getattr(component, "type_name", type(component).__name__)
        title = "Box Collider" if type_name == "BoxCollider" else "Circle Collider"
        widget, body = _section(title)
        numeric_fields = ["offset_x", "offset_y"]
        fields: dict[str, QDoubleSpinBox] = {}
        for candidate in ("width", "height", "radius"):
            if hasattr(component, candidate):
                numeric_fields.insert(0, candidate)
        for property_name in numeric_fields:
            label = {
                "offset_x": "Centro X",
                "offset_y": "Centro Y",
                "width": "Tamanho X",
                "height": "Tamanho Y",
                "radius": "Raio",
            }.get(property_name, property_name)
            row = _property_row(
                label,
                _float_field(
                    getattr(component, property_name),
                    lambda value, prop=property_name: setattr(component, prop, value),
                ),
            )
            body.addWidget(row)
            fields[property_name] = row.findChild(QDoubleSpinBox)
        for property_name in ("is_trigger", "debug_draw"):
            if hasattr(component, property_name):
                field = QCheckBox()
                field.setObjectName("InspectorCheckBox")
                field.setChecked(bool(getattr(component, property_name)))
                field.toggled.connect(lambda value, prop=property_name: setattr(component, prop, bool(value)))
                label = "Editar Collider" if property_name == "debug_draw" else "Trigger"
                body.addWidget(_property_row(label, field))
                if property_name == "is_trigger":
                    widget.chk_trigger = field
        if "width" in fields:
            widget.sb_w = fields["width"]
        if "height" in fields:
            widget.sb_h = fields["height"]
        if "radius" in fields:
            widget.sb_r = fields["radius"]

        def commit_val(field: QDoubleSpinBox, property_name: str) -> None:
            old_value = int(getattr(field, "original_value", getattr(component, property_name)))
            new_value = int(field.value())
            if old_value == new_value:
                return
            owner = getattr(component, "game_object", None)

            def apply(value: int = new_value) -> None:
                setattr(component, property_name, value)
                if owner is not None:
                    if property_name == "width":
                        owner.transform.scale[0] = float(value)
                    elif property_name == "height":
                        owner.transform.scale[1] = float(value)
                    elif property_name == "radius":
                        owner.transform.scale[0] = float(value * 2)
                        owner.transform.scale[1] = float(value * 2)
                field.blockSignals(True)
                field.setValue(value)
                field.original_value = value
                field.blockSignals(False)
                if refresh is not None:
                    refresh()

            def undo(value: int = old_value) -> None:
                apply(value)

            if command_manager is None:
                apply()
            else:
                command_manager.execute(FunctionCommand(f"Set Collider.{property_name}", apply, undo))

        widget.commit_val = commit_val
        widget.setProperty("component_type", type_name)
        return widget
