from __future__ import annotations

from typing import Any

from PySide6.QtWidgets import QWidget

from editor.runtime.command_manager import CommandManager, FunctionCommand


class InspectorPlugin:
    """Base para editores de componentes hospedados pelo Inspector."""

    component_type: str = ""
    title: str | None = None

    def supports(self, component: Any) -> bool:
        comp_type = getattr(component, "component_type", getattr(component, "type_name", type(component).__name__))
        return comp_type == self.component_type

    def create_widget(
        self,
        component: Any,
        command_manager: CommandManager | None,
        refresh: callable | None = None,
    ) -> QWidget:
        raise NotImplementedError

    def set_property(
        self,
        component: Any,
        property_name: str,
        value: Any,
        command_manager: CommandManager | None,
        refresh: callable | None = None,
    ) -> None:
        old_value = getattr(component, property_name)

        def apply(next_value: Any = value) -> None:
            setattr(component, property_name, next_value)
            if refresh is not None:
                refresh()

        def undo(previous_value: Any = old_value) -> None:
            setattr(component, property_name, previous_value)
            if refresh is not None:
                refresh()

        if command_manager is None:
            apply()
            return
        comp_type = getattr(component, "component_type", getattr(component, "type_name", type(component).__name__))
        command_manager.execute(
            FunctionCommand(
                f"Set {comp_type}.{property_name}",
                apply,
                undo,
            )
        )

    def refresh_widget(self, widget: QWidget, component: Any) -> None:
        return None
