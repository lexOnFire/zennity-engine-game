from __future__ import annotations

from typing import Any, Callable


SelectionListener = Callable[[Any], None]


class SelectionManager:
    """Fonte única de verdade para seleção no editor.

    A Viewport, Hierarchy, Inspector e futuros Gizmos devem consultar este
    gerenciador em vez de manter seleção própria isolada.
    """

    def __init__(self) -> None:
        self._selected: Any = None
        self._listeners: list[SelectionListener] = []
        self._projection_listeners: list[SelectionListener] = []

    @property
    def selected(self) -> Any:
        return self._selected

    def set_selected(self, obj: Any) -> None:
        if obj is self._selected:
            self._notify(self._projection_listeners)
            return

        self._selected = obj
        self._notify([*self._listeners, *self._projection_listeners])

    select = set_selected

    def clear(self) -> None:
        self.set_selected(None)

    def subscribe(self, callback: SelectionListener) -> None:
        if callback not in self._listeners:
            self._listeners.append(callback)

    def subscribe_projection(self, callback: SelectionListener) -> None:
        """Registra uma projeção que também ressincroniza seleções idempotentes."""
        if callback not in self._projection_listeners:
            self._projection_listeners.append(callback)

    def unsubscribe(self, callback: SelectionListener) -> None:
        if callback in self._listeners:
            self._listeners.remove(callback)

        if callback in self._projection_listeners:
            self._projection_listeners.remove(callback)

    def reset(self) -> None:
        self._selected = None
        self._listeners.clear()
        self._projection_listeners.clear()

    def _notify(self, listeners: list[SelectionListener]) -> None:
        for callback in list(listeners):
            callback(self._selected)