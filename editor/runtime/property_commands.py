from __future__ import annotations

from typing import Any, Callable


class SetTransformPropertyCommand:
    """Comando reversível para alterar valores numéricos de propriedades do Transform."""

    def __init__(
        self,
        target_transform: Any,
        prop_name: str,
        index: int,
        old_value: float,
        new_value: float,
        description: str = "",
        on_changed: Callable[[float], None] | None = None
    ) -> None:
        self.target_transform = target_transform
        self.prop_name = prop_name
        self.index = index
        self.old_value = float(old_value)
        self.new_value = float(new_value)
        self.description = description or f"Set Transform {prop_name}[{index}] to {new_value}"
        self.on_changed = on_changed

    def execute(self) -> None:
        arr = getattr(self.target_transform, self.prop_name)
        arr[self.index] = self.new_value
        if self.on_changed:
            self.on_changed(self.new_value)

    def undo(self) -> None:
        arr = getattr(self.target_transform, self.prop_name)
        arr[self.index] = self.old_value
        if self.on_changed:
            self.on_changed(self.old_value)


class SetPropertyCommand:
    """Comando reversível para alterar propriedades genéricas em qualquer objeto/componente."""

    def __init__(
        self,
        target: Any,
        property_name: str,
        old_value: Any,
        new_value: Any,
        description: str = "",
        on_changed: Callable[[Any], None] | None = None
    ) -> None:
        self.target = target
        self.property_name = property_name
        self.old_value = old_value
        self.new_value = new_value
        self.description = description or f"Set {property_name} to {new_value}"
        self.on_changed = on_changed

    def execute(self) -> None:
        setattr(self.target, self.property_name, self.new_value)
        if self.on_changed:
            self.on_changed(self.new_value)

    def undo(self) -> None:
        setattr(self.target, self.property_name, self.old_value)
        if self.on_changed:
            self.on_changed(self.old_value)
