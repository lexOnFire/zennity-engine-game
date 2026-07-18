from __future__ import annotations
from typing import Any

from PySide6.QtWidgets import QDockWidget
from editor.premium_panels import RealInspectorPanel
from editor.runtime.command_manager import FunctionCommand

class InspectorDock(QDockWidget):
    def __init__(self, editor_context=None, parent=None):
        super().__init__("Inspector", parent)
        self.panel = RealInspectorPanel()
        self.setWidget(self.panel)
        self.viewmodel = None  # To satisfy test expectations

    def set_viewmodel(self, viewmodel):
        self.viewmodel = viewmodel

    def load_object(self, obj):
        self.panel.load_object(obj)

    def set_command_manager(self, cm):
        self.panel.set_command_manager(cm)
        if self.viewmodel:
            self.viewmodel.command_manager = cm
        
    def clear(self):
        self.panel.current_object = None
        self.panel.header_label.setText("Sem seleção")
        self.panel.renderer_label.setText("")
        self.panel.transform_label.setText("")
        self.panel._clear_component_controls()
        self.panel.add_component_button.hide()
        
    def __getattr__(self, name):
        return getattr(self.panel, name)

    # Shims for UX Polish Tests
    def _component_matches_filter(self, component: Any) -> bool:
        if hasattr(self, "_component_filter_text"):
            self.panel.component_filter.setText(self._component_filter_text)
        return self.panel._component_matches_filter(component)

    def _copy_component(self, component: Any) -> None:
        self.panel.copy_component(component)

    def _paste_component_values(self, component: Any) -> None:
        if self.viewmodel and hasattr(self.viewmodel, "command_manager"):
            self.panel.set_command_manager(self.viewmodel.command_manager)
        self.panel.paste_component_values(component)

    def _reset_component(self, component: Any) -> None:
        if self.viewmodel and hasattr(self.viewmodel, "command_manager"):
            self.panel.set_command_manager(self.viewmodel.command_manager)
        self.panel.reset_component(component)

    def _move_component(self, obj: Any, component: Any, direction: int) -> None:
        if self.viewmodel and hasattr(self.viewmodel, "command_manager"):
            self.panel.set_command_manager(self.viewmodel.command_manager)
        self.panel.current_object = obj
        self.panel.move_component_visual(component, direction)

    def _set_object_property(self, prop_name: str, value: Any) -> None:
        obj = self.panel.current_object
        if obj is None and self.viewmodel:
            obj = getattr(self.viewmodel, "selected_object", None)

        if obj is None:
            return

        old_value = getattr(obj, prop_name)

        def set_val(v):
            setattr(obj, prop_name, v)

        cmd = FunctionCommand(
            f"Set {prop_name} on {obj.name}",
            lambda: set_val(value),
            lambda: set_val(old_value)
        )
        if self.viewmodel and hasattr(self.viewmodel, "command_manager"):
            self.viewmodel.command_manager.execute(cmd)
        elif self.panel.command_manager:
            self.panel.command_manager.execute(cmd)
        else:
            cmd.execute()
