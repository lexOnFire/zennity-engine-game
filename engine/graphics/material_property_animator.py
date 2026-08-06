"""
MaterialPropertyAnimator — Anima propriedades de componentes com easing.

Permite animar propriedades como:
  - Cor (RGB + Alpha)
  - Opacidade (Alpha)
  - Valores numéricos (brilho, escala, etc)
  - Qualquer propriedade com valor float/int/tupla

Suporta easing curves (linear, ease-in, ease-out, etc) e callbacks.

Exemplo:
    animator = go.add_component(MaterialPropertyAnimator(
        target_component="SpriteRenderer",
        property_name="color",
        target_value=(1.0, 0.0, 0.0, 1.0),
        duration=0.5,
        easing="ease_in_out"
    ))
"""

from __future__ import annotations
from typing import Any, Callable, List, Optional, Tuple, Union, TYPE_CHECKING
from enum import Enum
import math

from engine.core.component import Component

if TYPE_CHECKING:
    from engine.game_object import GameObject


class EasingType(Enum):
    """Tipos de easing disponíveis."""
    LINEAR = "linear"
    EASE_IN = "ease_in"
    EASE_OUT = "ease_out"
    EASE_IN_OUT = "ease_in_out"
    BOUNCE = "bounce"
    ELASTIC = "elastic"


class PropertyAnimation:
    """Representa uma animação de uma propriedade."""

    def __init__(
        self,
        component: Any,
        property_name: str,
        target_value: Any,
        duration: float,
        easing: str = "linear",
        on_complete: Optional[Callable] = None,
    ):
        self.component = component
        self.property_name = property_name
        self.target_value = target_value
        self.duration = max(duration, 0.01)
        self.easing = easing
        self.on_complete = on_complete

        # Estado
        self.elapsed = 0.0
        self.start_value = None
        self.is_complete = False

    def start(self) -> None:
        """Inicia a animação e captura o valor inicial."""
        try:
            self.start_value = getattr(self.component, self.property_name, None)
        except AttributeError:
            self.start_value = None

    def update(self, dt: float) -> None:
        """Atualiza a animação."""
        if self.is_complete:
            return

        self.elapsed += dt

        if self.elapsed >= self.duration:
            self.elapsed = self.duration
            self.is_complete = True

        # Calcula progresso (0 a 1)
        progress = self.elapsed / self.duration

        # Aplica easing
        eased_progress = self._apply_easing(progress)

        # Interpola valor
        current_value = self._interpolate(self.start_value, self.target_value, eased_progress)

        # Aplica ao componente
        try:
            setattr(self.component, self.property_name, current_value)
        except AttributeError:
            pass

        # Dispara callback quando completa
        if self.is_complete and self.on_complete:
            try:
                self.on_complete()
            except Exception:
                pass

    def _apply_easing(self, progress: float) -> float:
        """Aplica função de easing."""
        if self.easing == "linear":
            return progress
        elif self.easing == "ease_in":
            return progress * progress
        elif self.easing == "ease_out":
            return 1.0 - (1.0 - progress) ** 2
        elif self.easing == "ease_in_out":
            if progress < 0.5:
                return 2.0 * progress * progress
            else:
                return 1.0 - (-2.0 * progress + 2.0) ** 2 / 2.0
        elif self.easing == "bounce":
            return self._easing_bounce(progress)
        elif self.easing == "elastic":
            return self._easing_elastic(progress)
        return progress

    @staticmethod
    def _easing_bounce(progress: float) -> float:
        """Easing bounce."""
        n1 = 7.5625
        d1 = 2.75

        if progress < 1.0 / d1:
            return n1 * progress * progress
        elif progress < 2.0 / d1:
            progress -= 1.5 / d1
            return n1 * progress * progress + 0.75
        elif progress < 2.5 / d1:
            progress -= 2.25 / d1
            return n1 * progress * progress + 0.9375
        else:
            progress -= 2.625 / d1
            return n1 * progress * progress + 0.984375

    @staticmethod
    def _easing_elastic(progress: float) -> float:
        """Easing elastic."""
        c4 = (2.0 * math.pi) / 3.0

        if progress == 0.0:
            return 0.0
        elif progress == 1.0:
            return 1.0
        else:
            return -(2.0 ** (10.0 * progress - 10.0)) * math.sin((progress * 10.0 - 10.75) * c4)

    @staticmethod
    def _interpolate(start: Any, end: Any, progress: float) -> Any:
        """Interpola entre dois valores."""
        # Número
        if isinstance(start, (int, float)) and isinstance(end, (int, float)):
            return start + (end - start) * progress

        # Tupla/Lista (cor, vetor, etc)
        if isinstance(start, (tuple, list)) and isinstance(end, (tuple, list)):
            return tuple(
                start[i] + (end[i] - start[i]) * progress
                for i in range(min(len(start), len(end)))
            )

        # Fallback: retorna valor final
        return end


