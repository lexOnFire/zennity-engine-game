"""Barramento de eventos determinístico para comunicação entre Logic Graphs."""

from __future__ import annotations

from collections import deque
from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Callable


@dataclass(frozen=True)
class LogicEvent:
    name: str
    payload: Any = None
    source: str = ""


class LogicEventBus:
    """Entrega eventos em fila e limita cascatas para evitar loops infinitos."""

    MAX_EVENTS_PER_DISPATCH = 128

    def __init__(self) -> None:
        self._subscribers: dict[str, list[Callable[[LogicEvent], None]]] = {}
        self._queue: deque[LogicEvent] = deque()
        self._dispatching = False
        self.recent: list[dict[str, Any]] = []

    def subscribe(self, name: str, callback: Callable[[LogicEvent], None]) -> None:
        event_name = str(name).strip()
        key = event_name.casefold()
        if not event_name or callback in self._subscribers.setdefault(key, []):
            return
        self._subscribers[key].append(callback)

    def emit(self, name: str, payload: Any = None, source: str = "") -> None:
        event_name = str(name).strip()
        if not event_name:
            raise ValueError("O evento precisa ter um nome.")
        self._queue.append(LogicEvent(event_name, deepcopy(payload), str(source)))

    def dispatch(self) -> int:
        if self._dispatching:
            return 0
        self._dispatching = True
        delivered = 0
        try:
            while self._queue:
                if delivered >= self.MAX_EVENTS_PER_DISPATCH:
                    self._queue.clear()
                    raise RuntimeError("Limite de eventos excedido; verifique eventos que disparam uns aos outros.")
                event = self._queue.popleft()
                self.recent.append({
                    "name": event.name,
                    "source": event.source,
                    "payload": self._debug_value(event.payload),
                })
                self.recent = self.recent[-12:]
                for callback in tuple(self._subscribers.get(event.name.casefold(), ())):
                    callback(event)
                delivered += 1
            return delivered
        except Exception:
            self._queue.clear()
            raise
        finally:
            self._dispatching = False

    @staticmethod
    def _debug_value(value: Any) -> Any:
        if value is None or isinstance(value, (bool, int, float, str)):
            return value
        return f"<{type(value).__name__}>"
