"""
AudioManager — Sistema de áudio simples para a Zennity Engine.
Uso em scripts:
    from engine.audio import AudioManager
    AudioManager.play('sons/pulo.wav')
    AudioManager.stop_all()
"""
from __future__ import annotations
import os
from typing import Dict
import pygame


class AudioManager:
    _channels: Dict[str, pygame.mixer.Channel] = {}
    _initialized: bool = False

    @classmethod
    def _init(cls) -> bool:
        if cls._initialized:
            return True
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
            cls._initialized = True
            return True
        except Exception as e:
            print(f"[AudioManager] Não foi possível inicializar o mixer: {e}")
            return False

    @classmethod
    def play(cls, path: str, loop: bool = False, volume: float = 1.0) -> None:
        """Toca um arquivo de áudio (.wav ou .ogg). loop=True repete infinitamente."""
        if not cls._init():
            return
        if not os.path.exists(path):
            print(f"[AudioManager] Arquivo não encontrado: {path}")
            return
        try:
            sound = pygame.mixer.Sound(path)
            sound.set_volume(max(0.0, min(1.0, volume)))
            ch = sound.play(-1 if loop else 0)
            cls._channels[path] = ch
        except Exception as e:
            print(f"[AudioManager] Erro ao tocar '{path}': {e}")

    @classmethod
    def stop(cls, path: str) -> None:
        """Para o som de um arquivo específico."""
        ch = cls._channels.get(path)
        if ch:
            ch.stop()
            del cls._channels[path]

    @classmethod
    def stop_all(cls) -> None:
        """Para todos os sons."""
        pygame.mixer.stop()
        cls._channels.clear()

    @classmethod
    def set_volume(cls, path: str, volume: float) -> None:
        """Ajusta o volume de um som em reprodução (0.0 a 1.0)."""
        ch = cls._channels.get(path)
        if ch:
            ch.set_volume(max(0.0, min(1.0, volume)))
