from engine.behavior.graph_runtime import BehaviorGraphRunner


class Game:
    def __init__(self, x=0.0, y=0.0, targets=None):
        self.x, self.y = x, y
        self.targets = targets or {}
        self.axes = []

    def find(self, name):
        return self.targets.get(name)

    def move(self, dx, dy):
        self.x += dx
        self.y += dy

    def override_physics_axis(self, axis):
        self.axes.append(axis)


def graph(nodes, edges):
    return {
        "format": "zennity.generic_graph",
        "category": "Behavior Tree",
        "nodes": nodes,
        "edges": edges,
    }


def test_visual_behavior_sequence_waits_then_moves_to_scene_object():
    data = graph(
        [
            {"id": "root", "type": "bt.sequence"},
            {"id": "wait", "type": "bt.wait", "inputs": {"duration": 0.1}},
            {
                "id": "move", "type": "bt.move_to",
                "inputs": {"target_pos": "Target", "speed": 10},
            },
        ],
        [
            {"source_node": "root", "source_port": "out_1", "target_node": "wait"},
            {"source_node": "root", "source_port": "out_2", "target_node": "move"},
        ],
    )
    target = Game(10, 0)
    game = Game(targets={"Target": target})
    runner = BehaviorGraphRunner(data)

    runner.start(game)
    runner.update(game, 0.05)
    assert game.x == 0
    runner.update(game, 0.05)
    assert game.x == 0.5
    runner.update(game, 0.5)

    assert game.x == 5.5
    assert runner.current_state == "move"
    assert game.axes == ["x", "y", "x", "y"]


def test_visual_behavior_rejects_other_graph_categories():
    try:
        BehaviorGraphRunner(graph([], []) | {"category": "Dialogue"})
    except ValueError as exc:
        assert "Behavior Tree" in str(exc)
    else:
        raise AssertionError("categoria inválida deveria ser rejeitada")
