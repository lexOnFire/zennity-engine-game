from __future__ import annotations

from pathlib import Path

from engine.behavior.controller_asset import (
    BehaviorControllerRunner,
    BehaviorControllerRuntime,
    load_behavior_controller,
    normalize_behavior_controller,
    save_behavior_controller,
    validate_behavior_controller,
)


def controller_data(script: str = ""):
    return {
        "name": "Enemy",
        "initial_state": "Patrol",
        "parameters": {
            "distance": {"type": "float", "default": 999.0},
            "attack": {"type": "trigger", "default": False},
        },
        "states": {
            "Patrol": {"script": script},
            "Chase": {"script": script},
            "Attack": {"script": script},
        },
        "transitions": [
            {"from": "Patrol", "to": "Chase", "conditions": [{"parameter": "distance", "operator": "<", "value": 300}]},
            {"from": "*", "to": "Attack", "priority": 10, "conditions": [{"parameter": "attack", "operator": "trigger"}]},
        ],
    }


def test_round_trip_uses_zbehavior_extension(tmp_path):
    path = tmp_path / "enemy"
    saved = save_behavior_controller(path, controller_data())
    output = tmp_path / "enemy.zbehavior"
    assert output.is_file()
    assert saved == load_behavior_controller(output)
    assert saved["format"] == "zennity.behavior_controller"


def test_runtime_evaluates_priority_and_consumes_trigger():
    runtime = BehaviorControllerRuntime(controller_data())
    runtime.set_float("distance", 100.0)
    assert runtime.update() and runtime.current_state == "Chase"
    runtime.trigger("attack")
    assert runtime.update() and runtime.current_state == "Attack"
    assert runtime.previous_state == "Chase"
    assert runtime.parameters["attack"] is False


def test_normalization_removes_invalid_states_and_transitions():
    data = controller_data()
    data["initial_state"] = "Missing"
    data["transitions"] = [{"from": "Missing", "to": "Patrol", "conditions": []}]
    normalized = normalize_behavior_controller(data)
    assert normalized["initial_state"] == "Patrol"
    assert normalized["transitions"] == []


def test_validation_reports_missing_script(tmp_path):
    data = controller_data("Assets/Scripts/missing.py")
    issues = validate_behavior_controller(data, tmp_path)
    assert len([issue for issue in issues if issue["level"] == "error"]) == 3


def test_runner_calls_exit_before_enter_on_transition(tmp_path):
    events: list[str] = []
    script = tmp_path / "state.py"
    script.write_text(
        "def on_enter(game): game.events.append('enter')\n"
        "def on_update(game, dt): game.events.append('update')\n"
        "def on_exit(game): game.events.append('exit')\n",
        encoding="utf-8",
    )
    data = controller_data(str(script))
    runner = BehaviorControllerRunner(data, tmp_path)

    class Game:
        pass

    game = Game()
    game.events = events
    game.behavior = runner
    runner.start(game)
    runner.set_float("distance", 100.0)
    assert runner.update(game, 0.016)
    assert runner.current_state == "Chase"
    assert events == ["enter", "update", "exit", "enter"]
    runner.stop(game)
    assert events[-1] == "exit"


def test_repository_demo_is_complete():
    root = Path(__file__).resolve().parents[2]
    controller = load_behavior_controller(root / "Assets/Behaviors/EnemyDemo.zbehavior")
    assert set(controller["states"]) == {"Patrol", "Chase", "Attack"}
    assert not validate_behavior_controller(controller, root)
