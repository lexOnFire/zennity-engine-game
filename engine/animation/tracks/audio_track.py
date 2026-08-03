from __future__ import annotations
from typing import Any, Dict, List
from engine.animation.tracks.base_track import AnimationTrack


class AudioTrack(AnimationTrack):
    """Trilha para disparar efeitos sonoros e músicas em carimbos de tempo específicos."""

    def __init__(self, name: str = "AudioTrack", enabled: bool = True) -> None:
        super().__init__(name, enabled)
        self.keyframes: List[dict] = []  # [{time: float, audio_path: str, volume: float}]
        self._last_sampled_time: float = -1.0

    def sample(self, time_seconds: float, target: Any) -> None:
        if not self.enabled or not self.keyframes:
            return

        t = float(time_seconds)
        for kf in self.keyframes:
            kf_time = float(kf.get("time", 0.0))
            if self._last_sampled_time < kf_time <= t:
                audio_path = kf.get("audio_path")
                volume = float(kf.get("volume", 1.0))
                if audio_path:
                    from engine.assets import Assets
                    sound = Assets.get_sound(audio_path)
                    if hasattr(sound, "set_volume"):
                        sound.set_volume(volume)
                    if hasattr(sound, "play"):
                        sound.play()
        self._last_sampled_time = t

    def evaluate(self, time_seconds: float) -> dict[str, Any]:
        triggered = []
        for kf in self.keyframes:
            if float(kf.get("time", 0.0)) <= time_seconds:
                triggered.append(kf)
        return {"triggered": triggered}

    def clone(self) -> AudioTrack:
        track = AudioTrack(name=self.name, enabled=self.enabled)
        track.deserialize(self.serialize())
        return track

    def preview(self, time_seconds: float) -> str:
        data = self.evaluate(time_seconds)
        count = len(data.get("triggered", []))
        return f"Audio(triggered={count})"

    def duration(self) -> float:
        return max((float(kf.get("time", 0.0)) for kf in self.keyframes), default=0.0)

    def serialize(self) -> Dict[str, Any]:
        data = super().serialize()
        data["keyframes"] = self.keyframes
        return data

    def deserialize(self, data: Dict[str, Any]) -> None:
        super().deserialize(data)
        self.keyframes = list(data.get("keyframes", []))
        self._last_sampled_time = -1.0
