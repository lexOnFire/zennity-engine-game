from __future__ import annotations

from typing import Any, Callable


class SetTransformPropertyCommand:
    """Comando reversivel para alterar valores numericos de propriedades do Transform."""

    def __init__(
        self,
        target_transform: Any,
        prop_name: str,
        index: int,
        old_value: float,
        new_value: float,
        description: str = "",
        on_changed: Callable[[float], None] | None = None,
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
    """Comando reversivel para alterar propriedades genericas em qualquer objeto/componente.

    Seguranca extra: se `old_value` nao for fornecido explicitamente, o construtor
    le o valor atual do target ANTES do execute para evitar snapshots errados.
    """

    def __init__(
        self,
        target: Any,
        property_name: str,
        new_value: Any,
        old_value: Any = _SENTINEL := object(),
        description: str = "",
        on_changed: Callable[[Any], None] | None = None,
    ) -> None:
        self.target = target
        self.property_name = property_name
        self.new_value = new_value
        # Captura old_value do estado atual caso nao tenha sido passado
        if old_value is SetPropertyCommand._SENTINEL:  # type: ignore[attr-defined]
            try:
                self.old_value = getattr(target, property_name)
            except AttributeError:
                self.old_value = None
        else:
            self.old_value = old_value
        self.description = description or f"Set {property_name} to {new_value}"
        self.on_changed = on_changed

    _SENTINEL = object()

    def execute(self) -> None:
        setattr(self.target, self.property_name, self.new_value)
        if self.on_changed:
            self.on_changed(self.new_value)

    def undo(self) -> None:
        setattr(self.target, self.property_name, self.old_value)
        if self.on_changed:
            self.on_changed(self.old_value)
