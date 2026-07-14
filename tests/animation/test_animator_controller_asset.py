from engine.animation.controller_asset import (
    AnimatorControllerRuntime,
    default_animator_controller,
    load_animator_controller,
    normalize_animator_controller,
    save_animator_controller,
    validate_animator_controller,
)


def controller_data():
    return {
        "name": "Player",
        "initial_state": "Idle",
        "parameters": {
            "speed": {"type": "float", "default": 0.0},
            "jump": {"type": "trigger", "default": False},
        },
        "states": {
            "Idle": {"animation": "Assets/Animations/idle.zanim"},
            "Walk": {"animation": "Assets/Animations/walk.zanim"},
            "Jump": {"animation": "Assets/Animations/jump.zanim"},
        },
        "transitions": [
            {"from": "Idle", "to": "Walk", "conditions": [{"parameter": "speed", "operator": ">", "value": 0.1}]},
            {"from": "*", "to": "Jump", "conditions": [{"parameter": "jump", "operator": "trigger", "value": True}]},
        ],
    }


def test_controller_round_trip(tmp_path):
    path = tmp_path / "player.zanimator"
    saved = save_animator_controller(path, controller_data())
    assert saved == load_animator_controller(path)
    assert saved["format"] == "zennity.animator_controller"


def test_runtime_changes_state_and_consumes_trigger():
    runtime = AnimatorControllerRuntime(controller_data())
    assert runtime.current_state == "Idle"
    runtime.set_float("speed", 1.0)
    assert runtime.update() is True
    assert runtime.current_state == "Walk"
    runtime.trigger("jump")
    assert runtime.update() is True
    assert runtime.current_state == "Jump"
    assert runtime.parameters["jump"] is False


def test_normalization_removes_invalid_references():
    data = default_animator_controller()
    data["initial_state"] = "Missing"
    data["transitions"] = [{"from": "Missing", "to": "Idle", "conditions": []}]
    normalized = normalize_animator_controller(data)
    assert normalized["initial_state"] == "Idle"
    assert normalized["transitions"] == []


def test_validation_reports_empty_and_missing_animations(tmp_path):
    data = controller_data()
    data["states"]["Idle"]["animation"] = ""
    issues = validate_animator_controller(data, tmp_path)
    assert any(issue["state"] == "Idle" and issue["level"] == "warning" for issue in issues)
    assert any(issue["state"] == "Walk" and issue["level"] == "error" for issue in issues)
