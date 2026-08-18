"""Nós de audio avançado para Logic Graph - Audio 100% visual."""
from __future__ import annotations

import os
from typing import Any, Mapping
import pygame
from engine.audio import AudioManager
from ..registry import registry


@registry.register_executor('play_sound_fade')
def execute_play_sound_fade(runtime, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
    """Toca som com fade in/out via AudioManager/pygame.mixer."""
    node_id = str(node['id'])
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}

    try:
        path = str(properties.get("path", "") or "").strip()
        fade_in = float(properties.get("fade_in", 0.0))
        volume = float(properties.get("volume", 1.0))
        fade_ms = max(0, int(fade_in * 1000))

        if not path:
            return ["exec_failure"]

        if hasattr(game, "play_sound_fade"):
            game.play_sound_fade(path, fade_in, float(properties.get("fade_out", 0.0)), volume)
            return ["exec_playing"]

        # Suporte a streaming de música ou SFX com fade
        if path.lower().endswith((".mp3", ".ogg", ".mid")):
            if os.path.exists(path):
                AudioManager.play_music(path, loop=False, fade_ms=fade_ms)
                return ["exec_playing"]

        # SFX com fade via Pygame Sound
        if os.path.exists(path):
            if not pygame.mixer.get_init():
                try:
                    pygame.mixer.init()
                except Exception:
                    return ["exec_failure"]
            snd = AudioManager._load_sfx(path) if hasattr(AudioManager, "_load_sfx") else None
            if snd is None:
                snd = pygame.mixer.Sound(path)
            snd.set_volume(max(0.0, min(1.0, volume)))
            snd.play(fade_ms=fade_ms)
            return ["exec_playing"]

        return ["exec_failure"]
    except Exception as e:
        print(f"Erro em play_sound_fade: {e}")
        return ["exec_failure"]


@registry.register_executor('set_volume')
def execute_set_volume(runtime, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
    """Define volume de um canal de áudio via AudioManager."""
    node_id = str(node['id'])
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}

    try:
        volume = max(0.0, min(1.0, float(properties.get("volume", 1.0))))
        channel = str(properties.get("channel", "master")).lower().strip()

        if hasattr(game, "set_volume"):
            game.set_volume(volume, channel)
            runtime._store(node_id, "volume", volume)
            return ["exec_success"]

        if channel == "music":
            AudioManager.set_music_volume(volume)
        elif channel == "sfx":
            AudioManager.set_sfx_volume(volume)
        else:
            AudioManager.set_master_volume(volume)

        runtime._store(node_id, "volume", volume)
        return ["exec_success"]
    except Exception as e:
        print(f"Erro em set_volume: {e}")
        return ["exec_failure"]


@registry.register_executor('set_pitch')
def execute_set_pitch(runtime, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
    """Define pitch (velocidade) de um som. Retorna falha explícita se pitch != 1.0 (não suportado pelo backend SDL)."""
    node_id = str(node['id'])
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}

    try:
        pitch = float(properties.get("pitch", 1.0))

        if hasattr(game, "set_pitch"):
            game.set_pitch(pitch)
            runtime._store(node_id, "pitch", pitch)
            return ["exec_success"]

        # Backend SDL / Pygame standard mixer não possui DSP de pitch em tempo real
        if abs(pitch - 1.0) < 1e-4:
            runtime._store(node_id, "pitch", 1.0)
            return ["exec_success"]

        # Pitch != 1.0 é não suportado pelo backend atual: falha explícita e honesta
        return ["exec_failure"]
    except Exception as e:
        print(f"Erro em set_pitch: {e}")
        return ["exec_failure"]


@registry.register_executor('stop_all_sounds')
def execute_stop_all_sounds(runtime, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
    """Para todos os sons tocando via backend/AudioManager."""
    try:
        if hasattr(game, "stop_all_sounds"):
            game.stop_all_sounds()
            return ["exec_success"]

        if pygame.mixer.get_init():
            pygame.mixer.stop()
            AudioManager.stop_music()
            return ["exec_success"]

        return ["exec_failure"]
    except Exception as e:
        print(f"Erro em stop_all_sounds: {e}")
        return ["exec_failure"]
