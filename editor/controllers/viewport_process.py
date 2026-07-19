"""Controller da fronteira entre o shell Qt e a viewport isolada."""
from __future__ import annotations

from dataclasses import dataclass
from queue import Empty
from typing import Any, Iterator

from editor.runtime.viewport_command_bus import ViewportCommandBus


@dataclass(slots=True)
class ViewportProcessStats:
    commands_sent: int
    commands_coalesced: int
    last_sequence: int
    events_received: int


class ViewportProcessController:
    """Encapsula filas/processo sem depender de widgets PySide6."""

    def __init__(self, process: Any, commands: Any, events: Any) -> None:
        self.process = process
        self.commands = commands if isinstance(commands, ViewportCommandBus) else ViewportCommandBus(commands)
        self.events = events
        self.events_received = 0

    def send(self, command_type: str, **payload: Any) -> bool:
        return self.commands.put({"type": str(command_type), **payload})

    def send_scene(self, objects: list[dict[str, Any]]) -> bool:
        return self.send("scene_snapshot", objects=objects)

    def send_viewport_size(self, width: int, height: int, window_id: int | None = None) -> bool:
        payload: dict[str, Any] = {"size": (max(1, int(width)), max(1, int(height)))}
        if window_id is not None:
            payload["window_id"] = int(window_id)
        return self.send("viewport_size", **payload)

    def drain_events(self, limit: int = 512) -> Iterator[dict[str, Any]]:
        for _ in range(max(0, int(limit))):
            try:
                event = self.events.get_nowait()
            except Empty:
                break
            self.events_received += 1
            if isinstance(event, dict):
                yield event

    def shutdown(self, timeout: float = 2.0) -> None:
        self.send("shutdown")
        process = self.process
        if process is None:
            return
        process.join(timeout=max(0.0, float(timeout)))
        if process.is_alive():
            process.terminate()
            process.join(timeout=1.0)

    def stats(self) -> ViewportProcessStats:
        command_stats = self.commands.stats()
        return ViewportProcessStats(
            commands_sent=command_stats["sent"],
            commands_coalesced=command_stats["coalesced"],
            last_sequence=command_stats["sequence"],
            events_received=self.events_received,
        )
