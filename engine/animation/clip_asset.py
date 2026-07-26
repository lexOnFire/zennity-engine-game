"""Formato persistente e reutilizável para clips 2D do Zennity Editor."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any, Mapping


ANIMATION_ASSET_FORMAT = "zennity.animation_clip"
ANIMATION_ASSET_VERSION = 1


def default_animation_asset(name: str = "NewAnimation") -> dict[str, Any]:
    """Cria um asset pronto para edição, sem depender de Pygame ou Qt."""
    return {
        "format": ANIMATION_ASSET_FORMAT,
        "version": ANIMATION_ASSET_VERSION,
        "name": str(name).strip() or "NewAnimation",
        "texture": "",
        "frame_width": 32,
        "frame_height": 32,
        "frames": [0],
        "fps": 8.0,
        "loop": True,
        "events": [],
        "tracks": [],
    }


def normalize_animation_asset(data: Mapping[str, Any] | None) -> dict[str, Any]:
    """Valida dados externos e retorna o schema canônico da versão atual."""
    source = dict(data or {})
    result = default_animation_asset(str(source.get("name", "NewAnimation")))

    result["texture"] = str(source.get("texture", "")).replace("\\", "/")
    result["frame_width"] = max(1, _safe_int(source.get("frame_width"), 32))
    result["frame_height"] = max(1, _safe_int(source.get("frame_height"), 32))
    result["fps"] = max(0.1, _safe_float(source.get("fps"), 8.0))
    result["loop"] = bool(source.get("loop", True))

    frames = source.get("frames")
    if isinstance(frames, (list, tuple)):
        normalized_frames = [max(0, _safe_int(frame, 0)) for frame in frames]
    else:
        start = max(0, _safe_int(source.get("start_frame"), 0))
        count = max(1, _safe_int(source.get("frame_count"), 1))
        normalized_frames = list(range(start, start + count))
    result["frames"] = normalized_frames or [0]

    events = source.get("events", [])
    normalized_events = []
    for event in events if isinstance(events, list) else []:
        if not isinstance(event, dict):
            continue
        name = str(event.get("name", event.get("event", ""))).strip()
        if not name:
            continue
        normalized_events.append({
            "frame": min(len(result["frames"]) - 1, max(0, _safe_int(event.get("frame", event.get("frame_index", 0)), 0))),
            "name": name,
            "payload": deepcopy(event.get("payload")),
        })
    result["events"] = sorted(normalized_events, key=lambda item: (item["frame"], item["name"]))
    tracks = source.get("tracks", [])
    result["tracks"] = [
        deepcopy(track) for track in tracks
        if isinstance(track, dict) and str(track.get("type", "")).strip()
    ] if isinstance(tracks, list) else []
    return result


def animation_asset_from_clip(name: str, clip: Mapping[str, Any]) -> dict[str, Any]:
    """Converte o formato embutido legado do Inspector para ``.zanim``."""
    data = dict(clip)
    data["name"] = name
    return normalize_animation_asset(data)


def animation_asset_to_clip(asset: Mapping[str, Any], asset_path: str = "") -> dict[str, Any]:
    """Cria o cache legado esperado pelo Play Mode atual."""
    normalized = normalize_animation_asset(asset)
    frames = list(normalized["frames"])
    clip = {
        "texture": normalized["texture"],
        "frame_width": normalized["frame_width"],
        "frame_height": normalized["frame_height"],
        "start_frame": frames[0],
        "frame_count": len(frames),
        "frames": frames,
        "fps": normalized["fps"],
        "loop": normalized["loop"],
        "events": deepcopy(normalized["events"]),
        "tracks": deepcopy(normalized["tracks"]),
    }
    if asset_path:
        clip["asset_path"] = str(asset_path).replace("\\", "/")
    return clip


def load_animation_asset(path: str | Path) -> dict[str, Any]:
    asset_path = Path(path)
    with asset_path.open("r", encoding="utf-8") as stream:
        raw = json.load(stream)
    if not isinstance(raw, dict):
        raise ValueError("O arquivo de animação deve conter um objeto JSON.")
    if raw.get("format", ANIMATION_ASSET_FORMAT) != ANIMATION_ASSET_FORMAT:
        raise ValueError("Formato de animação não reconhecido.")
    return normalize_animation_asset(raw)


def save_animation_asset(path: str | Path, data: Mapping[str, Any]) -> dict[str, Any]:
    """Salva de forma atômica para não deixar assets incompletos."""
    asset_path = Path(path)
    if asset_path.suffix.lower() != ".zanim":
        asset_path = asset_path.with_suffix(".zanim")
    asset_path.parent.mkdir(parents=True, exist_ok=True)
    normalized = normalize_animation_asset(data)
    temporary_path = asset_path.with_suffix(asset_path.suffix + ".tmp")
    with temporary_path.open("w", encoding="utf-8", newline="\n") as stream:
        json.dump(normalized, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    temporary_path.replace(asset_path)
    return normalized


def _safe_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _safe_float(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default
