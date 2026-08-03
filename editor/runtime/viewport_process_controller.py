"""Lifecycle boundary for the isolated Pygame viewport process."""
from __future__ import annotations

from typing import Any, Callable

from editor.runtime.viewport_command_bus import ViewportCommandBus


class ViewportProcessController:
    """Owns viewport queues, process startup and idempotent shutdown."""

    def __init__(
        self,
        context: Any,
        command_queue: Any,
        event_queue: Any,
        process: Any = None,
    ) -> None:
        self._context = context
        self.command_queue = command_queue
        self.events = event_queue
        self.commands = ViewportCommandBus(command_queue)
        self.process = process
        self._shutdown_requested = False
        self._queues_closed = False

    @classmethod
    def create(cls, context: Any) -> "ViewportProcessController":
        return cls(context, context.Queue(), context.Queue())

    @classmethod
    def from_queues(
        cls,
        command_queue: Any,
        event_queue: Any,
        process: Any = None,
    ) -> "ViewportProcessController":
        return cls(None, command_queue, event_queue, process)

    def attach(self, process: Any) -> None:
        self.process = process
        self._shutdown_requested = False

    def start(
        self,
        target: Callable[..., Any],
        args: tuple[Any, ...],
        *,
        name: str,
    ) -> Any:
        if self._context is None:
            raise RuntimeError("viewport process context is not configured")
        if self.process is not None and self.process.is_alive():
            return self.process
        process = self._context.Process(target=target, args=args, name=name)
        self.attach(process)
        process.start()
        return process

    def shutdown(self, *, graceful_timeout: float = 1.5, kill_timeout: float = 2.0) -> None:
        if not self._shutdown_requested:
            try:
                self.commands.put_nowait({"type": "shutdown"})
            except Exception:
                pass
            self._shutdown_requested = True

        process = self.process
        if process is not None and process.is_alive():
            process.join(timeout=graceful_timeout)
            if process.is_alive():
                process.terminate()
                process.join(timeout=kill_timeout)
        self._close_queues()

    def _close_queues(self) -> None:
        """Stop multiprocessing feeder threads after the child has exited."""
        if self._queues_closed:
            return
        self._queues_closed = True
        for queue in (self.command_queue, self.events):
            close = getattr(queue, "close", None)
            if callable(close):
                close()
            join_thread = getattr(queue, "join_thread", None)
            if callable(join_thread):
                join_thread()
