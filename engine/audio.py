from __future__ import annotations
import os
from typing import Dict, List, Optional, Any
import pygame
from engine.core.component import Component
from engine.logger import Logger


class AudioManager:
    """
    Gerenciador central de áudio da Zennity Engine.
    Controla reprodução global, cache de sons e registro de componentes de áudio.
    """
    _initialized: bool = False
    _sound_cache: Dict[str, pygame.mixer.Sound] = {}
    _sources: List[AudioSource] = []
    _listeners: List[AudioListener] = []

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
            Logger.error(f"[AudioManager] Mixer não inicializado: {e}")
            return False

    # ------------------------------------------------------------------
    # Música (pygame.mixer.music — streaming)
    # ------------------------------------------------------------------

    @classmethod
    def play_music(cls, path: str, loop: bool = True, fade_ms: int = 0) -> None:
        """Toca música de fundo com streaming. loop=True repete infinitamente."""
        if not cls._init() or not os.path.exists(path):
            Logger.error(f"[AudioManager] Música não encontrada: {path}")
            return
        try:
            pygame.mixer.music.load(path)
            vol = cls._master_volume * cls._music_volume
            pygame.mixer.music.set_volume(max(0.0, min(1.0, vol)))
            pygame.mixer.music.play(-1 if loop else 0, fade_ms=fade_ms)
            cls._music_path = path
            cls._music_paused = False
        except Exception as e:
            Logger.error(f"[AudioManager] Erro ao tocar música '{path}': {e}")

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
                Logger.error(f"[AudioManager] SFX não encontrado: {path}")
                return None
            try:
                cls._sound_cache[path] = pygame.mixer.Sound(path)
            except Exception as e:
                Logger.error(f"[AudioManager] Erro ao carregar SFX '{path}': {e}")
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

    # ------------------------------------------------------------------
    # Component Registry
    # ------------------------------------------------------------------

    @classmethod
    def register_audio_source(cls, source: AudioSource) -> None:
        """Registra um AudioSource ativo."""
        if source not in cls._sources:
            cls._sources.append(source)

    @classmethod
    def remove_audio_source(cls, source: AudioSource) -> None:
        """Remove um AudioSource registrado."""
        if source in cls._sources:
            cls._sources.remove(source)

    @classmethod
    def register_audio_listener(cls, listener: AudioListener) -> None:
        """Registra um AudioListener ativo."""
        if listener not in cls._listeners:
            cls._listeners.append(listener)

    @classmethod
    def remove_audio_listener(cls, listener: AudioListener) -> None:
        """Remove um AudioListener registrado."""
        if listener in cls._listeners:
            cls._listeners.remove(listener)

    @classmethod
    def get_active_listener(cls) -> Optional[AudioListener]:
        """Retorna o AudioListener ativo mais recentemente registrado."""
        for listener in reversed(cls._listeners):
            if listener.enabled:
                return listener
        return None

    @classmethod
    def clear(cls) -> None:
        """Interrompe sons e limpa o registro de componentes de áudio."""
        try:
            cls.stop_all()
        except Exception:
            cls._music_path = None
            cls._music_paused = False
        try:
            cls.unload_cache()
        except Exception:
            cls._sound_cache.clear()
        cls._sources.clear()
        cls._listeners.clear()


class AudioSource(Component):
    """
    Componente responsável pela reprodução de clipes de áudio no runtime.
    """
    component_type = "AudioSource"

    def __init__(
        self,
        audio_clip: str = "",
        volume: float = 1.0,
        pitch: float = 1.0,
        loop: bool = False,
        play_on_awake: bool = False,
        mute: bool = False
    ) -> None:
        super().__init__()
        self.audio_clip = str(audio_clip)
        self.volume = float(volume)
        self.pitch = float(pitch)
        self.loop = bool(loop)
        self.play_on_awake = bool(play_on_awake)
        self.mute = bool(mute)
        self._channel: Optional[pygame.mixer.Channel] = None
        self._playing = False

    def start(self) -> None:
        """Registra o AudioSource no AudioManager."""
        AudioManager.register_audio_source(self)

    def on_runtime_start(self) -> None:
        """Registra no AudioManager do runtime e inicia reprodução se play_on_awake."""
        AudioManager.register_audio_source(self)
        if self.play_on_awake and self.enabled:
            self.play()

    def play(self) -> None:
        """Inicia a reprodução do clipe de áudio."""
        if not self.enabled or not self.audio_clip:
            return
        loops = -1 if self.loop else 0
        vol = 0.0 if self.mute else self.volume
        self._channel = AudioManager.play_sfx(self.audio_clip, volume=vol, loops=loops)
        self._playing = True

    def stop(self) -> None:
        """Interrompe a reprodução do áudio."""
        if self._channel:
            self._channel.stop()
            self._channel = None
        self._playing = False

    def pause(self) -> None:
        """Pausa a reprodução do canal de áudio."""
        if self._channel:
            self._channel.pause()

    def unpause(self) -> None:
        """Retoma a reprodução pausada do canal de áudio."""
        if self._channel:
            self._channel.unpause()

    def is_playing(self) -> bool:
        """Retorna True se o áudio está sendo reproduzido no momento."""
        if self._channel:
            return self._channel.get_busy()
        return False

    def destroy(self) -> None:
        """Para a reprodução e desregistra o componente do AudioManager."""
        self.stop()
        AudioManager.remove_audio_source(self)
        super().destroy()

    def serialize_properties(self) -> dict[str, Any]:
        """Serializa os parâmetros de áudio."""
        return {
            "audio_clip": self.audio_clip,
            "volume": self.volume,
            "pitch": self.pitch,
            "loop": self.loop,
            "play_on_awake": self.play_on_awake,
            "mute": self.mute
        }

    def deserialize_properties(self, data: dict[str, Any]) -> None:
        """Deserializa os parâmetros de áudio."""
        self.audio_clip = str(data.get("audio_clip", self.audio_clip))
        self.volume = float(data.get("volume", self.volume))
        self.pitch = float(data.get("pitch", self.pitch))
        self.loop = bool(data.get("loop", self.loop))
        self.play_on_awake = bool(data.get("play_on_awake", self.play_on_awake))
        self.mute = bool(data.get("mute", self.mute))


class AudioListener(Component):
    """
    Componente receptor de áudio. Apenas um Listener ativo existe na cena.
    """
    component_type = "AudioListener"

    def start(self) -> None:
        """Registra o AudioListener no AudioManager."""
        AudioManager.register_audio_listener(self)

    def on_runtime_start(self) -> None:
        """Registra o AudioListener no AudioManager do runtime."""
        AudioManager.register_audio_listener(self)

    def destroy(self) -> None:
        """Desregistra o AudioListener do AudioManager."""
        AudioManager.remove_audio_listener(self)
        super().destroy()

