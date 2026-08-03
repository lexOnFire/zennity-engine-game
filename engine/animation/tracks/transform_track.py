from __future__ import annotations
from typing import Any, Dict, List
import numpy as np
from engine.animation.tracks.base_track import AnimationTrack


class TransformTrack(AnimationTrack):
    """Trilha especializada para sequenciar Posição, Rotação e Escala no Transform."""

    def __init__(self, name: str = "TransformTrack", enabled: bool = True) -> None:
        super().__init__(name, enabled)
        self.position_keyframes: List[dict] = []  # [{time, value: [x,y,z]}]
        self.rotation_keyframes: List[dict] = []  # [{time, value: [rx,ry,rz]}]
        self.scale_keyframes: List[dict] = []     # [{time, value: [sx,sy,sz]}]

    def sample(self, time_seconds: float, target: Any) -> None:
        if not self.enabled or target is None or not hasattr(target, "transform"):
            return

        transform = target.transform
        if self.position_keyframes:
            pos = self._sample_vec3(self.position_keyframes, time_seconds, transform.position)
            transform.position = pos

        if self.rotation_keyframes:
            rot = self._sample_vec3(self.rotation_keyframes, time_seconds, transform.rotation)
            transform.rotation = rot

        if self.scale_keyframes:
            scl = self._sample_vec3(self.scale_keyframes, time_seconds, transform.scale)
            transform.scale = scl

    def _sample_vec3(self, keyframes: List[dict], t: float, current: np.ndarray) -> np.ndarray:
        if not keyframes:
            return current
        sorted_kfs = sorted(keyframes, key=lambda k: k["time"])
        if t <= sorted_kfs[0]["time"]:
            return np.array(sorted_kfs[0]["value"], dtype=np.float32)
        if t >= sorted_kfs[-1]["time"]:
            return np.array(sorted_kfs[-1]["value"], dtype=np.float32)

        for left, right in zip(sorted_kfs, sorted_kfs[1:]):
            if left["time"] <= t <= right["time"]:
                span = max(float(right["time"] - left["time"]), 0.000001)
                alpha = (t - float(left["time"])) / span
                v_a = np.array(left["value"], dtype=np.float32)
                v_b = np.array(right["value"], dtype=np.float32)
                return v_a + (v_b - v_a) * alpha
        return current

    def evaluate(self, time_seconds: float) -> dict[str, Any]:
        """Retorna os valores puros de posição, rotação e escala para o instante."""
        dummy_pos = np.zeros(3, dtype=np.float32)
        dummy_rot = np.zeros(3, dtype=np.float32)
        dummy_scl = np.ones(3, dtype=np.float32)
        return {
            "position": self._sample_vec3(self.position_keyframes, time_seconds, dummy_pos),
            "rotation": self._sample_vec3(self.rotation_keyframes, time_seconds, dummy_rot),
            "scale": self._sample_vec3(self.scale_keyframes, time_seconds, dummy_scl),
        }

    def clone(self) -> TransformTrack:
        track = TransformTrack(name=self.name, enabled=self.enabled)
        track.deserialize(self.serialize())
        return track

    def preview(self, time_seconds: float) -> str:
        values = self.evaluate(time_seconds)
        pos = values["position"]
        return f"Transform(pos=[{pos[0]:.1f}, {pos[1]:.1f}, {pos[2]:.1f}])"

    def duration(self) -> float:
        all_times = [
            kf["time"]
            for kfs in (self.position_keyframes, self.rotation_keyframes, self.scale_keyframes)
            for kf in kfs
        ]
        return max(all_times, default=0.0)

    def serialize(self) -> Dict[str, Any]:
        data = super().serialize()
        data.update({
            "position_keyframes": self.position_keyframes,
            "rotation_keyframes": self.rotation_keyframes,
            "scale_keyframes": self.scale_keyframes,
        })
        return data

    def deserialize(self, data: Dict[str, Any]) -> None:
        super().deserialize(data)
        self.position_keyframes = list(data.get("position_keyframes", []))
        self.rotation_keyframes = list(data.get("rotation_keyframes", []))
        self.scale_keyframes = list(data.get("scale_keyframes", []))
