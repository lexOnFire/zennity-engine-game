from __future__ import annotations
from typing import Any, Dict, List
import numpy as np
from engine.animation.tracks.base_track import AnimationTrack


class PropertyTrack(AnimationTrack):
    """Trilha genérica para animar qualquer propriedade numérico/booleana de um Componente ou GameObject."""

    def __init__(self, name: str = "PropertyTrack", component_type: str = "", property_name: str = "", enabled: bool = True) -> None:
        super().__init__(name, enabled)
        self.component_type = component_type
        self.property_name = property_name
        self.keyframes: List[dict] = []  # [{time: float, value: Any}]

    def sample(self, time_seconds: float, target: Any) -> None:
        if not self.enabled or target is None or not self.property_name or not self.keyframes:
            return

        obj = target
        if self.component_type and hasattr(target, "get_component_by_name"):
            comp = target.get_component_by_name(self.component_type)
            if comp is not None:
                obj = comp

        if not hasattr(obj, self.property_name):
            return

        sorted_kfs = sorted(self.keyframes, key=lambda k: k["time"])
        t = float(time_seconds)

        if t <= sorted_kfs[0]["time"]:
            val = sorted_kfs[0]["value"]
        elif t >= sorted_kfs[-1]["time"]:
            val = sorted_kfs[-1]["value"]
        else:
            val = sorted_kfs[-1]["value"]
            for left, right in zip(sorted_kfs, sorted_kfs[1:]):
                if left["time"] <= t <= right["time"]:
                    span = max(float(right["time"] - left["time"]), 0.000001)
                    alpha = (t - float(left["time"])) / span
                    val = self._lerp(left["value"], right["value"], alpha)
                    break

        setattr(obj, self.property_name, val)

    def _lerp(self, a: Any, b: Any, alpha: float) -> Any:
        if isinstance(a, (int, float)) and isinstance(b, (int, float)):
            return float(a) + (float(b) - float(a)) * alpha
        if isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)):
            length = min(len(a), len(b))
            return [float(a[i]) + (float(b[i]) - float(a[i])) * alpha for i in range(length)]
        return b if alpha >= 1.0 else a

    def evaluate(self, time_seconds: float) -> Any:
        if not self.keyframes:
            return None
        sorted_kfs = sorted(self.keyframes, key=lambda k: k["time"])
        t = float(time_seconds)
        if t <= sorted_kfs[0]["time"]:
            return sorted_kfs[0]["value"]
        if t >= sorted_kfs[-1]["time"]:
            return sorted_kfs[-1]["value"]
        for left, right in zip(sorted_kfs, sorted_kfs[1:]):
            if left["time"] <= t <= right["time"]:
                span = max(float(right["time"] - left["time"]), 0.000001)
                alpha = (t - float(left["time"])) / span
                return self._lerp(left["value"], right["value"], alpha)
        return sorted_kfs[-1]["value"]

    def clone(self) -> PropertyTrack:
        track = PropertyTrack(name=self.name, component_type=self.component_type, property_name=self.property_name, enabled=self.enabled)
        track.deserialize(self.serialize())
        return track

    def preview(self, time_seconds: float) -> str:
        val = self.evaluate(time_seconds)
        prop = self.property_name or "Property"
        return f"{prop}={val}"

    def duration(self) -> float:
        return max((float(kf.get("time", 0.0)) for kf in self.keyframes), default=0.0)

    def serialize(self) -> Dict[str, Any]:
        data = super().serialize()
        data.update({
            "component_type": self.component_type,
            "property_name": self.property_name,
            "keyframes": self.keyframes,
        })
        return data

    def deserialize(self, data: Dict[str, Any]) -> None:
        super().deserialize(data)
        self.component_type = str(data.get("component_type", ""))
        self.property_name = str(data.get("property_name", ""))
        self.keyframes = list(data.get("keyframes", []))
