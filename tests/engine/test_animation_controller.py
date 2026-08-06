"""Testes para AnimationController component."""

import pytest
from engine.animation.animation_controller import AnimationController, ParameterType
from engine.game_object import GameObject


def test_animation_controller_creation():
    """Testa criação básica de AnimationController."""
    controller = AnimationController(
        default_state="idle",
        blend_duration=0.2,
    )

    assert controller.default_state == "idle"
    assert controller.blend_duration == 0.2
    assert controller.get_current_state() == ""


def test_animation_controller_add_states():
    """Testa adição de estados."""
    controller = AnimationController()

    controller.add_state("idle", "idle_clip")
    controller.add_state("run", "run_clip")
    controller.add_state("jump", "jump_clip")

    assert "idle" in controller._states
    assert "run" in controller._states
    assert "jump" in controller._states
    assert controller._states["idle"] == "idle_clip"


def test_animation_controller_parameters():
    """Testa sistema de parâmetros."""
    controller = AnimationController()

    # Define parâmetros de diferentes tipos
    controller.set_parameter("speed", 1.5)
    controller.set_parameter("is_jumping", True)
    controller.set_parameter("combo_count", 3)

    # Recupera parâmetros
    assert controller.get_parameter("speed") == 1.5
    assert controller.get_parameter("is_jumping") == True
    assert controller.get_parameter("combo_count") == 3
    assert controller.get_parameter("nonexistent", "default") == "default"


def test_animation_controller_auto_parameter_type_detection():
    """Testa detecção automática de tipo de parâmetro."""
    controller = AnimationController()

    # Float
    controller.set_parameter("speed", 1.5)
    assert controller._parameter_types["speed"] == ParameterType.FLOAT

    # Bool
    controller.set_parameter("is_grounded", True)
    assert controller._parameter_types["is_grounded"] == ParameterType.BOOL

    # Int
    controller.set_parameter("frame_count", 10)
    assert controller._parameter_types["frame_count"] == ParameterType.INT


def test_animation_controller_transitions():
    """Testa adição de transições."""
    controller = AnimationController()

    controller.add_state("idle", "idle_clip")
    controller.add_state("run", "run_clip")

    # Adiciona transição com condição
    controller.add_transition(
        from_state="idle",
        to_state="run",
        condition=lambda p: p.get("speed", 0) > 0.5,
        duration=0.1
    )

    assert len(controller._transitions) == 1
    trans = controller._transitions[0]
    assert trans["from"] == "idle"
    assert trans["to"] == "run"
    assert trans["duration"] == 0.1


def test_animation_controller_transition_condition():
    """Testa avaliação de condições de transição."""
    controller = AnimationController()

    controller.add_state("idle", "idle_clip")
    controller.add_state("run", "run_clip")

    # Transição que verifica speed > 0.5
    controller.add_transition(
        from_state="idle",
        to_state="run",
        condition=lambda p: p.get("speed", 0) > 0.5,
    )

    # Simula condição falsa
    trans = controller._transitions[0]
    controller._parameters = {"speed": 0.3}
    assert trans["condition"](controller._parameters) == False

    # Simula condição verdadeira
    controller._parameters = {"speed": 1.0}
    assert trans["condition"](controller._parameters) == True


def test_animation_controller_callbacks():
    """Testa callbacks de entrada/saída de estado."""
    controller = AnimationController()

    controller.add_state("idle", "idle_clip")
    controller.add_state("run", "run_clip")

    enter_called = False
    exit_called = False

    def on_enter():
        nonlocal enter_called
        enter_called = True

    def on_exit():
        nonlocal exit_called
        exit_called = True

    controller.on_state_enter("idle", on_enter)
    controller.on_state_exit("idle", on_exit)

    assert controller._on_state_enter["idle"] is not None
    assert controller._on_state_exit["idle"] is not None


def test_animation_controller_serialization():
    """Testa serialização e desserialização."""
    controller = AnimationController(
        default_state="idle",
        blend_duration=0.15,
    )

    controller.add_state("idle", "idle_clip")
    controller.add_state("run", "run_clip")
    controller.set_parameter("speed", 1.5)

    # Serializa
    data = controller.serialize()

    assert data["default_state"] == "idle"
    assert data["blend_duration"] == 0.15
    assert data["states"]["idle"] == "idle_clip"
    assert data["states"]["run"] == "run_clip"
    assert data["parameters"]["speed"] == 1.5

    # Desserializa
    controller2 = AnimationController()
    controller2.deserialize(data)

    assert controller2.default_state == "idle"
    assert controller2.blend_duration == 0.15
    assert controller2._states["idle"] == "idle_clip"
    assert controller2._parameters["speed"] == 1.5


def test_animation_controller_blend_progress():
    """Testa progresso de blending entre animações."""
    controller = AnimationController(blend_duration=0.5)

    assert controller._blend_progress == 0.0
    assert controller._is_blending == False

    # Simula blending
    controller._is_blending = True
    controller.update(0.25)

    # Progresso deve ser 0.25 / 0.5 = 0.5
    assert controller._blend_progress == 0.5

    controller.update(0.25)

    # Progresso deve ter completado
    assert controller._blend_progress >= 1.0
    assert controller._is_blending == False
