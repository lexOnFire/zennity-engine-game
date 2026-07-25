from __future__ import annotations
from typing import Any, Dict, List
from engine.animation.tracks.base_track import AnimationTrack


class EventTrack(AnimationTrack):
    """Trilha para disparar eventos genéricos no EventBus em instantes de tempo específicos."""

    def __init__(self, name: str = "EventTrack", enabled: bool = True) -> None:
        super().__init__(name, enabled)
        self.keyframes: List[dict] = []  # [{time: float, event_name: str, payload: dict}]
        self._last_sampled_time: float = -1.0

    def sample(self, time_seconds: float, target: Any) -> None:
        if not self.enabled or not self.keyframes:
            return

        t = float(time_seconds)
        for kf in self.keyframes:
            kf_time = float(kf.get("time", 0.0))
            if self._last_sampled_time < kf_time <= t:
                event_name = kf.get("event_name")
                payload = kf.get("payload", {})
                if event_name:
                    from engine.core.context import EngineContext
                    context = EngineContext.current()
                    if context:
                        from engine.event_bus import EventBus
                        bus = context.services.get_optional(EventBus)
                        if bus:
                            bus.publish_raw(event_name, payload)
        self._last_sampled_time = t

    def evaluate(self, time_seconds: float) -> dict[str, Any]:
        events = [kf for kf in self.keyframes if float(kf.get("time", 0.0)) <= time_seconds]
        return {"events": events}

    def clone(self) -> EventTrack:
        track = EventTrack(name=self.name, enabled=self.enabled)
        track.deserialize(self.serialize())
        return track

    def preview(self, time_seconds: float) -> str:
        events = self.evaluate(time_seconds).get("events", [])
        return f"Event(fired={len(events)})"

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
