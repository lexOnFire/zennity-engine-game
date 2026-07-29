import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCENE_PATH = ROOT / "Assets/Scenes/JogoBase2D.zscene"


def test_scene_is_complete_and_uses_graph_authoring() -> None:
    scene = json.loads(SCENE_PATH.read_text(encoding="utf-8"))
    objects = scene["objects"]
    names = {obj["name"] for obj in objects}

    assert {"MainCamera", "Player", "Chao", "Inimigo", "PortalFinal"} <= names
    assert sum(obj["tag"] == "Coin" for obj in objects) == 5
    serialized = json.dumps(scene)
    assert "Assets/Scripts" not in serialized
    assert "script_path" not in serialized
    assert all("scripts" not in obj.get("components", {}) for obj in objects)


def test_play_api_supports_hud_destroy_and_restart() -> None:
    from editor.isolated_viewport import PlayScriptAPI

    obj = {"name": "Player", "active": True}
    game = PlayScriptAPI("Player", obj, None)
    game.set_hud("health", "VIDA: 3", (255, 100, 100), "top-left", 24)
    game.set_ui_text("HUD_Vida", "VIDA: 3")
    game.remove_hud("health")
    game.restart()
    game.destroy()

    assert not game.active
    assert [item["command"] for item in obj["logic_events"]] == [
        "set_hud", "set_ui_text", "remove_hud", "restart_scene",
    ]


def test_base_scene_demonstrates_all_native_ui_components() -> None:
    scene = json.loads(SCENE_PATH.read_text(encoding="utf-8"))
    ui_types = {
        component["type"]
        for obj in scene["objects"]
        for component in obj.get("components", {}).get("items", [])
        if component.get("type") in {"Canvas", "Label", "Image", "Button"}
    }

    assert ui_types == {"Canvas", "Label", "Image", "Button"}
