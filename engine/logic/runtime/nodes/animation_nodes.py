"""Nós de animação para Logic Graph - Play/Pause/Stop + Controller Integration."""
from __future__ import annotations

from typing import Any, Mapping
from ..registry import registry

# Phase 6B.4: Import controller
from engine.animation.animation_controller import AnimationController


def _resolve_animator(target: Any, game: Any) -> tuple[Any, str | None]:
    """Resolve an Animator component from a target name.

    Returns:
        (animator, error_message) where error_message is None on success
    """
    if not target:
        return None, "Target name is empty"

    if not hasattr(game, "find_object"):
        return None, "Game object doesn't support find_object"

    game_obj = game.find_object(str(target))
    if not game_obj:
        return None, f"GameObject '{target}' not found"

    if not hasattr(game_obj, "get_component"):
        return None, f"GameObject '{target}' doesn't support get_component"

    from engine.animation.animator import Animator
    animator = game_obj.get_component(Animator)

    if not animator:
        return None, f"GameObject '{target}' has no Animator component"

    return animator, None


# Phase 6B.4: Animator Controller resolution
def _resolve_animator_controller(target: Any, game: Any) -> tuple[Any, str | None]:
    """Resolve an AnimationController component from a target name.

    Returns:
        (controller, error_message) where error_message is None on success
    """
    if not target:
        return None, "Target name is empty"

    if not hasattr(game, "find_object"):
        return None, "Game object doesn't support find_object"

    game_obj = game.find_object(str(target))
    if not game_obj:
        return None, f"GameObject '{target}' not found"

    if not hasattr(game_obj, "get_component"):
        return None, f"GameObject '{target}' doesn't support get_component"

    controller = game_obj.get_component(AnimationController)

    if not controller:
        return None, f"GameObject '{target}' has no AnimationController component"

    return controller, None


# Phase 6B.2: Play Animation Executor
@registry.register_executor('play_animation')
def execute_play_animation(runtime, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
    """Play an animation on target Animator."""
    node_id = str(node['id'])
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}

    # PHASE 9 recovery item 4.2. This read ``animation_name`` while every saved
    # node stores ``state``, so the author's value was ignored and the seeded
    # default played instead. ``state`` is the authoring property; the legacy
    # name is migrated at load time and kept here only as a defensive fallback
    # for a graph that reaches the runtime without passing the normalizer.
    target_name = str(
        runtime._read_input(node_id, "target", properties.get("target", ""), game, dt, set())
    ).strip()
    state = str(
        runtime._read_input(
            node_id, "state",
            properties.get("state") or properties.get("animation_name", ""),
            game, dt, set(),
        )
    ).strip()
    force = bool(properties.get("force", False))

    if not state:
        return ["exec_failure"]

    animator, error = _resolve_animator(target_name, game)
    if error or not animator:
        return ["exec_failure"]

    try:
        # Validate animation exists before playing
        if state not in animator._clips:
            return ["exec_failure"]

        # Call actual Animator API
        animator.play(state, force=force)
        runtime._store(node_id, "animation", state)
        return ["next"]

    except (ValueError, TypeError, AttributeError):
        return ["exec_failure"]


# Phase 6B.2: Pause Animation Executor
@registry.register_executor('pause_animation')
def execute_pause_animation(runtime, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
    """Pause animation on target Animator."""
    node_id = str(node['id'])
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}

    target_name = str(properties.get("target", "")).strip()

    animator, error = _resolve_animator(target_name, game)
    if error or not animator:
        return ["failure"]

    try:
        animator.pause()
        runtime._store(node_id, "paused", True)
        return ["success"]

    except (ValueError, TypeError, AttributeError):
        return ["failure"]


# Phase 6B.2: Stop Animation Executor
@registry.register_executor('stop_animation')
def execute_stop_animation(runtime, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
    """Stop animation on target Animator."""
    node_id = str(node['id'])
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}

    target_name = str(
        runtime._read_input(node_id, "target", properties.get("target", ""), game, dt, set())
    ).strip()

    animator, error = _resolve_animator(target_name, game)
    if error or not animator:
        return ["exec_failure"]

    try:
        animator.stop()
        runtime._store(node_id, "stopped", True)
        return ["next"]

    except (ValueError, TypeError, AttributeError):
        return ["exec_failure"]


def _parse_animator_param_value(value_str: str, existing_value: Any = None) -> Any:
    """Parse string value into typed value (bool, int, float) based on existing value or auto-detect."""
    if isinstance(existing_value, bool):
        return value_str.lower() in ("true", "1", "yes")
    if isinstance(existing_value, int):
        return int(value_str)
    if isinstance(existing_value, float):
        return float(value_str)
    if value_str.lower() in ("true", "false", "yes", "no", "1", "0"):
        return value_str.lower() in ("true", "yes", "1")
    try:
        return int(value_str) if "." not in value_str else float(value_str)
    except ValueError:
        return value_str.lower() in ("true", "1", "yes")


