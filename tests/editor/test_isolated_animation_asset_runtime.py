from __future__ import annotations

from editor.isolated_viewport import hydrate_animation_asset_clips
from engine.animation.clip_asset import save_animation_asset


def test_play_mode_refreshes_applied_clip_from_zanim(tmp_path) -> None:
    animations = tmp_path / "Assets" / "Animations"
    asset_path = animations / "andar.zanim"
    save_animation_asset(asset_path, {
        "name": "andar",
        "texture": "Assets/Textures/player.png",
        "frame_width": 32,
        "frame_height": 48,
        "frames": [2, 4, 6],
        "fps": 10,
        "loop": True,
    })
    objects = {
        "Player": {
            "animator": {
                "active_clip": "andar",
                "clips": {
                    "andar": {
                        "asset_path": "Assets/Animations/andar.zanim",
                        "texture": "old.png",
                        "frame_count": 1,
                    }
                },
            }
        }
    }

    messages = hydrate_animation_asset_clips(objects, tmp_path)

    clip = objects["Player"]["animator"]["clips"]["andar"]
    assert clip["texture"] == "Assets/Textures/player.png"
    assert clip["frames"] == [2, 4, 6]
    assert clip["frame_count"] == 3
    assert messages == [("INFO", "Player", "animação atualizada: andar.zanim")]


def test_play_mode_reports_missing_zanim_without_removing_cached_clip(tmp_path) -> None:
    cached = {
        "asset_path": "Assets/Animations/andar.zanim",
        "texture": "cached.png",
        "frame_count": 2,
    }
    objects = {"Player": {"animator": {"clips": {"andar": dict(cached)}}}}

    messages = hydrate_animation_asset_clips(objects, tmp_path)

    assert objects["Player"]["animator"]["clips"]["andar"] == cached
    assert messages[0][0:2] == ("ERROR", "Player")
    assert "andar.zanim" in messages[0][2]
