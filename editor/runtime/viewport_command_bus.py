"""Ponte tipada e observável entre a interface Qt e a Viewport Pygame."""
from __future__ import annotations

from copy import deepcopy
from typing import Any


class ViewportCommandBus:
    """Adiciona sequência e elimina comandos de estado pequenos e idênticos."""

    COALESCED_TYPES = {"viewport_size", "runtime_input", "set_tool", "set_snap", "set_view_mode"}

    def __init__(self, queue: Any) -> None:
        self.queue = queue
        self.sequence = 0
        self.sent = 0
        self.coalesced = 0
        self._last_by_type: dict[str, dict[str, Any]] = {}

    def _prepare(self, message: dict[str, Any]) -> dict[str, Any] | None:
        payload = deepcopy(dict(message))
        command_type = str(payload.get("type", ""))
        if command_type in self.COALESCED_TYPES and self._last_by_type.get(command_type) == payload:
            self.coalesced += 1
            return None
        if command_type in self.COALESCED_TYPES:
            self._last_by_type[command_type] = deepcopy(payload)
        self.sequence += 1
        payload.setdefault("_seq", self.sequence)
        self.sent += 1
        return payload

    def put(self, message: dict[str, Any], *args: Any, **kwargs: Any) -> bool:
        payload = self._prepare(message)
        if payload is None:
            return False
        self.queue.put(payload, *args, **kwargs)
        return True

    def put_nowait(self, message: dict[str, Any]) -> bool:
        payload = self._prepare(message)
        if payload is None:
            return False
        self.queue.put_nowait(payload)
        return True

    def stats(self) -> dict[str, int]:
        return {"sent": self.sent, "coalesced": self.coalesced, "sequence": self.sequence}
