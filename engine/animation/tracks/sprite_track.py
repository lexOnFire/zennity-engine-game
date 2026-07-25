from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, List
from engine.animation.tracks.base_track import AnimationTrack


class SpriteTrack(AnimationTrack):
    """Trilha especializada para trocar frames ou imagens do SpriteRenderer."""

    def __init__(self, name: str = "SpriteTrack", enabled: bool = True) -> None:
        super().__init__(name, enabled)
        self.keyframes: List[dict] = []  # [{time: float, image_path: str, flip_h: bool}]

    def sample(self, time_seconds: float, target: Any) -> None:
        if not self.enabled or target is None or not self.keyframes:
            return

        from engine.graphics.renderer2d import SpriteRenderer
        sr = target.get_component(SpriteRenderer) if hasattr(target, "get_component") else None
        if sr is None:
            return

        sorted_kfs = sorted(self.keyframes, key=lambda k: k["time"])
        current_kf = sorted_kfs[0]
        for kf in sorted_kfs:
            if kf["time"] <= time_seconds:
                current_kf = kf
            else:
                break

        image_path = current_kf.get("image_path")
        if image_path:
            from engine.assets import Assets
            sr.image = Assets.get_image(image_path)
            if current_kf.get("flip_h"):
                import pygame
                sr.image = pygame.transform.flip(sr.image, True, False)

    def evaluate(self, time_seconds: float) -> dict[str, Any]:
        if not self.keyframes:
            return {}
        sorted_kfs = sorted(self.keyframes, key=lambda k: k["time"])
        current_kf = sorted_kfs[0]
        for kf in sorted_kfs:
            if kf["time"] <= time_seconds:
                current_kf = kf
            else:
                break
        return dict(current_kf)

    def clone(self) -> SpriteTrack:
        track = SpriteTrack(name=self.name, enabled=self.enabled)
        track.deserialize(self.serialize())
        return track

    def preview(self, time_seconds: float) -> str:
        eval_data = self.evaluate(time_seconds)
        path = eval_data.get("image_path", "None")
        return f"Sprite({Path(path).name if path else 'None'})"

    def duration(self) -> float:
        return max((float(kf.get("time", 0.0)) for kf in self.keyframes), default=0.0)

    def serialize(self) -> Dict[str, Any]:
        data = super().serialize()
        data["keyframes"] = self.keyframes
        return data

    def deserialize(self, data: Dict[str, Any]) -> None:
        super().deserialize(data)
        self.keyframes = list(data.get("keyframes", []))
