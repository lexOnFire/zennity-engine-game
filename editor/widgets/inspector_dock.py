import warnings
from typing import Any

warnings.warn(
    "editor.widgets.inspector_dock está deprecado (legado embutido).",
    DeprecationWarning,
    stacklevel=2,
)


from PySide6.QtWidgets import QDockWidget
from editor.premium_panels import RealInspectorPanel
from editor.runtime.command_manager import FunctionCommand

class InspectorDock(RealInspectorPanel):
    def __init__(self, editor_context=None, parent=None):
        # Chama QDockWidget via Panel -> InspectorPanel -> RealInspectorPanel
        super().__init__()
        self.viewmodel = None

    def set_viewmodel(self, viewmodel):
        self.viewmodel = viewmodel

    def load_object(self, obj):
        super().load_object(obj)

    def set_command_manager(self, cm):
        super().set_command_manager(cm)
        if self.viewmodel:
            self.viewmodel.command_manager = cm
        
    def clear(self):
        self.load_object(None)
        
    # Shims for UX Polish Tests
    def _component_matches_filter(self, component: Any) -> bool:
        if hasattr(self, "_component_filter_text"):
            self.component_filter.setText(self._component_filter_text)
        return super()._component_matches_filter(component)

    def _copy_component(self, component: Any) -> None:
        self.copy_component(component)

    def _paste_component_values(self, component: Any) -> None:
        if self.viewmodel and hasattr(self.viewmodel, "command_manager"):
            self.set_command_manager(self.viewmodel.command_manager)
        self.paste_component_values(component)

    def _reset_component(self, component: Any) -> None:
        if self.viewmodel and hasattr(self.viewmodel, "command_manager"):
            self.set_command_manager(self.viewmodel.command_manager)
        self.reset_component(component)

    def _move_component(self, obj: Any, component: Any, direction: int) -> None:
        if self.viewmodel and hasattr(self.viewmodel, "command_manager"):
            self.set_command_manager(self.viewmodel.command_manager)
        self.current_object = obj
        self.move_component_visual(component, direction)

    def _set_object_property(self, prop_name: str, value: Any) -> None:
        obj = self.current_object
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
        elif self.command_manager:
            self.command_manager.execute(cmd)
        else:
            cmd.execute()
