from __future__ import annotations

from editor.isolated_viewport import PlayLogicAPI, hydrate_behavior_controllers
from editor.runtime.viewport_runtime_initializer import ViewportRuntimeInitializer
from engine.behavior.controller_asset import BehaviorControllerRunner, save_behavior_controller


def _controller(script: str = "") -> dict:
    return {
        "name": "TestBehavior",
        "initial_state": "Idle",
        "parameters": {"move": {"type": "bool", "default": False}},
        "states": {
            "Idle": {"script": script},
            "Move": {"script": script},
        },
        "transitions": [
            {"from": "Idle", "to": "Move", "conditions": [{"parameter": "move", "operator": "==", "value": True}]}
        ],
    }


def test_play_mode_hydrates_zbehavior_asset(tmp_path) -> None:
    path = tmp_path / "Assets" / "Behaviors" / "player.zbehavior"
    save_behavior_controller(path, _controller())
    objects = {
        "Player": {
            "behavior": {
                "controller_path": "Assets/Behaviors/player.zbehavior",
                "parameters": {},
            }
        }
    }

    messages = hydrate_behavior_controllers(objects, tmp_path)

    behavior = objects["Player"]["behavior"]
    assert behavior["controller"]["initial_state"] == "Idle"
    assert set(behavior["controller"]["states"]) == {"Idle", "Move"}
    assert messages == [("INFO", "Player", "behavior carregado: player.zbehavior (2 estado(s))")]


def test_game_behavior_api_changes_parameters_and_state(tmp_path) -> None:
    script = tmp_path / "state.py"
    script.write_text(
        "def on_enter(game): game.state['entered'] = game.behavior.state\n"
        "def on_update(game, dt): pass\n"
        "def on_exit(game): game.state['exited'] = game.behavior.state\n",
        encoding="utf-8",
    )
    obj: dict = {}
    api = PlayLogicAPI("Player", obj, None, {"Player": obj})
    runner = BehaviorControllerRunner(_controller(str(script)), tmp_path)
    api.behavior.bind(runner, api)
    runner.start(api)

    assert api.behavior.state == "Idle"
    api.behavior.set_bool("move", True)
    assert runner.update(api, 0.016)
    assert api.behavior.state == "Move"
    assert api.behavior.parameters["move"] is True
    assert obj["_logic_state"]["entered"] == "Move"


def test_repository_behavior_demo_scene_references_controller() -> None:
    from pathlib import Path
    import json

    root = Path(__file__).resolve().parents[2]
    scene = json.loads((root / "Assets/Scenes/BehaviorControllerDemo.zscene").read_text(encoding="utf-8"))
    enemy = next(item for item in scene["objects"] if item["name"] == "BehaviorEnemy")
    assert enemy["editor_data"]["behavior"]["controller_path"] == "Assets/Behaviors/EnemyDemo.zbehavior"
    assert "scripts" not in enemy.get("components", {})


def test_runtime_initializer_stops_registered_behavior_runners() -> None:
    stopped = []
    runner = type("Runner", (), {"stop": lambda self, api: stopped.append(api)})()
    api = object()
    initializer = ViewportRuntimeInitializer.__new__(ViewportRuntimeInitializer)
    initializer.behavior_runners = {"Enemy": runner}
    initializer.logic_apis = {"Enemy": api}
    initializer.logic_runtimes = {}
    initializer.logic_modules = {}
    initializer.animator_controllers = {}
    initializer.initialized_ids = set()
    initializer.animator_event_signatures = {}
    initializer.emit = lambda _event: None

    initializer._clear_runtime_state()

    assert stopped == [api]
    assert initializer.behavior_runners == {}


def test_linked_behavior_without_auto_start_waits_for_logic_node() -> None:
    initializer = ViewportRuntimeInitializer.__new__(ViewportRuntimeInitializer)
    initializer.api_factory = lambda *_args: (_ for _ in ()).throw(AssertionError("não deve iniciar"))
    initializer.logic_apis = {}
    initializer.behavior_runners = {}

    initializer._initialize_behavior(
        "Enemy",
        {"behavior": {"controller_path": "Assets/Behaviors/Enemy.zbehavior", "auto_start": False}},
    )

    assert initializer.logic_apis == {}
    assert initializer.behavior_runners == {}
