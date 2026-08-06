"""
AnimationController — Máquina de estados avançada para animações.

Sistema tipo Mecanim do Unity que suporta:
  - Estados nomeados (idle, run, jump, etc)
  - Transições com condições (parâmetros)
  - Parâmetros float, int, bool que controlam transições
  - Blending/cross-fade entre animações
  - Callbacks em eventos de estado

Exemplo:
    controller = go.add_component(AnimationController())
    controller.add_state("idle", "idle_clip")
    controller.add_state("run", "run_clip")
    controller.add_transition(
        from_state="idle",
        to_state="run",
        condition=lambda p: p["speed"] > 0.5
    )
    controller.set_parameter("speed", 1.5)
"""

from __future__ import annotations
from typing import Any, Callable, Dict, List, Optional, Tuple, TYPE_CHECKING
from enum import Enum

from engine.core.component import Component
from engine.animation.animator import Animator
from engine.animation.clip import AnimationClip

if TYPE_CHECKING:
    from engine.game_object import GameObject


class ParameterType(Enum):
    """Tipos de parâmetros para transições."""
    FLOAT = "float"
    INT = "int"
    BOOL = "bool"


class AnimationController(Component):
    """Máquina de estados avançada para animações."""

    UNIQUE = True
    component_type = "AnimationController"

    def __init__(
        self,
        default_state: str = "idle",
        blend_duration: float = 0.1,
    ):
        """
        Parameters
        ----------
        default_state : str
            Estado inicial da máquina
        blend_duration : float
            Duração do cross-fade entre animações (em segundos)
        """
        super().__init__()
        self.default_state = default_state
        self.blend_duration = blend_duration

        # Estados e transições
        self._states: Dict[str, str] = {}  # state_name -> clip_name
        self._transitions: List[Dict[str, Any]] = []
        self._parameters: Dict[str, Any] = {}
        self._parameter_types: Dict[str, ParameterType] = {}

        # Estado atual
        self._current_state = ""
        self._next_state: Optional[str] = None
        self._blend_progress = 0.0
        self._is_blending = False

        # Componentes internos
        self._animator: Optional[Animator] = None

        # Callbacks
        self._on_state_enter: Dict[str, Callable] = {}
        self._on_state_exit: Dict[str, Callable] = {}

    def start(self) -> None:
        """Inicializa o controller."""
        # Busca ou cria o Animator
        self._animator = self.game_object.get_component(Animator)
        if self._animator is None:
            self._animator = self.game_object.add_component(Animator())

        # Coloca no estado inicial
        if self.default_state in self._states:
            self._current_state = self.default_state
            self._play_state(self.default_state)

    def update(self, dt: float) -> None:
        """Atualiza transições e blending."""
        # Atualiza blending
        if self._is_blending:
            self._blend_progress += dt / max(self.blend_duration, 0.01)
            if self._blend_progress >= 1.0:
                self._blend_progress = 1.0
                self._is_blending = False

        # Verifica transições
        self._evaluate_transitions()

    def add_state(self, state_name: str, clip_name: str) -> None:
        """Registra um estado."""
        self._states[state_name] = clip_name

    def add_transition(
        self,
        from_state: str,
        to_state: str,
        condition: Optional[Callable[[Dict[str, Any]], bool]] = None,
        duration: float = 0.1,
    ) -> None:
        """
        Adiciona uma transição entre estados.

        Parameters
        ----------
        from_state : str
            Estado de origem
        to_state : str
            Estado de destino
        condition : callable
            Função que retorna True quando deve transicionar
            Recebe dict de parâmetros
        duration : float
            Duração do blend/cross-fade
        """
        self._transitions.append({
            "from": from_state,
            "to": to_state,
            "condition": condition or (lambda p: True),
            "duration": duration,
        })

    def set_parameter(self, param_name: str, value: Any) -> None:
        """Define um parâmetro."""
        # Detecta tipo automaticamente
        if param_name not in self._parameter_types:
            if isinstance(value, bool):
                self._parameter_types[param_name] = ParameterType.BOOL
            elif isinstance(value, int):
                self._parameter_types[param_name] = ParameterType.INT
            elif isinstance(value, float):
                self._parameter_types[param_name] = ParameterType.FLOAT

        self._parameters[param_name] = value

    def get_parameter(self, param_name: str, default: Any = None) -> Any:
        """Obtém um parâmetro."""
        return self._parameters.get(param_name, default)

    def get_current_state(self) -> str:
        """Retorna o estado atual."""
        return self._current_state

    def set_state(self, state_name: str, force: bool = False) -> None:
        """Muda manualmente para um estado."""
        if state_name not in self._states:
            return

        if self._current_state == state_name and not force:
            return

        self._transition_to(state_name)

    def on_state_enter(self, state_name: str, callback: Callable) -> None:
        """Registra callback quando entra em um estado."""
        self._on_state_enter[state_name] = callback

    def on_state_exit(self, state_name: str, callback: Callable) -> None:
        """Registra callback quando sai de um estado."""
        self._on_state_exit[state_name] = callback

    # ======================================================================
    # Métodos internos
    # ======================================================================

    def _evaluate_transitions(self) -> None:
        """Avalia todas as transições e muda de estado se necessário."""
        if self._current_state not in self._states:
            return

        for trans in self._transitions:
            if trans["from"] != self._current_state:
                continue

            try:
                if trans["condition"](self._parameters):
                    self._transition_to(trans["to"], duration=trans["duration"])
                    break
            except Exception:
                pass

    def _transition_to(self, to_state: str, duration: Optional[float] = None) -> None:
        """Realiza transição para um novo estado."""
        if to_state not in self._states:
            return

        if self._current_state == to_state:
            return

        # Dispara callback de saída
        if self._current_state in self._on_state_exit:
            try:
                self._on_state_exit[self._current_state]()
            except Exception:
                pass

        # Muda de estado
        self._next_state = to_state
        self._blend_progress = 0.0
        self._is_blending = True

        # Toca a nova animação
        self._play_state(to_state)

        # Dispara callback de entrada
        if to_state in self._on_state_enter:
            try:
                self._on_state_enter[to_state]()
            except Exception:
                pass

    def _play_state(self, state_name: str) -> None:
        """Toca a animação de um estado."""
        if self._animator is None:
            return

        clip_name = self._states.get(state_name, "")
        if clip_name:
            self._animator.play(clip_name)
            self._current_state = state_name

    def serialize(self) -> dict:
        """Serializa o componente."""
        data = super().serialize()
        data["default_state"] = self.default_state
        data["blend_duration"] = self.blend_duration
        # Serializa states
        data["states"] = dict(self._states)
        # Serializa parâmetros
        data["parameters"] = dict(self._parameters)
        return data

    def deserialize(self, data: dict) -> None:
        """Desserializa o componente."""
        super().deserialize(data)
        self.default_state = data.get("default_state", "idle")
        self.blend_duration = data.get("blend_duration", 0.1)
        self._states = data.get("states", {})
        self._parameters = data.get("parameters", {})
