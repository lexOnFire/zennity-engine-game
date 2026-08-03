"""Short English code previews for visual logic nodes."""
from __future__ import annotations

from typing import Any, Mapping


def _value(properties: Mapping[str, Any], name: str, default: Any) -> Any:
    return properties.get(name, default)


def node_code_preview(node: Mapping[str, Any]) -> str:
    """Return compact English pseudocode that fits inside a visual node."""
    node_type = str(node.get("type", ""))
    properties = node.get("properties", {}) if isinstance(node.get("properties"), Mapping) else {}
    previews = {
        "event_start": "on_start():\n    run next",
        "event_update": "on_update(dt):\n    run next",
        "event_timer": f"every({_value(properties, 'seconds', 1.0)}s):\n    run next",
        "event_key_pressed": f"on_key_pressed('{_value(properties, 'key', 'D')}'):\n    run next",
        "event_object_created": "on_object_created(new_object):\n    current_target = new_object",
        "input_axis": f"axis = key('{_value(properties, 'positive', 'D')}')\n     - key('{_value(properties, 'negative', 'A')}')",
        "move": f"target.x += input * {_value(properties, 'speed', 200)} * dt",
        "move_by": f"target.x += {_value(properties, 'x', 100)} * dt\ntarget.y += {_value(properties, 'y', 0)} * dt",
        "start_continuous_motion": (
            f"motion = start_motion('{_value(properties, 'movement', 'Movement')}', "
            f"x={_value(properties, 'x', 100)}, y={_value(properties, 'y', 0)}, "
            f"space='{_value(properties, 'space', 'global')}')"
        ),
        "update_continuous_motion": f"update_motion('{_value(properties, 'movement', 'Movement')}', x={_value(properties, 'x', 100)}, y={_value(properties, 'y', 0)})",
        "pause_continuous_motion": f"pause_motion('{_value(properties, 'movement', 'Movement')}')",
        "resume_continuous_motion": f"resume_motion('{_value(properties, 'movement', 'Movement')}')",
        "stop_continuous_motion": f"stop_motion('{_value(properties, 'movement', 'all')}')",
        "get_continuous_motion": f"state = get_motion('{_value(properties, 'movement', 'Movement')}')",
        "get_position": "x = target.x\ny = target.y",
        "patrol_axis": (
            f"if position >= {_value(properties, 'maximum', 100)}: direction = -1\n"
            f"if position <= {_value(properties, 'minimum', -100)}: direction = 1\n"
            f"position += direction * {_value(properties, 'speed', 100)} * dt"
        ),
        "jump": f"if grounded:\n    jump({_value(properties, 'force', 420)})",
        "if_else": f"if {_value(properties, 'condition', True)}:\n    true output\nelse:\n    false output",
        "key_pressed": f"pressed = key_pressed('{_value(properties, 'key', 'SPACE')}')",
        "key_held": f"held = key_down('{_value(properties, 'key', 'SPACE')}')",
        "compare_number": f"result = input {_value(properties, 'operator', '>')} {_value(properties, 'value', 0)}",
        "set_position": f"target.x = {_value(properties, 'x', 0)}\ntarget.y = {_value(properties, 'y', 0)}",
        "rotate": f"target.rotation += {_value(properties, 'degrees', 90)}",
        "set_active": f"target.active = {_value(properties, 'active', True)}",
        "destroy_object": "target.destroy()",
        "destroy_after_time": f"target.destroy_after({_value(properties, 'seconds', 2)}s)",
        "play_animation": f"animator.play('{_value(properties, 'state', 'Idle')}')",
        "play_animation_asset": f"play_animation(\n  '{_value(properties, 'path', 'select .zanim')}'\n)",
        "stop_animation": "stop_animation()",
        "play_sound": f"play_sound(\n  '{_value(properties, 'path', 'select audio')}'\n)",
        "set_sprite": f"target.sprite =\n  '{_value(properties, 'path', 'select image')}'",
        "start_texture_scroll": (
            f"start_texture_scroll(x={_value(properties, 'speed_x', 0)}, "
            f"y={_value(properties, 'speed_y', 80)}, parallax={_value(properties, 'parallax', 1)})"
        ),
        "stop_texture_scroll": f"stop_texture_scroll(reset={_value(properties, 'reset', False)})",
        "set_hud": f"hud.text = '{_value(properties, 'text', 'Text')}'",
        "log_message": f"console.log('{_value(properties, 'text', 'Message')}')",
        "find_tag": f"object = find_tag('{_value(properties, 'tag', 'Player')}')",
        "get_tag": "tag = target.tag",
        "get_prefab_parameter": f"value = target.prefab_param('{_value(properties, 'name', 'speed')}')",
        "create_object": (
            f"new_object = create_object('{_value(properties, 'name', 'NewObject')}',\n"
            f"  x={_value(properties, 'x', 0)}, y={_value(properties, 'y', 0)},\n"
            f"  max={_value(properties, 'max_instances', 0)}, lifetime={_value(properties, 'lifetime', 0)}s)"
        ),
        "create_prefab": (
            f"new_object = create_prefab('{_value(properties, 'path', 'select .zprefab')}',\n"
            f"  override_position={_value(properties, 'override_position', True)}, "
            f"override_rotation={_value(properties, 'override_rotation', False)},\n"
            f"  override_scale={_value(properties, 'override_scale', False)}, "
            f"include_camera={_value(properties, 'include_camera', False)}, "
            f"include_audio={_value(properties, 'include_audio', False)}, "
            f"include_logic={_value(properties, 'include_logic', False)},\n"
            f"  parameters={_value(properties, 'parameters', {})})"
        ),
        "clone_object": "copy = clone(target)",
        "add_component": f"target.add_component('{_value(properties, 'component', 'BoxCollider')}')",
        "remove_component": f"target.remove_component('{_value(properties, 'component', 'BoxCollider')}')",
        "once": "if not_ran_yet:\n    run next",
        "compare_text": f"result = text {_value(properties, 'operator', '==')} '{_value(properties, 'value', 'Text')}'",
        "cooldown": f"if elapsed({_value(properties, 'seconds', 1.0)}s):\n    run next",
        "restart_scene": "restart_scene()",
        "get_variable": f"value = get_variable('{_value(properties, 'name', 'value')}')",
        "set_variable": f"set_variable('{_value(properties, 'name', 'value')}', input)",
        "number_value": f"value = {_value(properties, 'value', 0)}",
        "bool_value": f"value = {_value(properties, 'value', True)}",
        "text_value": f"value = '{_value(properties, 'value', 'Text')}'",
        "add_number": "value = a + b",
        "subtract_number": "value = a - b",
        "multiply_number": "value = a * b",
        "divide_number": "value = a / b",
        "join_text": "text = text_a + text_b",
        "to_text": "text = str(value)",
        "emit_event": f"emit_event('{_value(properties, 'name', 'event')}')",
    }
    if node_type in previews:
        return previews[node_type]
    title = str(node.get("title", node_type or "node")).replace(" ", "_").lower()
    arguments = ", ".join(f"{key}={value!r}" for key, value in list(properties.items())[:2])
    return f"{title}({arguments})" if arguments else f"{title}()"
