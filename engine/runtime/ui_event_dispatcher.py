"""Global UI event dispatcher for Play Mode Logic Graphs."""
from __future__ import annotations
from typing import Any, Callable

class UIEventDispatcher:
    """Centraliza despachamento de eventos de UI para Logic Graphs em Play Mode."""

    def __init__(self) -> None:
        self._subscribers: dict[str, list[Callable]] = {}

    def subscribe(self, event_type: str, callback: Callable[[dict[str, Any]], None]) -> None:
        """Inscrever callback para tipo de evento."""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(callback)

    def emit(self, event_type: str, payload: dict[str, Any]) -> None:
        """Despachar evento para todos os subscribers."""
        for callback in self._subscribers.get(event_type, []):
            try:
                callback(payload)
            except Exception:
                pass  # Silenciar erros para não quebrar o jogo


# Global instance
_ui_event_dispatcher = UIEventDispatcher()


def get_ui_event_dispatcher() -> UIEventDispatcher:
    """Get global UI event dispatcher."""
    return _ui_event_dispatcher


def subscribe_ui_event(event_type: str, callback: Callable[[dict[str, Any]], None]) -> None:
    """Subscribe to UI event (convenience function)."""
    _ui_event_dispatcher.subscribe(event_type, callback)


def emit_ui_event(event_type: str, payload: dict[str, Any]) -> None:
    """Emit UI event (convenience function)."""
    _ui_event_dispatcher.emit(event_type, payload)
