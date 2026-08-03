from pathlib import Path

from engine.logic.blackboard import BlackboardStore
from engine.logic.graph_asset import load_logic_graph, validate_logic_graph
from engine.logic.runtime import LogicGraphRuntime


ROOT = Path(__file__).resolve().parents[2]
GRAPH = ROOT / "Assets/Logic/Showcase_Player.zlogic"


def test_showcase_player_uses_supported_math_and_moves() -> None:
    graph = load_logic_graph(GRAPH)
    assert not validate_logic_graph(graph)

    class Game:
        name = "Player"
        x = 0.0
        y = 0.0
        rotation = 0.0

        @staticmethod
        def axis(_negative: str, _positive: str) -> int:
            return 1

        @staticmethod
        def key_pressed(_name: str) -> bool:
            return False

        def move(self, dx: float, dy: float = 0.0) -> None:
            self.x += dx
            self.y += dy

    game = Game()
    runtime = LogicGraphRuntime(graph, BlackboardStore(), game.name)
    runtime.start(game)
    runtime.update(game, 1.0)

    assert game.x == 300.0
    assert game.y == 0.0
