"""Nós de audio avançado para Logic Graph - Audio 100% visual."""
from __future__ import annotations

import time
from typing import Any, Mapping
from ..registry import registry


@registry.register_executor('play_sound_fade')
def execute_play_sound_fade(runtime, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
    """Toca som com fade in/out."""
    node_id = str(node['id'])
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}

    try:
        path = str(properties.get("path", ""))
        fade_in = float(properties.get("fade_in", 0.0))
        fade_out = float(properties.get("fade_out", 0.0))
        volume = float(properties.get("volume", 1.0))

        if path and hasattr(game, "play_sound_fade"):
            game.play_sound_fade(path, fade_in, fade_out, volume)
            return ["exec_playing"]
        elif path and hasattr(game, "play_sound"):
            game.play_sound(path)
            return ["exec_playing"]

        return ["exec_failure"]
    except Exception as e:
        print(f"Erro em play_sound_fade: {e}")
        return ["exec_failure"]


@registry.register_executor('set_volume')
def execute_set_volume(runtime, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
    """Define volume de um som ou música."""
    node_id = str(node['id'])
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}

    try:
        volume = float(properties.get("volume", 1.0))
        channel = str(properties.get("channel", "master")).lower()  # master, sfx, music

        if hasattr(game, "set_volume"):
            game.set_volume(volume, channel)
            runtime._store(node_id, "volume", volume)
            return ["exec_success"]

        return ["exec_failure"]
    except Exception as e:
        print(f"Erro em set_volume: {e}")
        return ["exec_failure"]


@registry.register_executor('set_pitch')
def execute_set_pitch(runtime, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
    """Define pitch (velocidade) de um som."""
    node_id = str(node['id'])
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}

    try:
        pitch = float(properties.get("pitch", 1.0))  # 1.0 = normal, 2.0 = dobrado

        if hasattr(game, "set_pitch"):
            game.set_pitch(pitch)
            runtime._store(node_id, "pitch", pitch)
            return ["exec_success"]

        return ["exec_failure"]
    except Exception as e:
        print(f"Erro em set_pitch: {e}")
        return ["exec_failure"]


@registry.register_executor('stop_all_sounds')
def execute_stop_all_sounds(runtime, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
    """Para todos os sons tocando."""
    try:
        if hasattr(game, "stop_all_sounds"):
            game.stop_all_sounds()
        return ["exec_success"]
    except Exception as e:
        print(f"Erro em stop_all_sounds: {e}")
        return ["exec_failure"]
