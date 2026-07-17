import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCENE_PATH = ROOT / "Assets/Scenes/JogoBase2D.zscene"


def _load_script(name: str):
    path = ROOT / f"Assets/Scripts/base_game_2d/{name}.py"
    spec = importlib.util.spec_from_file_location(f"base_game_{name}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FakeGame:
    def __init__(self, tag="Player"):
        self.tag = tag
        self.x = 120.0
        self.y = 590.0
        self.rotation = 0.0
        self.active = True
        self.state = {}
        self.logs = []
        self.instructions = []
        self.hud = {}
        self.ui_text = {}

    def log(self, message):
        self.logs.append(message)

    def axis(self, negative, positive):
        return 0

    def move(self, dx, dy=0.0):
        self.x += dx
        self.y += dy

    def key_pressed(self, key):
        return False

    def jump(self, force):
        self.state["jump_force"] = force

    def send(self, command, value=None):
        self.instructions.append({"command": command, "value": value})

    def set_hud(self, key, text, color=(255, 255, 255), position="top-left", font_size=22):
        self.hud[key] = {
            "text": text, "color": color, "position": position, "font_size": font_size,
        }

    def set_ui_text(self, object_name, text):
        self.ui_text[object_name] = text

    def restart(self):
        self.state["restart_requested"] = True


def test_scene_is_complete_and_references_existing_scripts() -> None:
    scene = json.loads(SCENE_PATH.read_text(encoding="utf-8"))
    objects = scene["objects"]
    names = {obj["name"] for obj in objects}

    assert {"MainCamera", "Player", "Chao", "Inimigo", "PortalFinal"} <= names
    assert sum(obj["tag"] == "Coin" for obj in objects) == 5
    for obj in objects:
        for script in obj.get("components", {}).get("scripts", []):
            assert (ROOT / script).is_file(), script


def test_player_coin_damage_and_victory_flow() -> None:
    player_script = _load_script("player")
    player = FakeGame()
    player_script.on_start(player)

    for _ in range(5):
        player_script.on_instruction(player, {"command": "add_coin", "value": 1})
    player_script.on_instruction(player, {"command": "damage", "value": 1})
    player_script.on_instruction(player, {"command": "finish", "value": None})

    assert player.state == {"health": 2, "coins": 5, "status": "victory"}
    assert any("VOCÊ VENCEU" in message for message in player.logs)
    assert {"HUD_Vida", "HUD_Moedas", "HUD_Resultado"} <= set(player.ui_text)


def test_coin_deactivates_and_notifies_player() -> None:
    coin_script = _load_script("coin")
    coin = FakeGame(tag="Coin")
    player = FakeGame()

    coin_script.on_trigger(coin, player)

    assert not coin.active
    assert player.instructions == [{"command": "add_coin", "value": 1}]


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
    assert [item["command"] for item in obj["script_instructions"]] == [
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
