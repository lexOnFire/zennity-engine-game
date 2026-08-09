from __future__ import annotations

from editor.runtime.benchmark_gameplay_compat import update_benchmark_gameplay


def test_benchmark_coin_collection_updates_score_and_hides_coin() -> None:
    objects = {
        "Player": {"name": "Player", "x": 0.0, "y": 0.0, "w": 40.0, "h": 40.0, "variables": {}},
        "Coin 1": {"name": "Coin 1", "x": 0.0, "y": 0.0, "w": 20.0, "h": 20.0, "active": True},
        "HUD": {
            "name": "HUD",
            "components": {"items": [{"type": "Canvas", "properties": {"layout_path": "Assets/UI/HUD.zui"}}]},
        },
    }

    update_benchmark_gameplay(objects, 1 / 60)

    assert objects["Coin 1"]["active"] is False
    assert objects["Coin 1"]["destroyed"] is True
    assert objects["Player"]["variables"]["coins"] == 1
    assert objects["Player"]["logic_events"][0]["value"] == {"object": "CoinsLabel", "text": "Coins: 1"}
    overrides = objects["HUD"]["components"]["items"][0]["properties"]["_widget_overrides"]
    assert overrides["CoinsLabel"]["text"] == "Coins: 1"


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


def test_benchmark_player_faces_horizontal_movement_direction() -> None:
    objects = {
        "Player": {
            "name": "Player", "x": 0.0, "y": 0.0, "w": 40.0, "h": 40.0,
            "_input": {"left": True, "right": False}, "variables": {},
        },
    }

    update_benchmark_gameplay(objects, 1 / 60)

    assert objects["Player"]["flip_x"] is True
    assert objects["Player"]["variables"]["facing_x"] == -1


def test_benchmark_enemy_contact_damages_player_and_updates_health_ui() -> None:
    objects = {
        "Player": {
            "name": "Player", "x": 0.0, "y": 0.0, "w": 40.0, "h": 40.0,
            "variables": {"health": 100},
        },
        "Enemy 1": {"name": "Enemy 1", "x": 0.0, "y": 0.0, "w": 32.0, "h": 32.0, "active": True},
        "HUD": {
            "name": "HUD",
            "components": {"items": [{"type": "Canvas", "properties": {"layout_path": "Assets/UI/HUD.zui"}}]},
        },
    }

    update_benchmark_gameplay(objects, 1 / 60)

    assert objects["Player"]["variables"]["health"] == 90
    assert {"command": "set_ui_text", "value": {"object": "HealthLabel", "text": "Health: 90"}} in objects["Player"]["logic_events"]
    assert {
        "command": "set_ui_progress",
        "value": {"object": "HealthBar", "value": 90.0, "max_value": 100.0},
    } in objects["Player"]["logic_events"]
    overrides = objects["HUD"]["components"]["items"][0]["properties"]["_widget_overrides"]
    assert overrides["HealthLabel"]["text"] == "Health: 90"
    assert overrides["HealthBar"] == {"value": 90.0, "max_value": 100.0}


def test_benchmark_game_over_loads_game_over_scene_when_health_reaches_zero() -> None:
    objects = {
        "Player": {
            "name": "Player", "x": 0.0, "y": 0.0, "w": 40.0, "h": 40.0,
            "variables": {"health": 10},
        },
        "Enemy 1": {"name": "Enemy 1", "x": 0.0, "y": 0.0, "w": 32.0, "h": 32.0, "active": True},
        "HUD": {"name": "HUD"},
    }

    update_benchmark_gameplay(objects, 1 / 60)

    assert objects["Player"]["variables"]["health"] == 0
    assert {
        "command": "load_scene",
        "value": {"path": "Assets/Scenes/GameOver.zscene"},
    } in objects["Player"]["logic_events"]
    assert any(
        event["command"] == "set_hud"
        and event["value"]["key"] == "game_over"
        and event["value"]["text"] == "GAME OVER"
        for event in objects["Player"]["logic_events"]
    )


def test_benchmark_guard_dialogue_prompt_and_interaction() -> None:
    objects = {
        "Player": {
            "name": "Player", "x": 0.0, "y": 0.0, "w": 40.0, "h": 40.0,
            "_input": {"interact": True}, "variables": {},
        },
        "Guard": {"name": "Guard", "x": 60.0, "y": 0.0, "w": 40.0, "h": 40.0, "active": True},
        "HUD": {"name": "HUD"},
    }

    update_benchmark_gameplay(objects, 1 / 60)

    events = objects["Player"]["logic_events"]
    assert any(event["value"]["key"] == "dialogue_hint" for event in events if event["command"] == "set_hud")
    assert any(
        event["value"]["key"] == "dialogue" and "gate is locked" in event["value"]["text"]
        for event in events
        if event["command"] == "set_hud"
    )
    assert any(
        event["command"] == "start_dialogue"
        and event["value"]["speaker"] == "Guard"
        and "gate is locked" in event["value"]["text"]
        for event in events
    )
