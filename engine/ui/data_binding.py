"""Data Binding e Event Dispatcher entre UI & HUD, Blackboard e Logic Graph.

Fornece sincronização automática entre propriedades visuais de UI (ProgressBar, Label, Button, etc.),
variáveis do Blackboard e eventos do Logic Graph durante o Play Mode.
"""
from __future__ import annotations

from typing import Any, Callable, Dict, Optional, List
from engine.logic.blackboard import BlackboardStore

# Alias de compatibilidade
Blackboard = BlackboardStore


class UIBinding:
    """Representa a vinculação entre um widget de UI e uma chave do Blackboard."""

    def __init__(
        self,
        widget: Any,
        widget_property: str,
        blackboard_key: str,
        blackboard: Optional[Any] = None,
        converter: Optional[Callable[[Any], Any]] = None,
        object_key: str = "__default__",
        scope: str = "scene",
    ) -> None:
        self.widget = widget
        self.widget_property = widget_property
        self.blackboard_key = blackboard_key
        self.blackboard = blackboard
        self.converter = converter
        self.object_key = object_key
        self.scope = scope
        self._last_value: Any = None

    def update(self) -> None:
        """Sincroniza o valor do Blackboard para o Widget."""
        if self.blackboard is None:
            return

        if hasattr(self.blackboard, "get") and hasattr(self.blackboard, "shared_values"):
            val = self.blackboard.get(self.scope, self.blackboard_key, self.object_key)
            if val is None:
                found = self.blackboard.find(self.blackboard_key, self.object_key)
                if found:
                    val = found[1]
        elif hasattr(self.blackboard, "get"):
            val = self.blackboard.get(self.blackboard_key, None)
        else:
            val = None

        if val is None or val == self._last_value:
            return

        self._last_value = val
        target_val = self.converter(val) if self.converter else val

        if hasattr(self.widget, f"set_{self.widget_property}"):
            setter = getattr(self.widget, f"set_{self.widget_property}")
            setter(target_val)
        elif hasattr(self.widget, self.widget_property):
            setattr(self.widget, self.widget_property, target_val)



class UIDataBindingManager:
    """Gerenciador central de Data Binding para componentes de interface."""

    _instance: Optional[UIDataBindingManager] = None

    def __init__(self) -> None:
        self._bindings: List[UIBinding] = []
        self._event_handlers: Dict[str, List[Callable[..., None]]] = {}

    @classmethod
    def instance(cls) -> UIDataBindingManager:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        cls._instance = None

    def bind(
        self,
        widget: Any,
        widget_property: str,
        blackboard_key: str,
        blackboard: Optional[Any] = None,
        converter: Optional[Callable[[Any], Any]] = None,
        object_key: str = "__default__",
        scope: str = "scene",
    ) -> UIBinding:
        binding = UIBinding(
            widget=widget,
            widget_property=widget_property,
            blackboard_key=blackboard_key,
            blackboard=blackboard,
            converter=converter,
            object_key=object_key,
            scope=scope,
        )
        self._bindings.append(binding)
        # Executa sincronização inicial
        binding.update()
        return binding


    def unbind(self, binding: UIBinding) -> None:
        if binding in self._bindings:
            self._bindings.remove(binding)

    def register_ui_event(self, event_name: str, handler: Callable[..., None]) -> None:
        """Registra um callback do Logic Graph para escutar eventos de UI (ex: 'on_button_click')."""
        if event_name not in self._event_handlers:
            self._event_handlers[event_name] = []
        self._event_handlers[event_name].append(handler)

    def dispatch_ui_event(self, event_name: str, *args: Any, **kwargs: Any) -> None:
        """Dispara um evento de UI para ser consumido no Logic Graph."""
        handlers = self._event_handlers.get(event_name, [])
        for handler in handlers:
            try:
                handler(*args, **kwargs)
            except Exception:
                pass

    def update_all_bindings(self) -> None:
        """Atualiza todos os bindings registrados durante o tick de frame."""
        for binding in self._bindings:
            binding.update()
