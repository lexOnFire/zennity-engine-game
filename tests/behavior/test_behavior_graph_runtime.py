from engine.behavior.graph_runtime import BehaviorGraphRunner


class Game:
    def __init__(self, x=0.0, y=0.0, targets=None):
        self.x, self.y = x, y
        self.targets = targets or {}
        self.axes = []
        self.health = 100.0
        self.animations = []
        self.animator = self

    def find(self, name):
        return self.targets.get(name)

    def move(self, dx, dy):
        self.x += dx
        self.y += dy

    def override_physics_axis(self, axis):
        self.axes.append(axis)

    def distance_to(self, other):
        return ((other.x - self.x) ** 2 + (other.y - self.y) ** 2) ** 0.5

    def play(self, name):
        self.animations.append(name)


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


def test_chase_condition_attack_and_cooldown_are_executable():
    target = Game(10, 0)
    game = Game(targets={"Player": target})
    data = graph(
        [
            {"id": "root", "type": "bt.sequence"},
            {"id": "range", "type": "bt.target_in_range", "properties": {"target": "Player", "distance": 20}},
            {"id": "chase", "type": "bt.chase", "properties": {"target": "Player", "speed": 10, "stop_distance": 5}},
            {"id": "cooldown", "type": "bt.cooldown", "properties": {"seconds": 1}},
            {"id": "attack", "type": "bt.attack", "properties": {"target": "Player", "damage": 25, "range": 5}},
        ],
        [
            {"source_node": "root", "source_port": "out_1", "target_node": "range"},
            {"source_node": "root", "source_port": "out_2", "target_node": "chase"},
            {"source_node": "root", "source_port": "out_3", "target_node": "cooldown"},
            {"source_node": "cooldown", "source_port": "child", "target_node": "attack"},
        ],
    )
    runner = BehaviorGraphRunner(data)

    runner.update(game, 0.5)
    assert game.x == 5
    runner.update(game, 0.1)
    assert target.health == 75
    runner.update(game, 0.1)
    assert target.health == 75  # cooldown blocks a second hit
    runner.update(game, 1.0)
    assert target.health == 50


def test_repeat_parameter_patrol_and_animation_nodes():
    animation_graph = graph(
        [
            {"id": "root", "type": "bt.sequence"},
            {"id": "condition", "type": "bt.parameter_condition", "properties": {"parameter": "alert", "operator": "==", "value": "true"}},
            {"id": "animation", "type": "bt.play_animation", "properties": {"animation": "Run"}},
        ],
        [
            {"source_node": "root", "source_port": "out_1", "target_node": "condition"},
            {"source_node": "root", "source_port": "out_2", "target_node": "animation"},
        ],
    )
    game = Game()
    runner = BehaviorGraphRunner(animation_graph)
    runner.set_bool("alert", True)
    runner.update(game, 0.1)
    assert game.animations == ["Run"]

    patrol_graph = graph(
        [
            {"id": "repeat", "type": "bt.repeat", "properties": {"count": 0}},
            {"id": "patrol", "type": "bt.patrol", "properties": {"point_a": "0,0", "point_b": "10,0", "speed": 10}},
        ],
        [{"source_node": "repeat", "source_port": "child", "target_node": "patrol"}],
    )
    patrol = BehaviorGraphRunner(patrol_graph)
    patrol.update(game, 0.5)
    assert game.x == 5
    patrol.update(game, 0.5)
    assert game.x == 10
    patrol.update(game, 0.5)
    assert game.x == 5
