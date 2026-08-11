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

    def unsubscribe(self, event_type: str, callback: Callable[[dict[str, Any]], None]) -> bool:
        """Remover uma inscrição. Seguro chamar para callback já removido.

        PHASE 9.5B Stage 3: sem isto, cada LogicGraphRuntime criado deixava aqui
        uma closure que segurava ``self``, então o runtime nunca era coletado e
        seus handlers de física/animação nunca eram desregistrados — cinco
        ciclos de Play/Stop deixavam cinco runtimes vivos.
        """
        callbacks = self._subscribers.get(event_type)
        if not callbacks:
            return False
        try:
            callbacks.remove(callback)
        except ValueError:
            return False
        if not callbacks:
            self._subscribers.pop(event_type, None)
        return True

    def clear(self) -> None:
        """Descartar todas as inscrições — usado no teardown da sessão de Play."""
        self._subscribers.clear()

    def subscriber_count(self) -> int:
        """Total de inscrições ativas. Usado pelos testes de lifecycle."""
        return sum(len(callbacks) for callbacks in self._subscribers.values())

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
