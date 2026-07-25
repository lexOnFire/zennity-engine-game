from __future__ import annotations

from typing import Any, Dict, List, Optional, Set
import numpy as np

from engine.core.services import IService
from engine.core.lifecycle import ServiceScope
from engine.animation.tracks.base_track import AnimationTrack


class AnimationPlaybackState:
    STOPPED = 0
    PLAYING = 1
    PAUSED = 2


class TrackPlaybackState:
    """Gerencia o tempo e amostragem de um conjunto de trilhas (Timeline / Clip)."""

    def __init__(self, name: str, tracks: Optional[List[AnimationTrack]] = None, duration: float = 1.0, loop: bool = True, speed: float = 1.0) -> None:
        self.name = str(name)
        self.tracks: List[AnimationTrack] = list(tracks or [])
        self.duration = max(float(duration), 0.01)
        self.loop = bool(loop)
        self.speed = float(speed)
        self.state = AnimationPlaybackState.STOPPED
        self.current_time = 0.0

    def play(self) -> None:
        self.state = AnimationPlaybackState.PLAYING
        if self.current_time >= self.duration and not self.loop:
            self.current_time = 0.0

    def pause(self) -> None:
        self.state = AnimationPlaybackState.PAUSED

    def stop(self) -> None:
        self.state = AnimationPlaybackState.STOPPED
        self.current_time = 0.0

    def seek(self, time_seconds: float) -> None:
        self.current_time = max(0.0, float(time_seconds))
        if self.loop and self.duration > 0:
            self.current_time = self.current_time % self.duration

    def update(self, delta_time: float, target: Any) -> None:
        if self.state != AnimationPlaybackState.PLAYING:
            return

        dt = float(delta_time) * self.speed
        self.current_time += dt

        if self.current_time >= self.duration:
            if self.loop:
                self.current_time = self.current_time % self.duration
            else:
                self.current_time = self.duration
                self.state = AnimationPlaybackState.STOPPED

        # Sample all active tracks onto target
        for track in self.tracks:
            if track.enabled:
                track.sample(self.current_time, target)


class AnimationPlayerService(IService):
    """
    Serviço central de execução, amostragem e mesclagem de animações da Zennity Engine.
    Atua no Engine Core e gerencia as reproduções desacopladas da interface.
    """

    def __init__(self) -> None:
        super().__init__()
        self.scope = ServiceScope.ENGINE
        self._active_playbacks: Dict[int, List[TrackPlaybackState]] = {}

    def initialize(self) -> None:
        pass

    def shutdown(self) -> None:
        self._active_playbacks.clear()

    def create_playback(self, target: Any, name: str, tracks: List[AnimationTrack], duration: float = 1.0, loop: bool = True, speed: float = 1.0) -> TrackPlaybackState:
        playback = TrackPlaybackState(name, tracks, duration, loop, speed)
        target_id = id(target)
        self._active_playbacks.setdefault(target_id, []).append(playback)
        return playback

    def update(self, delta_time: float, targets_map: Dict[int, Any]) -> None:
        """Executa a atualização de quadros e interpolação de todas as animações ativas."""
        for target_id, playbacks in list(self._active_playbacks.items()):
            target = targets_map.get(target_id)
            if target is None:
                continue
            for pb in playbacks:
                pb.update(delta_time, target)

    def blend_vectors(self, vec_a: np.ndarray, vec_b: np.ndarray, weight: float) -> np.ndarray:
        """Realiza mesclagem (blending) vetorizada usando NumPy."""
        w = max(0.0, min(1.0, float(weight)))
        return vec_a + (vec_b - vec_a) * w
