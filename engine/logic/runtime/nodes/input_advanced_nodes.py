"""Nós de input avançado para Logic Graph - Input 100% visual."""
from __future__ import annotations

from typing import Any, Mapping
from ..registry import registry


@registry.register_executor('detect_touch')
def execute_detect_touch(runtime, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
    """Detecta toque em uma área."""
    node_id = str(node['id'])
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}

    try:
        x = float(properties.get("x", 0.0))
        y = float(properties.get("y", 0.0))
        width = float(properties.get("width", 100.0))
        height = float(properties.get("height", 100.0))

        if hasattr(game, "get_touch_input"):
            touches = game.get_touch_input()
            for touch in touches:
                touch_x, touch_y = touch.get("x", 0), touch.get("y", 0)
                if x <= touch_x <= x + width and y <= touch_y <= y + height:
                    runtime._store(node_id, "touch_x", touch_x)
                    runtime._store(node_id, "touch_y", touch_y)
                    return ["touched"]

        return ["no_touch"]
    except Exception as e:
        print(f"Erro em detect_touch: {e}")
        return ["failure"]


@registry.register_executor('detect_swipe')
def execute_detect_swipe(runtime, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
    """Detecta gesto de swipe (deslize)."""
    node_id = str(node['id'])
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}

    try:
        direction = str(properties.get("direction", "right")).lower()  # right, left, up, down
        min_distance = float(properties.get("min_distance", 50.0))

        if hasattr(game, "get_swipe_input"):
            swipe = game.get_swipe_input()
            if swipe:
                swipe_dir = swipe.get("direction", "").lower()
                distance = swipe.get("distance", 0.0)

                if swipe_dir == direction and distance >= min_distance:
                    runtime._store(node_id, "swipe_distance", distance)
                    return ["swiped"]

        return ["no_swipe"]
    except Exception as e:
        print(f"Erro em detect_swipe: {e}")
        return ["failure"]


@registry.register_executor('detect_pinch')
def execute_detect_pinch(runtime, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
    """Detecta gesto de pinça (zoom)."""
    node_id = str(node['id'])
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}

    try:
        gesture_type = str(properties.get("type", "in")).lower()  # in (zoom out), out (zoom in)

        if hasattr(game, "get_pinch_input"):
            pinch = game.get_pinch_input()
            if pinch:
                scale = pinch.get("scale", 1.0)
                pinch_type = "in" if scale < 1.0 else "out"

                if pinch_type == gesture_type:
                    runtime._store(node_id, "pinch_scale", scale)
                    return ["pinched"]

        return ["no_pinch"]
    except Exception as e:
        print(f"Erro em detect_pinch: {e}")
        return ["failure"]


@registry.register_executor('is_key_pressed')
def execute_is_key_pressed(runtime, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
    """Verifica se uma tecla está pressionada AGORA."""
    node_id = str(node['id'])
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}

    try:
        key = str(properties.get("key", "space")).lower()

        if hasattr(game, "is_key_pressed"):
            if game.is_key_pressed(key):
                return ["pressed"]

        return ["not_pressed"]
    except Exception as e:
        print(f"Erro em is_key_pressed: {e}")
        return ["failure"]


@registry.register_executor('wait_key_release')
def execute_wait_key_release(runtime, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
    """Aguarda até uma tecla ser liberada."""
    node_id = str(node['id'])
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}

    try:
        key = str(properties.get("key", "space")).lower()
        timeout = float(properties.get("timeout", 10.0))

        if not hasattr(runtime, "_key_release_trackers"):
            runtime._key_release_trackers = {}

        if node_id not in runtime._key_release_trackers:
            runtime._key_release_trackers[node_id] = {"start_time": __import__('time').time()}

        tracker = runtime._key_release_trackers[node_id]
        elapsed = __import__('time').time() - tracker["start_time"]

        if hasattr(game, "is_key_pressed"):
            if not game.is_key_pressed(key):
                del runtime._key_release_trackers[node_id]
                return ["released"]

        if elapsed > timeout:
            del runtime._key_release_trackers[node_id]
            return ["timeout"]

        return ["waiting"]
    except Exception as e:
        print(f"Erro em wait_key_release: {e}")
        return ["failure"]
