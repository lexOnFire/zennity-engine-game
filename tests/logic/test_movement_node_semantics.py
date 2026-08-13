"""``move`` and ``move_by``: every authorable field reaches the runtime.

PHASE 9 recovery item 9.

Both nodes exposed properties the Inspector let an author edit and the executor
never read. Measured, not inferred:

* ``move_by`` with ``delta_x=120`` moved the object **zero pixels**, while the
  same value in ``x`` moved it 2.0 at 60fps. ``delta_x``/``delta_y`` were
  declared, authorable and inert.
* ``move`` declared ``direction_x``/``direction_y``; the executor calls
  ``game.move(amount * speed * dt)`` on a single axis and reads neither.
* ``move.speed`` declared 100 while the executor fell back to 200. That
  fallback was **unreachable**: the catalogue seeds ``speed`` into every
  normalized node, so the literal only applied to a graph carrying none -- and
  all five shipping graphs author it explicitly (200/180/220/220/160).
* ``_EXPLICIT_PORT_CONTRACTS`` declared ``move_by`` twice with different pins.
  The second silently won, which is how ``delta_x``/``delta_y`` reached the
  palette and how the ``target`` pin was lost.

``move_by`` applies a **velocity**, not a displacement: the executor multiplies
by ``dt`` and writes ``rigidbody.velocity``, and the 24 shipping instances set
values like 240 and 380 that are only sensible as pixels per second. The
declaration used to say "Mover Por" / "Delta X"; it now says what it does.

One gap is deliberately left and recorded rather than fixed --
``move_by.velocity``. See ``test_the_velocity_pin_is_declared_but_unread``.
"""

from __future__ import annotations

import ast
import inspect
import pathlib
import textwrap

import pytest

from engine.logic.graph_asset import (
    NODE_DEFINITIONS,
    NODE_PORT_DEFINITIONS,
    load_logic_graph,
    normalize_logic_graph,
    save_logic_graph,
)
from engine.logic.node_definitions.catalogue import ensure_catalogue_loaded
from engine.logic.node_system import load_runtime_node_modules
from engine.logic.runtime.core import LogicGraphRuntime
from engine.logic.runtime.registry import registry

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
DT = 1.0 / 60.0


@pytest.fixture(scope="module", autouse=True)
def _loaded():
    ensure_catalogue_loaded()
    load_runtime_node_modules()


class _Target:
    """A host with the one-argument ``move`` the executor actually calls."""

    def __init__(self):
        self.x = 0.0
        self.y = 0.0
        self.calls: list[tuple] = []

    def move(self, *args):
        self.calls.append(args)
        if len(args) == 1:
            self.x += args[0]
        else:
            self.x += args[0]
            self.y += args[1]


def _run(node_type: str, properties: dict, axis: float = 1.0, dt: float = DT):
    graph = normalize_logic_graph({
        "format": "zennity.logic_graph", "version": 1, "name": "Movement",
        "nodes": [{"id": "n", "type": node_type, "position": [0.0, 0.0],
                   "properties": dict(properties)}],
        "edges": [],
    })
    runtime = LogicGraphRuntime(graph)
    runtime.values["axis"] = axis
    target = _Target()
    registry.executors[node_type](runtime, graph["nodes"][0], target, dt)
    return target, graph["nodes"][0]


def _property_fallbacks(node_type: str, key: str) -> list:
    """Literal fallbacks the executor uses for ``properties.get(key, ...)``."""
    source = textwrap.dedent(inspect.getsource(registry.executors[node_type]))
    return [
        node.args[1].value
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "get"
        and len(node.args) == 2
        and isinstance(node.args[0], ast.Constant)
        and node.args[0].value == key
        and isinstance(node.args[1], ast.Constant)
    ]


def _executor_reads(node_type: str) -> set[str]:
    """Property keys the executor literally asks for."""
    source = textwrap.dedent(inspect.getsource(registry.executors[node_type]))
    keys: set[str] = set()
    for node in ast.walk(ast.parse(source)):
        if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)):
            continue
        if node.func.attr in ("get", "_read_input") and node.args:
            for argument in node.args[:2]:
                if isinstance(argument, ast.Constant) and isinstance(argument.value, str):
                    keys.add(argument.value)
    if "_read_target" in source:
        keys.add("target")
    return keys


# ---------------------------------------------------------------------------
# 1/4. move: one default, and displacement follows it
# ---------------------------------------------------------------------------

def test_the_declared_and_runtime_speed_defaults_are_the_same():
    declared = NODE_DEFINITIONS["move"]["properties"]["speed"]
    assert _property_fallbacks("move", "speed") == [declared], (
        f"declared default {declared}, executor fallback "
        f"{_property_fallbacks('move', 'speed')}"
    )


