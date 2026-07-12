from __future__ import annotations

from typing import Any, Callable, Dict, Optional

from engine.core.component import Component
from engine.component_registry import ComponentRegistry


# Configuração usada quando este arquivo é anexado pelo Inspector como script.
SCRIPT_CONFIG = {"duration": 1.0, "loop": False, "auto_start": True}


def on_start(game):
    game.state.update(elapsed=0.0, running=SCRIPT_CONFIG["auto_start"], completed=False)


def on_update(game, dt):
    """Atualiza um temporizador simples acessível por game.state."""
    if not game.state.get("running", SCRIPT_CONFIG["auto_start"]):
        return
    game.state["elapsed"] = float(game.state.get("elapsed", 0.0)) + dt
    if game.state["elapsed"] < SCRIPT_CONFIG["duration"]:
        return
    game.state["completed"] = True
    game.state["running"] = bool(SCRIPT_CONFIG["loop"])
    if SCRIPT_CONFIG["loop"]:
        game.state["elapsed"] = 0.0


def on_instruction(game, instruction):
    """Aceita os comandos start_timer, stop_timer e reset_timer."""
    command = instruction.get("command")
    if command == "start_timer":
        game.state.update(elapsed=0.0, running=True, completed=False)
    elif command == "stop_timer":
        game.state["running"] = False
    elif command == "reset_timer":
        game.state.update(elapsed=0.0, running=False, completed=False)


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
