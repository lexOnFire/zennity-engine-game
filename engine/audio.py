"""
AudioManager — Sistema de áudio completo para a Zennity Engine.

Uso:
    from engine.audio import AudioManager

    # Música (streaming — ideal para trilhas longas)
    AudioManager.play_music("assets/music/theme.ogg", loop=True, fade_ms=1000)
    AudioManager.set_music_volume(0.6)
    AudioManager.pause_music()
    AudioManager.resume_music()
    AudioManager.stop_music(fade_ms=500)

    # SFX (cache em RAM — ideal para sons curtos)
    AudioManager.play_sfx("assets/sfx/jump.wav", volume=0.8)
    AudioManager.play_sfx("assets/sfx/shoot.wav")

    # Volume global
    AudioManager.set_master_volume(0.5)   # 50% em tudo
    AudioManager.set_sfx_volume(0.8)
    AudioManager.stop_all()
"""
from __future__ import annotations
import os
from typing import Dict, Optional
import pygame


class AudioManager:
    _initialized: bool = False
    _sound_cache: Dict[str, pygame.mixer.Sound] = {}

    _master_volume: float = 1.0
    _sfx_volume: float = 1.0
    _music_volume: float = 1.0

    _music_path: Optional[str] = None
    _music_paused: bool = False

    # ------------------------------------------------------------------
    # Inicialização
    # ------------------------------------------------------------------

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
            print(f"[AudioManager] Mixer não inicializado: {e}")
            return False

    # ------------------------------------------------------------------
    # Música (pygame.mixer.music — streaming)
    # ------------------------------------------------------------------

    @classmethod
    def play_music(cls, path: str, loop: bool = True, fade_ms: int = 0) -> None:
        """Toca música de fundo com streaming. loop=True repete infinitamente."""
        if not cls._init() or not os.path.exists(path):
            print(f"[AudioManager] Música não encontrada: {path}")
            return
        try:
            pygame.mixer.music.load(path)
            vol = cls._master_volume * cls._music_volume
            pygame.mixer.music.set_volume(max(0.0, min(1.0, vol)))
            pygame.mixer.music.play(-1 if loop else 0, fade_ms=fade_ms)
            cls._music_path = path
            cls._music_paused = False
        except Exception as e:
            print(f"[AudioManager] Erro ao tocar música '{path}': {e}")

    @classmethod
    def stop_music(cls, fade_ms: int = 0) -> None:
        """Para a música atual, com fade opcional em milissegundos."""
        if fade_ms > 0:
            pygame.mixer.music.fadeout(fade_ms)
        else:
            pygame.mixer.music.stop()
        cls._music_path = None
        cls._music_paused = False

    @classmethod
    def pause_music(cls) -> None:
        """Pausa a música sem perder a posição."""
        if not cls._music_paused:
            pygame.mixer.music.pause()
            cls._music_paused = True

    @classmethod
    def resume_music(cls) -> None:
        """Retoma a música de onde parou."""
        if cls._music_paused:
            pygame.mixer.music.unpause()
            cls._music_paused = False

    @classmethod
    def is_music_playing(cls) -> bool:
        """Retorna True se a música estiver tocando (não pausada)."""
        return pygame.mixer.music.get_busy() and not cls._music_paused

    @classmethod
    def set_music_volume(cls, volume: float) -> None:
        """Volume da música (0.0–1.0). Multiplicado pelo master."""
        cls._music_volume = max(0.0, min(1.0, volume))
        pygame.mixer.music.set_volume(cls._master_volume * cls._music_volume)

    # ------------------------------------------------------------------
    # SFX (pygame.mixer.Sound — cache em memória)
    # ------------------------------------------------------------------

    @classmethod
    def _load_sfx(cls, path: str) -> Optional[pygame.mixer.Sound]:
        """Carrega e cacheia um Sound. Retorna None se falhar."""
        if path not in cls._sound_cache:
            if not os.path.exists(path):
                print(f"[AudioManager] SFX não encontrado: {path}")
                return None
            try:
                cls._sound_cache[path] = pygame.mixer.Sound(path)
            except Exception as e:
                print(f"[AudioManager] Erro ao carregar SFX '{path}': {e}")
                return None
        return cls._sound_cache[path]

    @classmethod
    def play_sfx(
        cls,
        path: str,
        volume: float = 1.0,
        loops: int = 0,
    ) -> Optional[pygame.mixer.Channel]:
        """
        Toca um efeito sonoro. Retorna o Channel para controle manual.
        loops=0 → toca uma vez; loops=-1 → loop infinito.
        """
        if not cls._init():
            return None
        sound = cls._load_sfx(path)
        if sound is None:
            return None
        effective_vol = max(0.0, min(1.0, volume * cls._sfx_volume * cls._master_volume))
        sound.set_volume(effective_vol)
        return sound.play(loops)

    @classmethod
    def stop_sfx(cls, path: str) -> None:
        """Para todas as instâncias de um SFX específico."""
        sound = cls._sound_cache.get(path)
        if sound:
            sound.stop()

    @classmethod
    def set_sfx_volume(cls, volume: float) -> None:
        """Volume master de todos os SFX (0.0–1.0). Reaplica nos sons cacheados."""
        cls._sfx_volume = max(0.0, min(1.0, volume))
        for sound in cls._sound_cache.values():
            sound.set_volume(cls._sfx_volume * cls._master_volume)

    # ------------------------------------------------------------------
    # Volume Global
    # ------------------------------------------------------------------

    @classmethod
    def set_master_volume(cls, volume: float) -> None:
        """Escala todo o áudio (0.0–1.0). Reaplica em música e cache de SFX."""
        cls._master_volume = max(0.0, min(1.0, volume))
        pygame.mixer.music.set_volume(cls._master_volume * cls._music_volume)
        for sound in cls._sound_cache.values():
            sound.set_volume(cls._sfx_volume * cls._master_volume)

    # ------------------------------------------------------------------
    # Controle Global
    # ------------------------------------------------------------------

    @classmethod
    def pause_all(cls) -> None:
        """Pausa música e todos os canais de SFX."""
        cls.pause_music()
        pygame.mixer.pause()

    @classmethod
    def resume_all(cls) -> None:
        """Retoma música e todos os canais de SFX."""
        cls.resume_music()
        pygame.mixer.unpause()

    @classmethod
    def stop_all(cls) -> None:
        """Para tudo e limpa o estado de música."""
        cls.stop_music()
        pygame.mixer.stop()

    @classmethod
    def unload_cache(cls) -> None:
        """Libera todos os SFX da memória. Útil ao trocar de cena."""
        for sound in cls._sound_cache.values():
            sound.stop()
        cls._sound_cache.clear()
