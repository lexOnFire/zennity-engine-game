from __future__ import annotations

from pathlib import Path

from editor.scene_persistence import EditorScenePersistence
from engine.logic.blackboard import BlackboardStore
from engine.logic.graph_asset import load_logic_graph, validate_logic_graph
from engine.logic.runtime import LogicGraphRuntime


ROOT = Path(__file__).resolve().parents[2]
SCENE = ROOT / "Assets/Scenes/NebulaDefensePro.zscene"
LOGIC = ROOT / "Assets/Logic/NebulaDefensePro"


def test_pro_demo_graphs_are_connected_and_valid() -> None:
    paths = sorted(LOGIC.glob("*.zlogic"))
    assert len(paths) == 5
    for path in paths:
        graph = load_logic_graph(path)
        assert graph["edges"], path.name
        assert not validate_logic_graph(graph), path.name


def test_pro_scene_hydrates_logic_and_native_hud() -> None:
    _document, snapshots, typed = EditorScenePersistence(ROOT).load(SCENE)
    objects = {item["name"]: item for item in snapshots}

    assert typed is True
    assert objects["PlayerShip"]["logic_assets"] == [
        "Assets/Logic/NebulaDefensePro/NebulaPlayerPro.zlogic"
    ]
    assert objects["HUD_Canvas"]["ui"]["type"] == "canvas"
    assert objects["ScoreText"]["ui"]["type"] == "text"
    assert objects["ShieldBar"]["ui"]["type"] == "progress_bar"
    assert objects["HealthBar"]["ui"]["value"] == 100.0
    assert objects["WaveText"]["ui"]["anchor"] == "top_right"
    assert objects["ShieldBar"]["ui"]["anchor"] == "bottom_left"
    assert objects["HealthBar"]["ui"]["margin_y"] == 60.0
    assert objects["PlayerShip"]["collider"]["is_trigger"] is False


def test_pro_player_moves_when_w_is_held() -> None:
    graph = load_logic_graph(LOGIC / "NebulaPlayerPro.zlogic")

    class Game:
        name = "PlayerShip"
        tag = "Player"
        x = 0.0
        y = 0.0
        rotation = 0.0

        @staticmethod
        def key(name: str) -> bool:
            return name == "w"

        @staticmethod
        def key_pressed(_name: str) -> bool:
            return False

        def move(self, x: float, y: float) -> None:
            self.x += x
            self.y += y

    game = Game()
    runtime = LogicGraphRuntime(graph, BlackboardStore(), game.name)
    runtime.start(game)
    runtime.update(game, 0.5)

    assert game.x == 0.0
    assert game.y == -170.0


def test_pro_game_manager_queues_audio_on_start() -> None:
    graph = load_logic_graph(LOGIC / "NebulaGameManagerPro.zlogic")

    class Game:
        name = "GameManagerPro"

        def __init__(self) -> None:
            self.sounds: list[str] = []

        def play_sound(self, path: str) -> None:
            self.sounds.append(path)

    game = Game()
    LogicGraphRuntime(graph, BlackboardStore(), game.name).start(game)

    assert game.sounds == ["Assets/Audio/jump-sound-531048.mp3"]
