"""
assets/scripts/timer_component.py
───────────────────────────────────────────────────────────────
Timer genérico com callback ao completar.

Uso:
    t = TimerComponent(duration=3.0, loop=False)
    t.on_complete = lambda: print("tempo esgotado!")
    go.add_component(t)
    t.start_timer()  # inicia contagem
"""
from __future__ import annotations

from typing import Any, Callable, Dict, Optional

from engine.core.component import Component
from engine.component_registry import ComponentRegistry


@ComponentRegistry.component
class TimerComponent(Component):
    """Timer reutilizável com suporte a loop e callback."""

    def __init__(
        self,
        duration: float = 1.0,
        loop: bool = False,
        auto_start: bool = False,
    ) -> None:
        super().__init__()
        self.duration: float = duration
        self.loop: bool = loop
        self.auto_start: bool = auto_start
        self.on_complete: Optional[Callable[[], None]] = None
        self._elapsed: float = 0.0
        self._running: bool = False

    # ------------------------------------------------------------------ #
    # API pública
    # ------------------------------------------------------------------ #

    def start_timer(self) -> None:
        """Inicia ou reinicia o timer."""
        self._elapsed = 0.0
        self._running = True

    def stop(self) -> None:
        """Para o timer sem disparar o callback."""
        self._running = False

    def reset(self) -> None:
        """Para e zera o timer."""
        self._running = False
        self._elapsed = 0.0

    @property
    def progress(self) -> float:
        """Progresso de 0.0 a 1.0."""
        if self.duration <= 0:
            return 1.0
        return min(1.0, self._elapsed / self.duration)

    @property
    def remaining(self) -> float:
        """Segundos restantes."""
        return max(0.0, self.duration - self._elapsed)

    # ------------------------------------------------------------------ #
    # Ciclo de vida
    # ------------------------------------------------------------------ #

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

    # ------------------------------------------------------------------ #
    # Serialização
    # ------------------------------------------------------------------ #

    def serialize(self) -> Dict[str, Any]:
        data = super().serialize()
        data["duration"] = self.duration
        data["loop"] = self.loop
        data["auto_start"] = self.auto_start
        data["elapsed"] = self._elapsed
        data["running"] = self._running
        return data

    def deserialize(self, data: Dict[str, Any]) -> None:
        super().deserialize(data)
        self.duration = float(data.get("duration", 1.0))
        self.loop = bool(data.get("loop", False))
        self.auto_start = bool(data.get("auto_start", False))
        self._elapsed = float(data.get("elapsed", 0.0))
        self._running = bool(data.get("running", False))