# Phase 6B.2: Animator Parameter Executor
@registry.register_executor('animator_parameter')
def execute_animator_parameter(runtime, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
    """Set an animator parameter via AnimationController (bool, float, int) or store in runtime (backward compat)."""
    node_id = str(node['id'])
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}

    target_name = str(properties.get("target", "")).strip()
    parameter_name = str(properties.get("parameter_name", "")).strip()
    value_str = str(properties.get("value", "")).strip()

    if not parameter_name or not value_str or not hasattr(game, "find_object"):
        return ["failure"]

    game_obj = game.find_object(target_name) if target_name else None
    if not game_obj:
        return ["failure"]

    controller = game_obj.get_component(AnimationController) if hasattr(game_obj, "get_component") else None

    try:
        existing = controller.get_parameter(parameter_name, None) if controller else None
        value = _parse_animator_param_value(value_str, existing)
        if controller:
            controller.set_parameter(parameter_name, value)
        runtime._store(node_id, parameter_name, value)
        return ["success"]
    except (ValueError, TypeError, AttributeError):
        return ["failure"]



# Phase 6B.4: Set Animator Trigger
@registry.register_executor('animator_set_trigger')
def execute_animator_set_trigger(runtime, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
    """Set an animator trigger parameter (pulse)."""
    node_id = str(node['id'])
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}

    target_name = str(properties.get("target", "")).strip()
    trigger_name = str(properties.get("trigger_name", "")).strip()

    if not trigger_name:
        return ["failure"]

    controller, error = _resolve_animator_controller(target_name, game)
    if error or not controller:
        return ["failure"]

    try:
        # Set trigger to True (will be consumed by controller on next update)
        controller.set_parameter(trigger_name, True)
        runtime._store(node_id, trigger_name, True)
        return ["success"]

    except (ValueError, TypeError, AttributeError):
        return ["failure"]


# Phase 6B.2: Getter Evaluators (Pure Data Nodes)
@registry.register_evaluator('get_current_animation')
def evaluate_get_current_animation(runtime, node_id: str, port_id: str, node: Mapping[str, Any], game: Any, dt: float, visited: set) -> Any:
    """Get current animation name."""
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}
    target_name = str(properties.get("target", "")).strip()

    animator, error = _resolve_animator(target_name, game)
    if error or not animator:
        return ""

    # Return animation name or empty string if none
    return animator.current_clip or ""


@registry.register_evaluator('get_current_frame')
def evaluate_get_current_frame(runtime, node_id: str, port_id: str, node: Mapping[str, Any], game: Any, dt: float, visited: set) -> Any:
    """Get current frame index."""
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}
    target_name = str(properties.get("target", "")).strip()

    animator, error = _resolve_animator(target_name, game)
    if error or not animator:
        return 0

    return int(animator.current_frame)


@registry.register_evaluator('get_animation_time')
def evaluate_get_animation_time(runtime, node_id: str, port_id: str, node: Mapping[str, Any], game: Any, dt: float, visited: set) -> Any:
    """Get animation time (clip time in seconds)."""
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}
    target_name = str(properties.get("target", "")).strip()

    animator, error = _resolve_animator(target_name, game)
    if error or not animator:
        return 0.0

    return float(animator.current_time)


@registry.register_evaluator('get_is_playing')
def evaluate_get_is_playing(runtime, node_id: str, port_id: str, node: Mapping[str, Any], game: Any, dt: float, visited: set) -> Any:
    """Check if animator is playing (not paused, not stopped, not finished)."""
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}
    target_name = str(properties.get("target", "")).strip()

    animator, error = _resolve_animator(target_name, game)
    if error or not animator:
        return False

    # Playing: current clip exists, _playing is True, not paused, not finished
    return bool(animator.is_any_playing)


# Phase 6B.4: Get Animator Parameter (Pure getter)
@registry.register_evaluator('animator_get_parameter')
def evaluate_animator_get_parameter(runtime, node_id: str, port_id: str, node: Mapping[str, Any], game: Any, dt: float, visited: set) -> Any:
    """Get current animator parameter value."""
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}
    target_name = str(properties.get("target", "")).strip()
    parameter_name = str(properties.get("parameter_name", "")).strip()

    controller, error = _resolve_animator_controller(target_name, game)
    if error or not controller:
        return None

    return controller.get_parameter(parameter_name, None)


# Phase 6B.4: Get Animator State (Pure getter)
@registry.register_evaluator('get_animator_state')
def evaluate_get_animator_state(runtime, node_id: str, port_id: str, node: Mapping[str, Any], game: Any, dt: float, visited: set) -> Any:
    """Get current animator controller state name."""
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}
    target_name = str(properties.get("target", "")).strip()

    controller, error = _resolve_animator_controller(target_name, game)
    if error or not controller:
        return ""

    return controller.get_current_state()


# Phase 6B.3: Animation Event Node Evaluators (Event Source Nodes)
@registry.register_evaluator(('on_animation_event', 'on_animation_finished'))
def evaluate_animation_event_nodes(runtime, node_id: str, port_id: str, node: Mapping[str, Any], game: Any, dt: float, visited: set) -> Any:
    """Evaluate data outputs from animation event nodes."""
    port_id = str(port_id)

    if port_id == "owner_object":
        return runtime.values.get((node_id, "owner_object"))
    elif port_id == "animation_name":
        return runtime.values.get((node_id, "animation_name"), "")
    elif port_id == "event_name":
        return runtime.values.get((node_id, "event_name"), "")
    elif port_id == "frame_index":
        return int(runtime.values.get((node_id, "frame_index"), 0))
    elif port_id == "elapsed_time":
        return float(runtime.values.get((node_id, "elapsed_time"), 0.0))
    else:
        return None
