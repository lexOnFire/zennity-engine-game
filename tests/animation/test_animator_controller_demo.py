from __future__ import annotations

import json
from pathlib import Path

from engine.animation.clip_asset import load_animation_asset
from engine.animation.controller_asset import AnimatorControllerRuntime, load_animator_controller
from engine.build.runtime_scene_loader import load_objects


ROOT = Path(__file__).resolve().parents[2]
DEMO_ROOT = ROOT / "Assets" / "Animations" / "AnimatorDemo"
SCENE_PATH = ROOT / "Assets" / "Scenes" / "AnimatorControllerDemo.zscene"


def test_demo_scene_references_complete_reusable_assets() -> None:
    controller = load_animator_controller(DEMO_ROOT / "PlayerDemo.zanimator")
    assert set(controller["states"]) == {"Idle", "Walk", "Jump", "Attack"}
    assert set(controller["parameters"]) == {"speed", "grounded", "attack"}
    for state in controller["states"].values():
        assert (ROOT / state["animation"]).is_file()
    objects = {obj["name"]: obj for obj in load_objects(SCENE_PATH)}
    assert {"MainCamera", "Chao", "Player", "AttackHitbox", "TrainingTarget"} <= set(objects)
    assert objects["Player"]["animator"]["controller_path"].endswith("PlayerDemo.zanimator")
    assert objects["AttackHitbox"]["active"] is False


def test_demo_controller_exercises_walk_jump_attack_and_exit_time() -> None:
    runtime = AnimatorControllerRuntime(load_animator_controller(DEMO_ROOT / "PlayerDemo.zanimator"))
    runtime.set_float("speed", 1.0)
    assert runtime.update() and runtime.current_state == "Walk"
    runtime.set_bool("grounded", False)
    assert runtime.update() and runtime.current_state == "Jump"
    runtime.set_bool("grounded", True)
    assert runtime.update() and runtime.current_state == "Idle"
    runtime.trigger("attack")
    assert runtime.update() and runtime.current_state == "Attack"
    assert not runtime.update(normalized_time=0.5, delta_time=0.4)
    assert runtime.update(normalized_time=1.0, delta_time=0.0)
    assert runtime.current_state == "Idle"


def test_demo_clips_define_audio_and_hitbox_events() -> None:
    walk = load_animation_asset(DEMO_ROOT / "Walk.zanim")
    attack = load_animation_asset(DEMO_ROOT / "Attack.zanim")
    assert [event["name"] for event in walk["events"]] == ["passo", "passo"]
    assert [event["name"] for event in attack["events"]] == ["ataque_inicio", "ataque_fim"]
    assert attack["loop"] is False


def test_demo_scene_uses_animator_assets_without_python_scripts() -> None:
    objects = load_objects(SCENE_PATH)
    assert all("scripts" not in obj for obj in objects)
    assert all("scripts" not in obj.get("components", {}) for obj in objects)
    player = next(obj for obj in objects if obj["name"] == "Player")
    assert player["animator"]["controller_path"].endswith("PlayerDemo.zanimator")
    assert player["animator"]["parameters"] == {"speed": 0.0, "grounded": True, "attack": False}


def test_demo_scene_json_survives_save_reload_shape() -> None:
    payload = json.loads(SCENE_PATH.read_text(encoding="utf-8"))
    assert payload["format_version"] == 2
    encoded = json.dumps(payload, ensure_ascii=False)
    assert json.loads(encoded) == payload
