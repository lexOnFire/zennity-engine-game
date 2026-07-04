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

    @property
    def selected(self) -> Any:
        return self._selected

    def set_selected(self, obj: Any) -> None:
        if obj is self._selected:
            return
        self._selected = obj
        self._notify()

    def clear(self) -> None:
        self.set_selected(None)

    def subscribe(self, callback: SelectionListener) -> None:
        if callback not in self._listeners:
            self._listeners.append(callback)

    def unsubscribe(self, callback: SelectionListener) -> None:
        if callback in self._listeners:
            self._listeners.remove(callback)

    def _notify(self) -> None:
        for callback in list(self._listeners):
            callback(self._selected)