class MaterialPropertyAnimator(Component):
    """Anima propriedades de componentes com easing."""

    UNIQUE = False
    component_type = "MaterialPropertyAnimator"

    def __init__(
        self,
        target_component: str = "SpriteRenderer",
        property_name: str = "color",
        target_value: Any = None,
        duration: float = 0.5,
        easing: str = "linear",
    ):
        """
        Parameters
        ----------
        target_component : str
            Nome do tipo de componente a animar (ex: "SpriteRenderer")
        property_name : str
            Nome da propriedade a animar (ex: "color", "opacity")
        target_value : Any
            Valor alvo da animação
        duration : float
            Duração da animação em segundos
        easing : str
            Tipo de easing (linear, ease_in, ease_out, ease_in_out, bounce, elastic)
        """
        super().__init__()
        self.target_component = target_component
        self.property_name = property_name
        self.target_value = target_value
        self.duration = duration
        self.easing = easing

        self._animations: List[PropertyAnimation] = []
        self._on_complete: Optional[Callable] = None

    def start(self) -> None:
        """Inicializa o animador."""
        pass

    def update(self, dt: float) -> None:
        """Atualiza todas as animações."""
        # Atualiza animações ativas
        for anim in self._animations:
            if not anim.is_complete:
                anim.update(dt)

        # Remove animações completas
        self._animations = [a for a in self._animations if not a.is_complete]

    def animate(
        self,
        component: Any,
        property_name: str,
        target_value: Any,
        duration: float,
        easing: str = "linear",
        on_complete: Optional[Callable] = None,
    ) -> PropertyAnimation:
        """
        Anima uma propriedade de um componente.

        Parameters
        ----------
        component : Any
            Componente a animar
        property_name : str
            Nome da propriedade
        target_value : Any
            Valor alvo
        duration : float
            Duração em segundos
        easing : str
            Tipo de easing
        on_complete : callable
            Callback quando animação completa

        Returns
        -------
        PropertyAnimation
            Objeto da animação (para controle)
        """
        anim = PropertyAnimation(
            component=component,
            property_name=property_name,
            target_value=target_value,
            duration=duration,
            easing=easing,
            on_complete=on_complete,
        )
        anim.start()
        self._animations.append(anim)
        return anim

    def animate_color(
        self,
        component: Any,
        target_color: Tuple[float, float, float, float],
        duration: float = 0.5,
        easing: str = "linear",
        on_complete: Optional[Callable] = None,
    ) -> PropertyAnimation:
        """Anima a cor de um componente (RGBA)."""
        return self.animate(
            component=component,
            property_name="color",
            target_value=target_color,
            duration=duration,
            easing=easing,
            on_complete=on_complete,
        )

    def animate_opacity(
        self,
        component: Any,
        target_opacity: float,
        duration: float = 0.5,
        easing: str = "linear",
        on_complete: Optional[Callable] = None,
    ) -> PropertyAnimation:
        """Anima opacidade (alpha)."""
        return self.animate(
            component=component,
            property_name="opacity",
            target_value=target_opacity,
            duration=duration,
            easing=easing,
            on_complete=on_complete,
        )

    def stop_all(self) -> None:
        """Para todas as animações."""
        self._animations.clear()

    def is_animating(self) -> bool:
        """Retorna se há animações em progresso."""
        return len(self._animations) > 0

    def on_complete(self, callback: Callable) -> None:
        """Registra callback quando todas as animações completam."""
        self._on_complete = callback

    def serialize(self) -> dict:
        """Serializa o componente."""
        data = super().serialize()
        data["target_component"] = self.target_component
        data["property_name"] = self.property_name
        data["target_value"] = self.target_value
        data["duration"] = self.duration
        data["easing"] = self.easing
        return data

    def deserialize(self, data: dict) -> None:
        """Desserializa o componente."""
        super().deserialize(data)
        self.target_component = data.get("target_component", "SpriteRenderer")
        self.property_name = data.get("property_name", "color")
        self.target_value = data.get("target_value")
        self.duration = data.get("duration", 0.5)
        self.easing = data.get("easing", "linear")