@pytest.mark.parametrize("speed", (100.0, 175.0, 200.0))
def test_the_authored_speed_reaches_the_runtime(speed: float):
    target, _node = _run("move", {"speed": speed})
    assert target.x == pytest.approx(speed * DT)


def test_omitting_speed_uses_the_declared_default():
    """The catalogue seeds it, so the executor fallback is never the answer."""
    target, node = _run("move", {})
    assert node["properties"]["speed"] == NODE_DEFINITIONS["move"]["properties"]["speed"]
    assert target.x == pytest.approx(100.0 * DT)


def test_displacement_is_linear_in_speed():
    slow, _ = _run("move", {"speed": 100.0})
    fast, _ = _run("move", {"speed": 200.0})
    assert fast.x == pytest.approx(slow.x * 2)


# ---------------------------------------------------------------------------
# 5/6. Nothing authorable is ignored
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("node_type", ("move", "move_by"))
def test_no_authorable_property_is_ignored_by_the_executor(node_type: str):
    """The rule item 9 exists for: a field the Inspector offers must do something.

    ``velocity`` used to be carved out of this check -- the one recorded
    exception, kept visible so it stayed a known gap. PHASE 9 recovery item 14F
    removed the pin instead, so the carve-out went with it and the rule is now
    unconditional: every authorable field on these nodes is read by their
    executor, with no name spelled into the gate.
    """
    authorable = set(NODE_DEFINITIONS[node_type].get("properties", {}))
    ignored = authorable - _executor_reads(node_type)
    assert not ignored, f"{node_type} offers {sorted(ignored)} and reads none of them"


@pytest.mark.parametrize("field", ("delta_x", "delta_y"))
def test_the_dead_delta_fields_are_gone(field: str):
    assert field not in NODE_DEFINITIONS["move_by"].get("properties", {})
    assert field not in {name for name, _k in NODE_PORT_DEFINITIONS["move_by"]["inputs"]}


@pytest.mark.parametrize("field", ("direction_x", "direction_y"))
def test_the_dead_direction_fields_are_gone(field: str):
    assert field not in NODE_DEFINITIONS["move"].get("properties", {})


def test_move_by_is_declared_exactly_once():
    """The duplicate dict key is how the dead fields reached the palette."""
    source = (
        REPO_ROOT / "engine" / "logic" / "node_definitions" / "catalogue.py"
    ).read_text(encoding="utf-8")
    assert source.count('"move_by": {"inputs"') == 1


def test_the_target_pin_survived_the_deduplication():
    """The losing duplicate had no ``target``; the executor calls _read_target."""
    assert "target" in {name for name, _k in NODE_PORT_DEFINITIONS["move_by"]["inputs"]}


# ---------------------------------------------------------------------------
# move_by: velocity semantics, measured
# ---------------------------------------------------------------------------

def test_the_authored_velocity_reaches_the_runtime():
    target, _node = _run("move_by", {"x": 120.0, "y": 0.0})
    assert target.x == pytest.approx(120.0 * DT)


def test_move_by_scales_with_dt_so_the_fields_are_a_velocity():
    """Displacement doubles when dt doubles -- that is a velocity, not a delta."""
    one, _ = _run("move_by", {"x": 120.0, "y": 0.0}, dt=DT)
    two, _ = _run("move_by", {"x": 120.0, "y": 0.0}, dt=DT * 2)
    assert two.x == pytest.approx(one.x * 2)


def test_the_labels_no_longer_promise_a_displacement():
    import engine.logic.node_definitions.movement_nodes as definitions

    definition = definitions.MoveByNode.__node_definition__
    labels = {pin.id: pin.label_key for pin in definition.inputs}
    assert "Delta" not in labels.get("x", "")
    assert "Delta" not in labels.get("y", "")


