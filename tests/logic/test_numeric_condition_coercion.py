"""A number is a condition by its value, not by how it prints.

PHASE 9 recovery item 15. ``LogicGraphRuntime._condition`` had no numeric branch:
a number fell through to a string path built for literals, tokens and variable
names. ``1`` and ``0`` came out right by coincidence -- ``str(1)`` happens to be
one of the recognized literals -- while ``2``, ``-1`` and *every* float reached
the final variable lookup and answered False.

That is why ``PlayerMovementLogic.zlogic`` never moved the player. ``input_axis``
returns ``float(game.axis(...))``, so ``if_else`` received ``1.0``, read it as
the variable named "1.0", found nothing and took the false branch -- in both
directions. An analog stick, which is the whole reason the axis is a float,
could never have worked.

Scope is deliberately narrow. ``_condition`` is reached by exactly two callers,
both ``if_else``; across every shipping asset exactly one edge feeds a condition
with a number. Strings are untouched: the fix dispatches on *type*, before
anything is turned into text, so a variable spelled like a number keeps its
meaning.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from engine.logic.graph_asset import load_logic_graph, normalize_logic_graph
from engine.logic.runtime import LogicGraphRuntime

REPO_ROOT = Path(__file__).resolve().parents[2]
PLAYER_GRAPH = REPO_ROOT / "Assets" / "Logic" / "PlayerMovementLogic.zlogic"


def _runtime(variables: dict | None = None) -> LogicGraphRuntime:
    runtime = LogicGraphRuntime(
        {"format": "zennity.logic_graph", "version": 1, "name": "probe",
         "nodes": [], "edges": [], "variables": {}}
    )
    runtime.variables.update(variables or {})
    return runtime


# ---------------------------------------------------------------------------
# The helper itself
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("value,expected", [
    (True, True),
    (False, False),
])
def test_bool_is_decided_before_anything_else(value, expected):
    """``bool`` is an ``int`` subclass, so its branch has to come first."""
    assert _runtime()._condition(value) is expected


@pytest.mark.parametrize("value", [1, 2, -1, 7, 1.0, -1.0, 0.5, -0.5, 0.25, 1e-9])
def test_a_non_zero_number_is_true(value):
    assert _runtime()._condition(value) is True


@pytest.mark.parametrize("value", [0, 0.0, -0.0])
def test_zero_is_false(value):
    assert _runtime()._condition(value) is False


def test_the_numbers_that_used_to_be_wrong():
    """The regression this item exists for, named one by one.

    ``1`` and ``0`` were already right, by accident. Everything else here
    answered False before, including every float and every int outside {0, 1}.
    """
    runtime = _runtime()
    for value in (2, -1, 1.0, -1.0, 0.5, -0.5):
        assert runtime._condition(value) is True, value
    for value in (1, 0):
        assert runtime._condition(value) is (value == 1)


# ---------------------------------------------------------------------------
# Strings: unchanged, and that is the point
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("text,expected", [
    ("true", True),
    ("verdadeiro", True),
    ("1", True),
    ("false", False),
    ("falso", False),
    ("0", False),
    ("", False),
])
def test_string_literals_keep_their_meaning(text, expected):
    assert _runtime()._condition(text) is expected


def test_a_string_that_looks_like_a_number_is_still_a_variable_name():
    """The distinction the fix depends on: type, not spelling.

    Intercepting ``"1.0"`` as a number would silently change what a variable
    named ``"1.0"`` means. No shipping asset has such a variable today, but the
    rule is what keeps that true by design rather than by luck.
    """
    runtime = _runtime({"1.0": True})
    assert runtime._condition("1.0") is True

    runtime = _runtime({"1.0": False})
    assert runtime._condition("1.0") is False

    # And with no such variable it stays false -- not "truthy because non-zero".
    assert _runtime()._condition("1.0") is False
    assert _runtime()._condition("-1") is False


def test_variable_names_still_resolve():
    runtime = _runtime({"door_open": True, "door_shut": False})
    assert runtime._condition("door_open") is True
    assert runtime._condition("door_shut") is False
    assert runtime._condition("never_declared") is False


def test_the_axis_tokens_still_work():
    """``axis != 0`` is authored in three shipping graphs; it reads runtime state."""
    runtime = _runtime()
    runtime.values["axis"] = 0.0
    assert runtime._condition("axis != 0") is False
    assert runtime._condition("axis == 0") is True

    runtime.values["axis"] = 1.0
    assert runtime._condition("axis != 0") is True
    assert runtime._condition("axis == 0") is False


@pytest.mark.parametrize("value", [None, [], {}, object()])
def test_non_numeric_non_string_values_are_unchanged(value):
    """Out of scope on purpose: these were false before and still are."""
    assert _runtime()._condition(value) is False


# ---------------------------------------------------------------------------
# if_else, end to end
# ---------------------------------------------------------------------------


def _branch_taken(condition) -> str:
    """Which flow port a real ``if_else`` fires for this condition value."""
    graph = normalize_logic_graph({
        "format": "zennity.logic_graph", "version": 1, "name": "branch",
        "nodes": [
            {"id": "e", "type": "event_update", "position": [0.0, 0.0]},
            {"id": "b", "type": "if_else", "position": [200.0, 0.0],
             "properties": {"condition": condition}},
        ],
        "edges": [{"from_node": "e", "from_port": "next", "to_node": "b", "to_port": "in"}],
    })
    runtime = LogicGraphRuntime(graph)
    from engine.logic.runtime.registry import registry

    node = next(n for n in graph["nodes"] if n["id"] == "b")
    return registry.executors["if_else"](runtime, node, object(), 1.0 / 60.0)[0]


@pytest.mark.parametrize("condition,port", [
    (True, "true"), (False, "false"),
    (1, "true"), (0, "false"),
    (1.0, "true"), (0.0, "false"), (-1.0, "true"), (0.5, "true"),
    ("true", "true"), ("false", "false"),
])
def test_if_else_fires_the_right_port(condition, port):
    assert _branch_taken(condition) == port


def test_if_else_resolves_a_variable_condition():
    graph = normalize_logic_graph({
        "format": "zennity.logic_graph", "version": 1, "name": "branchvar",
        "nodes": [
            {"id": "e", "type": "event_update", "position": [0.0, 0.0]},
            {"id": "b", "type": "if_else", "position": [200.0, 0.0],
             "properties": {"condition": "door_open"}},
        ],
        "edges": [{"from_node": "e", "from_port": "next", "to_node": "b", "to_port": "in"}],
    })
    from engine.logic.runtime.registry import registry

    node = next(n for n in graph["nodes"] if n["id"] == "b")

    runtime = LogicGraphRuntime(graph)
    runtime.variables["door_open"] = True
    assert registry.executors["if_else"](runtime, node, object(), 1 / 60)[0] == "true"

    runtime = LogicGraphRuntime(graph)
    runtime.variables["door_open"] = False
    assert registry.executors["if_else"](runtime, node, object(), 1 / 60)[0] == "false"


# ---------------------------------------------------------------------------
# The asset this was found through
# ---------------------------------------------------------------------------


class _Player:
    """A movable player. ``move`` takes the amount the executor computed."""

    rigidbody = None
    components: list = []

    def __init__(self, axis: float) -> None:
        self.x = 0.0
        self.y = 0.0
        self._axis = axis

    def axis(self, negative, positive) -> float:
        return self._axis

    def move(self, delta_x, delta_y=0.0) -> None:
        self.x += float(delta_x)
        self.y += float(delta_y)


def _play(axis: float, dt: float = 1.0 / 60.0) -> tuple[_Player, LogicGraphRuntime]:
    runtime = LogicGraphRuntime(normalize_logic_graph(load_logic_graph(PLAYER_GRAPH)))
    player = _Player(axis)
    runtime.update(player, dt)
    return player, runtime


#: ``speed`` authored on the graph's ``move`` node.
PLAYER_SPEED = 220.0


def test_the_player_moves_right():
    player, runtime = _play(1.0)
    assert "move" in runtime.executed_nodes
    assert player.x == pytest.approx(PLAYER_SPEED / 60.0)


def test_the_player_moves_left():
    player, runtime = _play(-1.0)
    assert "move" in runtime.executed_nodes
    assert player.x == pytest.approx(-PLAYER_SPEED / 60.0)
    assert player.x < 0.0, "a negative axis has to move the other way"


def test_a_neutral_axis_does_not_move_the_player():
    player, runtime = _play(0.0)
    assert "move" not in runtime.executed_nodes
    assert player.x == 0.0


@pytest.mark.parametrize("axis", [0.25, 0.5, -0.25, -0.5])
def test_an_analog_axis_moves_proportionally(axis: float):
    """The reason the axis is a float in the first place.

    A gamepad half-pressed must move half as far. Before the fix every one of
    these read as false and the player stood still.
    """
    player, runtime = _play(axis)
    assert "move" in runtime.executed_nodes
    assert player.x == pytest.approx(axis * PLAYER_SPEED / 60.0)


def test_the_player_graph_itself_is_structurally_sound():
    """So a later failure here points at the runtime, not at the asset.

    The graph was never the problem: no phantom node, no orphan edge. It is
    asserted because the bug looked like a broken asset for a long time.
    """
    from engine.logic.graph_asset import node_port_definitions
    from engine.logic.node_definitions import NODE_DEFINITIONS
    from engine.logic.node_definitions.catalogue import resolve_node_id

    graph = normalize_logic_graph(load_logic_graph(PLAYER_GRAPH))
    nodes = {str(n["id"]): n for n in graph["nodes"]}

    assert [t for t in {str(n["type"]) for n in graph["nodes"]}
            if resolve_node_id(t) not in NODE_DEFINITIONS] == []
    for edge in graph["edges"]:
        source, target = nodes[str(edge["from_node"])], nodes[str(edge["to_node"])]
        assert str(edge["from_port"]) in {n for n, _k in node_port_definitions(source)["outputs"]}
        assert str(edge["to_port"]) in {n for n, _k in node_port_definitions(target)["inputs"]}


# ---------------------------------------------------------------------------
# The reauthored AI graphs must be untouched by this
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("asset", ("BossAILogic", "EnemyAILogic"))
def test_the_ai_graphs_do_not_depend_on_this_helper(asset: str):
    """Item 14E moved them onto ``compare_number``, which compares numbers.

    Asserted rather than assumed: if a future edit puts an ``if_else`` back into
    a chase chain, that graph starts depending on ``_condition`` again and this
    says so.
    """
    graph = normalize_logic_graph(
        load_logic_graph(REPO_ROOT / "Assets" / "Logic" / f"{asset}.zlogic")
    )
    assert "if_else" not in {str(n["type"]) for n in graph["nodes"]}
    assert "compare_number" in {str(n["type"]) for n in graph["nodes"]}
