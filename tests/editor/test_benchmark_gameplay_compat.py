from __future__ import annotations

from editor.runtime.benchmark_gameplay_compat import update_benchmark_gameplay


def test_benchmark_coin_collection_updates_score_and_hides_coin() -> None:
    objects = {
        "Player": {"name": "Player", "x": 0.0, "y": 0.0, "w": 40.0, "h": 40.0, "variables": {}},
        "Coin 1": {"name": "Coin 1", "x": 0.0, "y": 0.0, "w": 20.0, "h": 20.0, "active": True},
        "HUD": {"name": "HUD"},
    }

    update_benchmark_gameplay(objects, 1 / 60)

    assert objects["Coin 1"]["active"] is False
    assert objects["Coin 1"]["destroyed"] is True
    assert objects["Player"]["variables"]["coins"] == 1
    assert objects["HUD"]["logic_events"][0]["value"] == {"object": "CoinsLabel", "text": "Coins: 1"}


def test_benchmark_enemy_moves_towards_player() -> None:
    objects = {
        "Player": {"name": "Player", "x": 100.0, "y": 0.0, "w": 40.0, "h": 40.0},
        "Enemy 1": {
            "name": "Enemy 1", "x": 0.0, "y": 0.0, "w": 32.0, "h": 32.0,
            "active": True, "variables": {"move_speed": 60, "detection_range": 500, "attack_range": 10},
        },
    }

    update_benchmark_gameplay(objects, 1.0)

    assert objects["Enemy 1"]["x"] == 60.0
    assert objects["Enemy 1"]["y"] == 0.0
    assert objects["Enemy 1"]["_logic_motion_axes"] == {"x", "y"}
