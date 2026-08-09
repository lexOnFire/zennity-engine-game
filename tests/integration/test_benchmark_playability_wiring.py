from __future__ import annotations

import json
from pathlib import Path

from editor.runtime.viewport_asset_hydration import hydrate_logic_graphs


PROJECT_ROOT = Path.cwd()


def _scene(name: str) -> dict:
    return json.loads((PROJECT_ROOT / "Assets" / "Scenes" / f"{name}.zscene").read_text(encoding="utf-8"))


def _ui(name: str) -> dict:
    return json.loads((PROJECT_ROOT / "Assets" / "UI" / name).read_text(encoding="utf-8"))


def test_benchmark_player_uses_single_playable_wasd_logic_graph() -> None:
    for scene_name in ("Level1", "Level2"):
        scene = _scene(scene_name)
        objects = {obj["name"]: obj for obj in scene["objects"]}

        hydrate_logic_graphs(objects, PROJECT_ROOT)

        graphs = objects["Player"].get("logic_graphs", [])
        assert [graph["path"] for graph in graphs] == ["Assets/Logic/PlayerMovement_wasd.zlogic"]
        assert graphs[0]["graph"]["enabled"] is True


def test_benchmark_boss_hud_only_appears_in_level2() -> None:
    assert _scene("Level1")["ui"] == "Assets/UI/HUD.zui"
    assert _scene("Level2")["ui"] == "Assets/UI/HUD_Boss.zui"

    level1_widgets = {child["name"] for child in _ui("HUD.zui")["canvas"]["children"]}
    level2_widgets = {child["name"] for child in _ui("HUD_Boss.zui")["canvas"]["children"]}

    assert "BossHealthBar" not in level1_widgets
    assert "BossNameLabel" not in level1_widgets
    assert {"BossHealthBar", "BossNameLabel"} <= level2_widgets


def test_level1_contains_guard_npc_with_dialogue_asset() -> None:
    objects = {obj["name"]: obj for obj in _scene("Level1")["objects"]}
    guard = objects["Guard"]

    assert guard["dialogue_asset"] == "Assets/Dialogues/GuardDialogue.zdialogue"
    assert guard["dialogue"]["asset_path"] == "Assets/Dialogues/GuardDialogue.zdialogue"
    assert guard["tag"] == "NPC"
    assert guard["visual"]["color"] == [0.25, 0.85, 1.0, 1.0]
    assert (PROJECT_ROOT / guard["dialogue_asset"]).is_file()


def test_level1_victory_flag_is_hidden_until_unlocked() -> None:
    objects = {obj["name"]: obj for obj in _scene("Level1")["objects"]}
    level_exit = objects["LevelExit"]
    key = objects["Key"]

    assert level_exit["active"] is False
    assert level_exit["enabled"] is False
    assert level_exit["visual"]["enabled"] is False
    assert level_exit["variables"]["unlock_condition"] == "boss_defeated_or_victory"
    assert key["tag"] == "Key"
    assert key["visual"]["texture"] != "Assets/Sprites/MyPlatformer/flag.png"


def test_game_over_scene_loads_ui_and_buttons_route_to_scenes() -> None:
    scene = _scene("GameOver")
    objects = {obj["name"]: obj for obj in scene["objects"]}
    canvas_item = objects["Canvas"]["components"]["items"][0]
    widgets = {child["name"]: child for child in _ui("GameOver.zui")["canvas"]["children"]}

    assert scene["ui"] == "Assets/UI/GameOver.zui"
    assert canvas_item["type"] == "Canvas"
    assert canvas_item["properties"]["layout_path"] == "Assets/UI/GameOver.zui"
    assert canvas_item["properties"]["ui_asset"] == "Assets/UI/GameOver.zui"
    assert widgets["RetryButton"]["event"] == "load_scene"
    assert widgets["RetryButton"]["scene_path"] == "Assets/Scenes/Level1.zscene"
    assert widgets["MainMenuButton"]["event"] == "load_scene"
    assert widgets["MainMenuButton"]["scene_path"] == "Assets/Scenes/MainMenu.zscene"
