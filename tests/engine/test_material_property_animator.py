"""Testes para MaterialPropertyAnimator component."""

import pytest
import math
from engine.graphics.material_property_animator import (
    MaterialPropertyAnimator,
    PropertyAnimation,
    EasingType,
)


class MockComponent:
    """Mock de componente para testes."""

    def __init__(self):
        self.color = (1.0, 1.0, 1.0, 1.0)
        self.opacity = 1.0
        self.brightness = 1.0


def test_material_property_animator_creation():
    """Testa criação básica."""
    animator = MaterialPropertyAnimator(
        target_component="SpriteRenderer",
        property_name="color",
        target_value=(1.0, 0.0, 0.0, 1.0),
        duration=0.5,
        easing="linear",
    )

    assert animator.target_component == "SpriteRenderer"
    assert animator.property_name == "color"
    assert animator.duration == 0.5
    assert animator.easing == "linear"


def test_property_animation_linear():
    """Testa animação linear."""
    component = MockComponent()
    anim = PropertyAnimation(
        component=component,
        property_name="brightness",
        target_value=0.0,
        duration=1.0,
        easing="linear",
    )

    anim.start()
    assert anim.start_value == 1.0

    # Meio da animação
    anim.update(0.5)
    assert abs(component.brightness - 0.5) < 0.01

    # Fim da animação
    anim.update(0.5)
    assert abs(component.brightness - 0.0) < 0.01
    assert anim.is_complete


def test_property_animation_ease_in():
    """Testa easing ease_in."""
    component = MockComponent()
    anim = PropertyAnimation(
        component=component,
        property_name="opacity",
        target_value=0.0,
        duration=1.0,
        easing="ease_in",
    )

    anim.start()

    # Primeira metade deve ser mais lenta
    anim.update(0.25)
    progress_25 = 1.0 - component.opacity

    anim.update(0.25)
    progress_50 = 1.0 - component.opacity

    # Com ease_in, o progresso deve ser menor na primeira metade
    assert progress_25 < 0.15  # menos de 15%


def test_property_animation_ease_out():
    """Testa easing ease_out."""
    component = MockComponent()
    anim = PropertyAnimation(
        component=component,
        property_name="opacity",
        target_value=0.0,
        duration=1.0,
        easing="ease_out",
    )

    anim.start()

    # Primeira metade deve ser mais rápida
    anim.update(0.25)
    progress_25 = 1.0 - component.opacity

    # Com ease_out, o progresso deve ser maior na primeira metade
    assert progress_25 > 0.40  # mais de 40%


def test_property_animation_color_interpolation():
    """Testa interpolação de cor."""
    component = MockComponent()
    anim = PropertyAnimation(
        component=component,
        property_name="color",
        target_value=(0.0, 0.0, 0.0, 1.0),
        duration=1.0,
        easing="linear",
    )

    anim.start()

    # Meio da animação
    anim.update(0.5)

    # Cor deve estar no meio
    assert isinstance(component.color, tuple)
    assert abs(component.color[0] - 0.5) < 0.01  # R = 0.5
    assert abs(component.color[1] - 0.5) < 0.01  # G = 0.5
    assert abs(component.color[2] - 0.5) < 0.01  # B = 0.5


def test_property_animation_bounce_easing():
    """Testa easing bounce."""
    component = MockComponent()
    anim = PropertyAnimation(
        component=component,
        property_name="brightness",
        target_value=0.0,
        duration=1.0,
        easing="bounce",
    )

    anim.start()

    # Bounce tem comportamento especial
    anim.update(1.0)
    assert anim.is_complete


def test_material_property_animator_animate():
    """Testa método animate do animator."""
    animator = MaterialPropertyAnimator()
    component = MockComponent()

    anim = animator.animate(
        component=component,
        property_name="brightness",
        target_value=0.5,
        duration=1.0,
        easing="linear",
    )

    assert anim is not None
    assert len(animator._animations) == 1
    assert anim.start_value == 1.0


def test_material_property_animator_animate_color():
    """Testa método animate_color."""
    animator = MaterialPropertyAnimator()
    component = MockComponent()

    anim = animator.animate_color(
        component=component,
        target_color=(1.0, 0.0, 0.0, 1.0),
        duration=0.5,
    )

    assert anim is not None
    assert anim.property_name == "color"


def test_material_property_animator_animate_opacity():
    """Testa método animate_opacity."""
    animator = MaterialPropertyAnimator()
    component = MockComponent()

    anim = animator.animate_opacity(
        component=component,
        target_opacity=0.0,
        duration=0.5,
    )

    assert anim is not None
    assert anim.property_name == "opacity"


def test_material_property_animator_is_animating():
    """Testa detecção de animação em progresso."""
    animator = MaterialPropertyAnimator()
    component = MockComponent()

    assert not animator.is_animating()

    animator.animate(
        component=component,
        property_name="brightness",
        target_value=0.0,
        duration=1.0,
    )

    assert animator.is_animating()

    # Completa animação
    animator._animations[0].is_complete = True
    animator.update(0.0)

    assert not animator.is_animating()


def test_material_property_animator_stop_all():
    """Testa parada de todas as animações."""
    animator = MaterialPropertyAnimator()
    component = MockComponent()

    animator.animate(component, "brightness", 0.0, 1.0)
    animator.animate(component, "opacity", 0.5, 1.0)

    assert len(animator._animations) == 2

    animator.stop_all()

    assert len(animator._animations) == 0


def test_material_property_animator_callback():
    """Testa callback de conclusão."""
    animator = MaterialPropertyAnimator()
    component = MockComponent()

    callback_called = False

    def on_complete():
        nonlocal callback_called
        callback_called = True

    anim = animator.animate(
        component=component,
        property_name="brightness",
        target_value=0.0,
        duration=0.1,
        on_complete=on_complete,
    )

    # Atualiza até completar
    animator.update(0.05)
    assert not callback_called

    animator.update(0.1)
    assert callback_called


def test_material_property_animator_serialization():
    """Testa serialização."""
    animator = MaterialPropertyAnimator(
        target_component="SpriteRenderer",
        property_name="color",
        target_value=(1.0, 0.0, 0.0, 1.0),
        duration=0.5,
        easing="ease_in",
    )

    data = animator.serialize()

    assert data["target_component"] == "SpriteRenderer"
    assert data["property_name"] == "color"
    assert data["duration"] == 0.5
    assert data["easing"] == "ease_in"

    # Desserializa
    animator2 = MaterialPropertyAnimator()
    animator2.deserialize(data)

    assert animator2.target_component == "SpriteRenderer"
    assert animator2.property_name == "color"
    assert animator2.duration == 0.5
