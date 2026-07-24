"""Typed dispatch boundary for events emitted by the isolated viewport."""
from __future__ import annotations

from typing import Any, Callable, Mapping


ViewportEventHandler = Callable[[dict[str, Any]], None]


class ViewportEventDispatcher:
    def __init__(self, handlers: Mapping[str, ViewportEventHandler]) -> None:
        self._handlers = dict(handlers)

    def dispatch(self, message: dict[str, Any]) -> bool:
        handler = self._handlers.get(str(message.get("type", "")))
        if handler is None:
            return False
        handler(message)
        return True
