from __future__ import annotations

from typing import Any, Callable, Dict, Optional

from engine.core.component import Component
from engine.component_registry import ComponentRegistry


@ComponentRegistry.component
class TimerComponent(Component):
    """Timer reutilizável com suporte a loop e callback."""

    def __init__(self, duration: float = 1.0, loop: bool = False, auto_start: bool = False) -> None:
        super().__init__()
        self.duration = float(duration)
        self.loop = bool(loop)
        self.auto_start = bool(auto_start)
        self.on_complete: Optional[Callable[[], None]] = None
        self._elapsed = 0.0
        self._running = False

    def start_timer(self) -> None:
        self._elapsed = 0.0
        self._running = True

    def stop(self) -> None:
        self._running = False

    def reset(self) -> None:
        self._running = False
        self._elapsed = 0.0

    @property
    def progress(self) -> float:
        return 1.0 if self.duration <= 0 else min(1.0, self._elapsed / self.duration)

    @property
    def remaining(self) -> float:
        return max(0.0, self.duration - self._elapsed)

    def start(self) -> None:
        if self.auto_start:
            self.start_timer()

    def update(self, dt: float) -> None:
        if not self._running:
            return
        self._elapsed += dt
        if self._elapsed >= self.duration:
            self._running = False
            if self.on_complete:
                self.on_complete()
            if self.loop:
                self.start_timer()

    def draw(self, screen) -> None:
        pass

    def serialize(self) -> Dict[str, Any]:
        data = super().serialize()
        data.update({"duration": self.duration, "loop": self.loop, "auto_start": self.auto_start, "elapsed": self._elapsed, "running": self._running})
        return data

    def deserialize(self, data: Dict[str, Any]) -> None:
        super().deserialize(data)
        self.duration = float(data.get("duration", 1.0))
        self.loop = bool(data.get("loop", False))
        self.auto_start = bool(data.get("auto_start", False))
        self._elapsed = float(data.get("elapsed", 0.0))
        self._running = bool(data.get("running", False))