def test_the_velocity_pin_is_gone():
    """Item 9 recorded this gap; item 14F closed it, and the check is inverted.

    It used to assert the opposite -- that ``velocity`` was declared and that
    the executor did not read it. That was true and worth pinning: BossAILogic
    and EnemyAILogic wired ``multiply_number.value`` into it while the executor
    read ``x``/``y``, so two enemies computed a movement and stood still.
    Deleting the pin then would have orphaned two shipping edges; reading it
    would have been a gameplay decision item 9 was not allowed to take.

    Item 14E reauthored both graphs onto ``x``/``y``, leaving a port with no
    producer and no consumer, and item 14F removed it at its only source -- the
    projection table, since the declarative ``MoveByNode`` never had it. The
    executor is untouched: it read ``x``/``y`` before and reads them now.
    """
    assert "velocity" not in {
        name for name, _kind in NODE_PORT_DEFINITIONS["move_by"]["inputs"]
    }
    assert "velocity" not in NODE_DEFINITIONS["move_by"].get("properties", {})
    assert "velocity" not in _executor_reads("move_by")

    # No alias took its place: there was no proven semantics to migrate to,
    # and a lie -- velocity -> x, say -- would be worse than the removal.
    from engine.logic import port_aliases

    assert port_aliases.resolve_input_port("velocity", ["in"]) == "velocity"
    from engine.logic.node_definitions.catalogue import NODE_ID_ALIASES

    assert "velocity" not in NODE_ID_ALIASES

    # The pins that do work are still there.
    inputs = {name for name, _kind in NODE_PORT_DEFINITIONS["move_by"]["inputs"]}
    assert {"in", "target", "x", "y"} <= inputs


def test_no_graph_wires_velocity_any_more():
    """Inverted by item 14E: the two graphs that wired it stopped.

    This counted the assets feeding ``move_by.velocity`` -- an input the
    executor never reads -- and held at exactly two so a third would force the
    decision. Item 14E reauthored both onto ``move_by.x`` / ``move_by.y``, so
    the set is now empty.

    That makes ``velocity`` a port with no producer and no consumer, which is
    precisely the question item 14F was left to answer. The assertion is kept
    so a graph reaching for it again is caught immediately.
    """
    wired = set()
    for path in sorted((REPO_ROOT / "Assets").rglob("*.zlogic")):
        graph = normalize_logic_graph(load_logic_graph(path))
        nodes = {str(n["id"]): n for n in graph["nodes"]}
        for edge in graph["edges"]:
            target = nodes.get(str(edge.get("to_node")))
            if (
                target
                and str(target["type"]) == "move_by"
                and str(edge.get("to_port")) == "velocity"
            ):
                wired.add(path.name)
    assert wired == set(), wired


# ---------------------------------------------------------------------------
# 3/8. Save, reopen, and the authored value still drives the runtime
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("node_type,properties,expected", [
    ("move", {"speed": 175.0}, 175.0 * DT),
    ("move_by", {"x": 90.0, "y": 0.0}, 90.0 * DT),
])
def test_save_reopen_preserves_the_authored_value_and_the_runtime_uses_it(
    tmp_path: pathlib.Path, node_type: str, properties: dict, expected: float
):
    graph = normalize_logic_graph({
        "format": "zennity.logic_graph", "version": 1, "name": "RoundTrip",
        "nodes": [{"id": "n", "type": node_type, "position": [0.0, 0.0],
                   "properties": dict(properties)}],
        "edges": [],
    })
    destination = tmp_path / f"{node_type}.zlogic"
    save_logic_graph(destination, graph)
    reopened = normalize_logic_graph(load_logic_graph(destination))

    assert reopened == graph
    for key, value in properties.items():
        assert reopened["nodes"][0]["properties"][key] == value

    runtime = LogicGraphRuntime(reopened)
    runtime.values["axis"] = 1.0
    target = _Target()
    registry.executors[node_type](runtime, reopened["nodes"][0], target, DT)
    assert target.x == pytest.approx(expected)


def test_a_new_save_writes_only_the_canonical_property_names(tmp_path: pathlib.Path):
    graph = normalize_logic_graph({
        "format": "zennity.logic_graph", "version": 1, "name": "Canonical",
        "nodes": [{"id": "n", "type": "move_by", "position": [0.0, 0.0],
                   "properties": {"x": 10.0, "y": 20.0}}],
        "edges": [],
    })
    destination = tmp_path / "canonical.zlogic"
    save_logic_graph(destination, graph)
    saved = set(load_logic_graph(destination)["nodes"][0].get("properties", {}))
    assert not saved & {"delta_x", "delta_y"}


# ---------------------------------------------------------------------------
# 10. Mutation: the gate must fail when the executor drifts
# ---------------------------------------------------------------------------

def test_pointing_the_executor_at_another_field_makes_the_gate_fail(monkeypatch):
    def _drifted(runtime, node, game, dt):
        properties = node.get("properties", {})
        return [str(properties.get("totally_other_field", "next"))]

    monkeypatch.setitem(registry.executors, "move_by", _drifted)
    authorable = set(NODE_DEFINITIONS["move_by"].get("properties", {}))
    ignored = authorable - _executor_reads("move_by")
    assert ignored, "the ignored-field check cannot fail, so it proves nothing"
