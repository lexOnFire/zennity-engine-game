from __future__ import annotations
"""
engine/animation/clip.py
───────────────────────────

AnimationClip  — sequencia de frames + metadata.
AnimationEvent — callback disparado em um frame específico.
"""

from dataclasses import dataclass, field
from typing import Any, Callable, List, Optional
import pygame


@dataclass
class AnimationEvent:
    """
    Evento disparado quando o clip passa pelo frame `frame_index`.

    Parameters
    ----------
    frame_index : int      – Frame que dispara o evento.
    callback    : Callable – Função chamada sem argumentos.
    fired       : bool     – Controle interno — não editar.
    """
    frame_index: int
    callback: Callable[[], None]
    fired: bool = field(default=False, repr=False)


@dataclass
class Keyframe:
    """Keyframe simples para animar uma propriedade serializável."""

    time: float
    property: str
    value: Any

    def serialize(self) -> dict[str, Any]:
        return {
            "time": float(self.time),
            "property": str(self.property),
            "value": self.value,
        }

    @classmethod
    def deserialize(cls, data: dict[str, Any]) -> "Keyframe":
        return cls(
            time=float(data.get("time", 0.0)),
            property=str(data.get("property", "")),
            value=data.get("value"),
        )


class AnimationClip:
    """
    Uma animação: lista de frames + FPS + configurações de loop.

    Parameters
    ----------
    name    : str                  – Nome único do clip (ex: "run", "idle").
    frames  : List[pygame.Surface] – Sequencia de surfaces.
    fps     : float                – Velocidade da animação em frames/segundo.
    loop    : bool                 – Reinicia ao chegar no último frame.
    flip_h  : bool                 – Espelha todos os frames horizontalmente.
    events  : Optional[List[AnimationEvent]] – Eventos iniciais do clip.
    """

    def __init__(
        self,
        name: str,
        frames: List[pygame.Surface],
        fps: float = 10.0,
        loop: bool = True,
        flip_h: bool = False,
        events: Optional[List[AnimationEvent]] = None,
        keyframes: Optional[List[Keyframe | dict[str, Any]]] = None,
        duration: float | None = None,
        properties: Optional[List[str]] = None,
        frame_source: Optional[dict[str, Any]] = None,
    ) -> None:
        self.name = name
        self.fps = max(fps, 0.01)
        self.loop = loop
        self._duration = float(duration) if duration is not None else None
        self.flip_h = bool(flip_h)
        # BUG FIX (limitação #9): serialize()/deserialize() antigos não
        # persistiam `frames` (as imagens de sprite-cycle), só as keyframes
        # de propriedade sobreviviam a um save/load via .zscene. Guardamos
        # aqui uma descrição serializável de ONDE os frames vieram (qual
        # spritesheet, recorte, flip) para reconstruí-los no deserialize.
        # Ver `frame_source` em serialize()/deserialize() abaixo.
        self.frame_source: Optional[dict[str, Any]] = dict(frame_source) if frame_source else None

        if flip_h:
            self.frames = [pygame.transform.flip(f, True, False) for f in frames]
        else:
            self.frames = list(frames)

        self._events: List[AnimationEvent] = list(events or [])
        self.keyframes: list[Keyframe] = [
            item if isinstance(item, Keyframe) else Keyframe.deserialize(item)
            for item in list(keyframes or [])
        ]
        self.properties: list[str] = list(properties or sorted({kf.property for kf in self.keyframes}))

    # ------------------------------------------------------------------
    # Eventos
    # ------------------------------------------------------------------

    def add_event(self, frame_index: int, callback: Callable[[], None]) -> "AnimationClip":
        """
        Adiciona um callback que será disparado quando a animação
        atingir o frame `frame_index`. Retorna self para encadeamento.
        """
        self._events.append(AnimationEvent(frame_index, callback))
        return self

    @property
    def events(self) -> List[AnimationEvent]:
        return self._events

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @property
    def frame_count(self) -> int:
        return len(self.frames)

    @property
    def duration(self) -> float:
        """Duração total do clip em segundos."""
        if self._duration is not None:
            return self._duration
        if self.keyframes:
            return max((float(kf.time) for kf in self.keyframes), default=0.0)
        return self.frame_count / self.fps

    def sample(self, time_seconds: float) -> dict[str, Any]:
        """Retorna valores interpolados por propriedade para o instante informado."""
        if not self.keyframes:
            return {}
        duration = max(self.duration, 0.0)
        t = float(time_seconds)
        if self.loop and duration > 0.0:
            t = t % duration
        else:
            t = max(0.0, min(t, duration))

        result: dict[str, Any] = {}
        for prop in self.properties:
            frames = sorted((kf for kf in self.keyframes if kf.property == prop), key=lambda item: item.time)
            if not frames:
                continue
            if t <= frames[0].time:
                result[prop] = frames[0].value
                continue
            if t >= frames[-1].time:
                result[prop] = frames[-1].value
                continue
            for left, right in zip(frames, frames[1:]):
                if left.time <= t <= right.time:
                    span = max(float(right.time - left.time), 0.000001)
                    alpha = (t - float(left.time)) / span
                    result[prop] = self._lerp_value(left.value, right.value, alpha)
                    break
        return result

    def serialize(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "name": self.name,
            "duration": float(self.duration),
            "loop": bool(self.loop),
            "fps": float(self.fps),
            "properties": list(self.properties),
            "keyframes": [keyframe.serialize() for keyframe in self.keyframes],
        }
        if self.frame_source is not None:
            # Persiste a referência à spritesheet + recorte de frames usados,
            # para que os frames de sprite-cycle sobrevivam a save/load.
            data["frame_source"] = dict(self.frame_source)
            data["flip_h"] = bool(self.flip_h)
        return data

    @classmethod
    def deserialize(cls, data: dict[str, Any]) -> "AnimationClip":
        frame_source = data.get("frame_source")
        frames: List[pygame.Surface] = []
        if isinstance(frame_source, dict) and frame_source.get("sheet"):
            frames = cls._load_frames_from_source(frame_source)

        return cls(
            name=str(data.get("name", "Clip")),
            frames=frames,
            fps=float(data.get("fps", 10.0)),
            loop=bool(data.get("loop", True)),
            flip_h=bool(data.get("flip_h", False)) if frames else False,
            keyframes=[Keyframe.deserialize(item) for item in data.get("keyframes", []) if isinstance(item, dict)],
            duration=float(data["duration"]) if data.get("duration") is not None else None,
            properties=list(data.get("properties", [])),
            frame_source=dict(frame_source) if isinstance(frame_source, dict) else None,
        )

    @staticmethod
    def _load_frames_from_source(source: dict[str, Any]) -> List[pygame.Surface]:
        """Reconstrói a lista de frames a partir de uma referência de spritesheet.

        `source` tem o formato:
            {
                "sheet": "Assets/.../sheet.png",
                "frame_width": 32, "frame_height": 32,
                "spacing": 0, "margin": 0, "scale": 1.0,
                "color_key": [255, 0, 255] | None,
                "frame_range": [start, end],   # exclusive end, tipo sheet.get_range()
            }
        Se o arquivo não puder ser carregado (asset ausente, pygame sem
        vídeo inicializado, etc.) retorna [] silenciosamente — o clip ainda
        funciona para tweening de propriedades, só perde o ciclo de sprites.
        """
        try:
            from engine.animation.spritesheet import SpriteSheet

            color_key = source.get("color_key")
            sheet = SpriteSheet(
                image_path=str(source["sheet"]),
                frame_width=int(source.get("frame_width", 32)),
                frame_height=int(source.get("frame_height", 32)),
                spacing=int(source.get("spacing", 0)),
                margin=int(source.get("margin", 0)),
                scale=float(source.get("scale", 1.0)),
                color_key=tuple(color_key) if color_key else None,
            ).load()

            frame_range = source.get("frame_range")
            if frame_range and len(frame_range) == 2:
                return sheet.get_range(int(frame_range[0]), int(frame_range[1]))
            frame_indices = source.get("frame_indices")
            if frame_indices:
                return [sheet.get(int(i)) for i in frame_indices]
            return sheet.frames
        except Exception:
            return []

    def _lerp_value(self, a: Any, b: Any, alpha: float) -> Any:
        if isinstance(a, (int, float)) and isinstance(b, (int, float)):
            return float(a) + (float(b) - float(a)) * alpha
        if isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)):
            length = min(len(a), len(b))
            return [float(a[i]) + (float(b[i]) - float(a[i])) * alpha for i in range(length)]
        return b if alpha >= 1.0 else a

    def __repr__(self) -> str:
        return (
            f"<AnimationClip '{self.name}' "
            f"frames={self.frame_count} "
            f"fps={self.fps} loop={self.loop}>"
        )
