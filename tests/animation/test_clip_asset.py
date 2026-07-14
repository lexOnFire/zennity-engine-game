from __future__ import annotations

import json

from engine.animation.clip_asset import (
    ANIMATION_ASSET_FORMAT,
    animation_asset_from_clip,
    animation_asset_to_clip,
    load_animation_asset,
    normalize_animation_asset,
    save_animation_asset,
)


def test_normalize_legacy_clip_builds_contiguous_frames() -> None:
    asset = normalize_animation_asset({
        "name": "Run",
        "texture": r"Assets\Textures\hero.png",
        "frame_width": 0,
        "frame_height": "48",
        "start_frame": 3,
        "frame_count": 4,
        "fps": 12,
        "loop": False,
    })

    assert asset["format"] == ANIMATION_ASSET_FORMAT
    assert asset["texture"] == "Assets/Textures/hero.png"
    assert asset["frame_width"] == 1
    assert asset["frame_height"] == 48
    assert asset["frames"] == [3, 4, 5, 6]
    assert asset["fps"] == 12.0
    assert asset["loop"] is False


def test_zanim_round_trip_is_human_readable(tmp_path) -> None:
    path = tmp_path / "idle.zanim"
    original = animation_asset_from_clip("Idle", {
        "texture": "Assets/Textures/hero.png",
        "frame_width": 32,
        "frame_height": 48,
        "start_frame": 0,
        "frame_count": 3,
        "fps": 8.0,
        "loop": True,
    })

    saved = save_animation_asset(path, original)

    assert load_animation_asset(path) == saved
    assert json.loads(path.read_text(encoding="utf-8"))["name"] == "Idle"
    assert not (tmp_path / "idle.zanim.tmp").exists()


def test_asset_to_clip_preserves_current_play_mode_contract() -> None:
    clip = animation_asset_to_clip({
        "name": "Attack",
        "texture": "Assets/Textures/hero.png",
        "frame_width": 64,
        "frame_height": 64,
        "frames": [5, 6, 7],
        "fps": 14,
        "loop": False,
    }, "Assets/Animations/Attack.zanim")

    assert clip["start_frame"] == 5
    assert clip["frame_count"] == 3
    assert clip["frames"] == [5, 6, 7]
    assert clip["asset_path"] == "Assets/Animations/Attack.zanim"


def test_animation_events_are_normalized_and_preserved_in_runtime_clip() -> None:
    asset = normalize_animation_asset({
        "name": "Attack", "frames": [0, 1, 2],
        "events": [
            {"frame_index": 2, "event": "hit", "payload": {"damage": 10}},
            {"frame": 0, "name": "start"},
            {"frame": 1, "name": ""},
        ],
    })
    assert [event["name"] for event in asset["events"]] == ["start", "hit"]
    clip = animation_asset_to_clip(asset)
    assert clip["events"][1] == {"frame": 2, "name": "hit", "payload": {"damage": 10}}
