"""Nós de câmera avançada para Logic Graph - Câmera 100% visual."""
from __future__ import annotations

import time
from typing import Any, Mapping
from ..registry import registry


@registry.register_executor('camera_shake')
def execute_camera_shake(runtime, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
    """Sacode a câmera."""
    node_id = str(node['id'])
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}

    try:
        duration = float(properties.get("duration", 0.5))
        intensity = float(properties.get("intensity", 5.0))
        frequency = float(properties.get("frequency", 10.0))

        if hasattr(game, "camera_shake"):
            game.camera_shake(duration, intensity, frequency)
            runtime._store(node_id, "shaking", True)
            return ["exec_shaking"]

        return ["exec_failure"]
    except Exception as e:
        print(f"Erro em camera_shake: {e}")
        return ["exec_failure"]


@registry.register_executor('camera_follow')
def execute_camera_follow(runtime, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
    """Câmera segue um objeto."""
    node_id = str(node['id'])
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}

    try:
        target_name = str(properties.get("target", ""))
        smooth_time = float(properties.get("smooth_time", 0.3))  # Lerp smoothing

        if target_name and hasattr(game, "camera_follow"):
            game.camera_follow(target_name, smooth_time)
            runtime._store(node_id, "following", True)
            return ["exec_following"]

        return ["exec_failure"]
    except Exception as e:
        print(f"Erro em camera_follow: {e}")
        return ["exec_failure"]


@registry.register_executor('camera_stop_follow')
def execute_camera_stop_follow(runtime, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
    """Para de seguir o alvo."""
    try:
        if hasattr(game, "camera_stop_follow"):
            game.camera_stop_follow()
        return ["next"]
    except Exception as e:
        print(f"Erro em camera_stop_follow: {e}")
        return ["exec_failure"]


@registry.register_executor('camera_look_at')
def execute_camera_look_at(runtime, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
    """Câmera olha para uma posição."""
    node_id = str(node['id'])
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}

    try:
        x = float(properties.get("x", 0.0))
        y = float(properties.get("y", 0.0))
        duration = float(properties.get("duration", 1.0))  # Tempo para alcançar a posição

        if hasattr(game, "camera_look_at"):
            game.camera_look_at(x, y, duration)
            return ["exec_looking"]

        return ["exec_failure"]
    except Exception as e:
        print(f"Erro em camera_look_at: {e}")
        return ["exec_failure"]


@registry.register_executor('camera_set_zoom')
def execute_camera_set_zoom(runtime, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
    """Define o zoom da câmera."""
    node_id = str(node['id'])
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}

    try:
        zoom = float(properties.get("zoom", 1.0))
        duration = float(properties.get("duration", 0.5))

        if hasattr(game, "camera_set_zoom"):
            game.camera_set_zoom(zoom, duration)
            runtime._store(node_id, "zoom", zoom)
            return ["next"]

        return ["exec_failure"]
    except Exception as e:
        print(f"Erro em camera_set_zoom: {e}")
        return ["exec_failure"]
