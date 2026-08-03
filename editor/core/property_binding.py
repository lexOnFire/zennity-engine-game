"""Property Binding Framework — editar qualquer propriedade gera undo/redo automático.

Fluxo:
    Property → Binding → Undo/Redo → Serialization → UI

Uso:
    binding = PropertyBinding(
        obj=player,
        prop="speed",
        label="Velocidade",
        on_changed=inspector.refresh,
    )
    binding.set(120.0)   # gera Command no CommandManager e notifica UI
    binding.undo()       # desfaz
"""
from __future__ import annotations

from typing import Any, Callable, Generic, TypeVar

T = TypeVar("T")


class PropertyBinding(Generic[T]):
    """Liga uma propriedade de um objeto ao sistema de undo/redo e à UI.

    Qualquer alteração via `set()` é automaticamente registrada como
    um comando reversível e emite notificação para a UI.
    """

    def __init__(
        self,
        obj: Any,
        prop: str,
        label: str = "",
        on_changed: Callable[[T], None] | None = None,
        command_manager: Any = None,
        serializer: Callable[[T], Any] | None = None,
        deserializer: Callable[[Any], T] | None = None,
    ) -> None:
        self._obj = obj
        self._prop = prop
        self.label = label or prop
        self._on_changed = on_changed
        self._command_manager = command_manager
        self._serializer = serializer
        self._deserializer = deserializer

    @property
    def value(self) -> T:
        return getattr(self._obj, self._prop, None)

    def set(self, new_value: T, record_undo: bool = True) -> None:
        """Define o valor da propriedade, registrando undo se solicitado."""
        old_value = self.value
        if new_value == old_value:
            return

        if record_undo and self._command_manager is not None:
            self._record_command(old_value, new_value)
        else:
            self._apply(new_value)

    def _apply(self, value: T) -> None:
        setattr(self._obj, self._prop, value)
        if self._on_changed:
            try:
                self._on_changed(value)
            except Exception:
                import traceback
                traceback.print_exc()

    def _record_command(self, old_value: T, new_value: T) -> None:
        try:
            from editor.runtime.command_manager import FunctionCommand
            obj_ref = self._obj
            prop = self._prop
            on_changed = self._on_changed

            def _do() -> None:
                setattr(obj_ref, prop, new_value)
                if on_changed:
                    on_changed(new_value)

            def _undo() -> None:
                setattr(obj_ref, prop, old_value)
                if on_changed:
                    on_changed(old_value)

            cmd = FunctionCommand(f"Set {self.label} = {new_value}", _do, _undo)
            self._command_manager.execute(cmd)
        except Exception:
            self._apply(new_value)

    def serialize(self) -> Any:
        if self._serializer:
            return self._serializer(self.value)
        return self.value

    def deserialize(self, raw: Any) -> None:
        if self._deserializer:
            self._apply(self._deserializer(raw))
        else:
            self._apply(raw)


class PropertyBindingGroup:
    """Agrupa múltiplos PropertyBindings para um mesmo objeto (ex.: Inspector)."""

    def __init__(self, obj: Any, command_manager: Any = None) -> None:
        self._obj = obj
        self._command_manager = command_manager
        self._bindings: dict[str, PropertyBinding] = {}

    def bind(
        self,
        prop: str,
        label: str = "",
        on_changed: Callable | None = None,
    ) -> PropertyBinding:
        binding = PropertyBinding(
            obj=self._obj,
            prop=prop,
            label=label or prop,
            on_changed=on_changed,
            command_manager=self._command_manager,
        )
        self._bindings[prop] = binding
        return binding

    def get(self, prop: str) -> PropertyBinding | None:
        return self._bindings.get(prop)

    def set(self, prop: str, value: Any, record_undo: bool = True) -> None:
        binding = self._bindings.get(prop)
        if binding:
            binding.set(value, record_undo=record_undo)

    def serialize_all(self) -> dict[str, Any]:
        return {prop: b.serialize() for prop, b in self._bindings.items()}

    def deserialize_all(self, data: dict[str, Any]) -> None:
        for prop, raw in data.items():
            if prop in self._bindings:
                self._bindings[prop].deserialize(raw)
