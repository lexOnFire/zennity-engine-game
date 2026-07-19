from __future__ import annotations

from enum import Enum
from typing import Any, Callable

from engine.input import Input
from engine.runtime.input_manager import InputManager
from engine.runtime.runtime_scene import RuntimeScene
from engine.time import Time


class RuntimeState(str, Enum):
    STOPPED = "stopped"
    PLAYING = "playing"


RuntimeStateListener = Callable[[RuntimeState], None]


class RuntimeManager:
    """Owns the lifecycle of the isolated Play Mode world.

    - start_play / stop_play são idempotentes.
    - stop_play nunca lança exceção: limpa o que conseguir e garante
      que o estado final seja STOPPED mesmo em caso de erro parcial.
    """

    def __init__(self) -> None:
        self.state = RuntimeState.STOPPED
        self.runtime_scene: RuntimeScene | None = None
        self.input = InputManager()
        self._input_bound: bool = False
        self._state_listeners: list[RuntimeStateListener] = []

    @property
    def is_playing(self) -> bool:
        return self.state == RuntimeState.PLAYING

    def subscribe_state(self, callback: RuntimeStateListener) -> None:
        if callback not in self._state_listeners:
            self._state_listeners.append(callback)

    def unsubscribe_state(self, callback: RuntimeStateListener) -> None:
        if callback in self._state_listeners:
            self._state_listeners.remove(callback)

    def _set_state(self, state: RuntimeState) -> None:
        if state == self.state:
            return
        self.state = state
        for callback in list(self._state_listeners):
            callback(state)

    def start_play(self, editor_scene: Any) -> RuntimeScene:
        """Inicia o Play Mode. Idempotente — retorna a cena existente se já iniciou."""
        if self.runtime_scene is not None:
            return self.runtime_scene
        Time._runtime_reset()
        self.input.start()
        Input.bind_manager(self.input)
        self._input_bound = True
        try:
            self.runtime_scene = RuntimeScene(editor_scene)
            self.runtime_scene.start_runtime()
            self._set_state(RuntimeState.PLAYING)
        except Exception:
            # Se a criação falhar, garante cleanup para não deixar estado sujo
            self._cleanup_input()
            self.runtime_scene = None
            self._set_state(RuntimeState.STOPPED)
            raise
        return self.runtime_scene

    def tick(self, delta_time: float) -> None:
        if self.state != RuntimeState.PLAYING or self.runtime_scene is None:
            return
        scaled_delta_time = Time._runtime_tick(delta_time)
        self.input.update()
        self.runtime_scene.update(float(scaled_delta_time))

    def stop_play(self) -> None:
        """Para o Play Mode. Idempotente — seguro chamar múltiplas vezes."""
        if self.state == RuntimeState.STOPPED and self.runtime_scene is None:
            return
        if self.runtime_scene is not None:
            try:
                self.runtime_scene.stop_runtime()
            except Exception:
                pass
            try:
                self.runtime_scene.destroy()
            except Exception:
                pass
        self.runtime_scene = None
        self._cleanup_input()
        Time._runtime_reset()
        self._set_state(RuntimeState.STOPPED)

    def handle_input_event(self, event: Any) -> None:
        if self.state != RuntimeState.PLAYING:
            return
        self.input.handle_event(event)

    def _cleanup_input(self) -> None:
        """Desbinda e para o input — seguro chamar mesmo se nunca foi bindado."""
        if self._input_bound:
            try:
                Input.unbind_manager(self.input)
            except Exception:
                pass
            self._input_bound = False
        try:
            self.input.stop()
        except Exception:
            pass
