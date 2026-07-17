"""SelectionManager — single source of truth for editor object selection.

Decouples selection state from SceneViewModel so that multiple panels
(Hierarchy, Viewport, Inspector) can observe or drive selection without
creating circular dependencies.

Usage::

    manager = SelectionManager()
    viewmodel = SceneViewModel(model, selection_manager=manager)

    # Drive selection from any panel:
    manager.set_selected(game_object)

    # Read selection anywhere:
    obj = manager.selected
"""
from __future__ import annotations

from typing import Callable, Optional

from engine.game_object import GameObject


class SelectionManager:
    """Holds the currently selected :class:`GameObject` and notifies listeners."""

    def __init__(self) -> None:
        self._selected: Optional[GameObject] = None
        self._listeners: list[Callable[[Optional[GameObject]], None]] = []

    # ------------------------------------------------------------------ #
    # Public API                                                           #
    # ------------------------------------------------------------------ #

    @property
    def selected(self) -> Optional[GameObject]:
        """Currently selected object, or *None*."""
        return self._selected

    def set_selected(self, obj: Optional[GameObject]) -> None:
        """Change the selection and notify all registered listeners."""
        current_id = self._selected.id if self._selected else None
        new_id = obj.id if obj else None
        if current_id != new_id:
            self._selected = obj
            for cb in list(self._listeners):
                cb(obj)

    # ------------------------------------------------------------------ #
    # Listener registration                                                #
    # ------------------------------------------------------------------ #

    def add_listener(self, cb: Callable[[Optional[GameObject]], None]) -> None:
        """Register *cb* to be called whenever the selection changes."""
        if cb not in self._listeners:
            self._listeners.append(cb)

    def remove_listener(self, cb: Callable[[Optional[GameObject]], None]) -> None:
        """Unregister a previously added listener (no-op if not found)."""
        try:
            self._listeners.remove(cb)
        except ValueError:
            pass

    def clear_listeners(self) -> None:
        """Remove all listeners."""
        self._listeners.clear()
