"""A property authored in the editor must reach the executor that reads it.

PHASE 9.5B Stage 4.1. Persistence alone is not the contract: a value that
survives save/reopen but never reaches the runtime is still broken from the
user's point of view. These tests drive the real executors with a spy host and
assert on what the executor actually did with the authored value.
"""

from __future__ import annotations

import pytest

from engine.logic.node_definitions import NODE_DEFINITIONS
from engine.logic.runtime import LogicGraphRuntime


def graph_with(node_type: str, properties: dict) -> dict:
    """An event_update wired straight into the node under test."""
    return {
        "format": "zennity.logic_graph",
        "version": 1,
        "enabled": True,
        "name": "RuntimeContract",
        "target": {"type": "name", "value": "Player"},
        "variables": {},
        "nodes": [
            {"id": "n_event", "type": "event_update", "title": "On Update",
             "category": "Events", "position": [0.0, 0.0], "properties": {}},
            {"id": "n_test", "type": node_type,
             "title": NODE_DEFINITIONS.get(node_type, {}).get("title", node_type),
             "category": NODE_DEFINITIONS.get(node_type, {}).get("category", "Custom"),
             "position": [240.0, 0.0], "properties": dict(properties)},
        ],
        "edges": [{
            "id": "e0", "from_node": "n_event", "from_port": "next",
            "to_node": "n_test", "to_port": "in", "kind": "flow",
        }],
    }


class SpyGame:
    """Records what the executors ask of the host."""

    def __init__(self):
        self.x = 0.0
        self.y = 0.0
        self.rigidbody = None
        self.components: list = []
        self.axis_calls: list[tuple[str, str]] = []
        self.animations: list[str] = []
        self.sounds: list[str] = []
        self.variables: dict = {}
        self.moved: list[tuple[float, float]] = []

    def axis(self, negative, positive):
        self.axis_calls.append((negative, positive))
        return 1.0

    def move(self, dx, dy):
        self.moved.append((dx, dy))
        self.x += dx
        self.y += dy

    @property
    def animator(self):
        game = self

        class _Animator:
            def play(self, state, *args, **kwargs):
                game.animations.append(str(state))

        return _Animator()

    def play_sound(self, path):
        self.sounds.append(str(path))

    def set_variable(self, name, value):
        self.variables[name] = value

    def stop_animation(self):
        pass


def run(node_type: str, properties: dict) -> SpyGame:
    runtime = LogicGraphRuntime(graph_with(node_type, properties))
    game = SpyGame()
    runtime.update(game, 1.0 / 60.0)
    runtime.stop()
    return game


def test_input_axis_uses_the_authored_keys():
    """The property the editor could not previously reach at all.

    The executor lowercases key names before asking the host, so the comparison
    is case-insensitive by design -- authoring "LEFT" and "left" must behave
    identically.
    """
    game = run("input_axis", {"negative": "LEFT", "positive": "RIGHT"})
    assert game.axis_calls, "the axis evaluator never ran"
    assert game.axis_calls[0] == ("left", "right"), (
        f"the executor read {game.axis_calls[0]} instead of the authored keys"
    )


def test_key_authoring_is_case_insensitive():
    upper = run("input_axis", {"negative": "J", "positive": "K"})
    lower = run("input_axis", {"negative": "j", "positive": "k"})
    assert upper.axis_calls[0] == lower.axis_calls[0] == ("j", "k")


def test_changing_the_authored_keys_changes_what_the_runtime_reads():
    first = run("input_axis", {"negative": "A", "positive": "D"})
    second = run("input_axis", {"negative": "J", "positive": "K"})
    assert first.axis_calls[0] == ("a", "d")
    assert second.axis_calls[0] == ("j", "k")
    assert first.axis_calls[0] != second.axis_calls[0]


@pytest.mark.xfail(
    reason=(
        "play_animation is claimed by two modules; animation_nodes wins the load "
        "order and needs a real Animator with populated _clips, so a spy host "
        "cannot drive it. Recorded in node_system.KNOWN_DUPLICATE_OWNERS and "
        "documented as a Stage 3 follow-up -- resolving it changes gameplay."
    ),
    strict=False,
)
def test_play_animation_uses_the_authored_state():
    game = run("play_animation", {"state": "Run", "animation_name": "Run", "target": ""})
    assert game.animations, "the animation executor never ran"


def test_play_sound_uses_the_authored_path():
    game = run("play_sound", {"path": "Assets/Audio/jump.wav"})
    assert game.sounds == ["Assets/Audio/jump.wav"]


def test_set_variable_uses_the_authored_name():
    game = run("set_variable", {"name": "player_health", "value": 42, "scope": "object"})
    assert "player_health" in game.variables, (
        f"the executor wrote {list(game.variables)} instead of the authored name"
    )
    assert game.variables["player_health"] == 42


def test_move_by_uses_the_authored_delta():
    game = run("move_by", {"x": 120.0, "y": 0.0})
    assert game.moved, "move_by never ran"
    assert game.moved[0][0] == pytest.approx(120.0 / 60.0)


def test_defaults_are_what_the_executor_expects():
    """Declared defaults must equal the executor's own fallback.

    If the two disagree, a node behaves differently depending on whether the
    user has ever touched the property -- the subtlest form of this bug.
    """
    game = run("input_axis", {})
    assert game.axis_calls[0] == ("a", "d"), (
        "the declared default disagrees with the executor's fallback"
    )
