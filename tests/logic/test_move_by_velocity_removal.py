"""``move_by.velocity`` is gone, and the reasons it could go are asserted.

PHASE 9 recovery item 14F. The pin arrived in `b19f603e` -- "resolve validator
errors ... and register port definitions" -- to quiet a validator, and no commit
in the repository's history ever made an executor read it. Item 9 found it
authorable and unread but could not remove it: BossAILogic and EnemyAILogic
wired ``multiply_number.value`` into it, so deleting the port would have
orphaned two shipping edges. Item 14E reauthored both onto ``x`` / ``y``, which
retired the last reason to keep it.

This file is the anti-vacuity proof. It does not grep for a string: it asserts
the four independent conditions that made removal correct, so that a real use
reappearing -- an executor that starts reading it, an asset that starts wiring
it, a plugin that declares it -- fails here rather than silently reintroducing
an authorable field that moves nothing.
"""

from __future__ import annotations

import ast
import inspect
import textwrap
from pathlib import Path

import pytest

from engine.logic.graph_asset import (
    NODE_DEFINITIONS,
    NODE_PORT_DEFINITIONS,
    load_logic_graph,
    node_port_definitions,
    normalize_logic_graph,
    save_logic_graph,
)
from engine.logic.runtime import LogicGraphRuntime
from engine.logic.runtime.registry import registry

REPO_ROOT = Path(__file__).resolve().parents[2]
NODE = "move_by"


def _executor_reads() -> set[str]:
    """Port/property names the executor actually asks for, read from its AST."""
    source = textwrap.dedent(inspect.getsource(registry.executors[NODE]))
    return {
        argument.value
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr in ("get", "_read_input")
        for argument in node.args[:2]
        if isinstance(argument, ast.Constant) and isinstance(argument.value, str)
    }


def _move_by_ids(graph: dict) -> set[str]:
    return {str(n["id"]) for n in graph["nodes"] if str(n["type"]) == NODE}


def _shipping_graphs():
    for path in sorted((REPO_ROOT / "Assets").rglob("*.zlogic")):
        yield path, normalize_logic_graph(load_logic_graph(path))


# ---------------------------------------------------------------------------
# 1/4. The pin is gone from its only source
# ---------------------------------------------------------------------------


def test_velocity_is_not_declared_anywhere_in_the_contract():
    assert "velocity" not in {n for n, _k in NODE_PORT_DEFINITIONS[NODE]["inputs"]}
    assert "velocity" not in {n for n, _k in NODE_PORT_DEFINITIONS[NODE]["outputs"]}
    assert "velocity" not in NODE_DEFINITIONS[NODE].get("properties", {})


def test_the_declarative_definition_never_had_it():
    """Which is why the projection table was the right place to remove it.

    ``MoveByNode`` declares ``exec``/``x``/``y`` -> ``exec_done`` and always
    did. ``velocity`` existed only in ``_EXPLICIT_PORT_CONTRACTS``, so removing
    it there removes it everywhere rather than hiding it behind an Inspector
    filter.
    """
    from engine.logic.node_definitions import movement_nodes

    declared = {pin.id for pin in movement_nodes.MoveByNode.__node_definition__.inputs}
    assert "velocity" not in declared
    assert {"x", "y"} <= declared


def test_the_pins_that_work_survived():
    inputs = {n for n, _k in NODE_PORT_DEFINITIONS[NODE]["inputs"]}
    assert {"in", "target", "x", "y"} <= inputs
    assert {n for n, _k in NODE_PORT_DEFINITIONS[NODE]["outputs"]} == {"next"}


# ---------------------------------------------------------------------------
# 2/4. The executor never read it -- and still does not
# ---------------------------------------------------------------------------


def test_the_executor_reads_x_and_y_and_not_velocity():
    reads = _executor_reads()
    assert {"x", "y"} <= reads
    assert "velocity" not in reads


def test_the_executor_was_not_touched_by_this_item():
    """Removal is a contract change, not a behaviour change.

    ``x``/``y`` are velocities -- the executor multiplies by ``dt`` -- and that
    is asserted here so "remove the dead pin" cannot quietly become "change
    what the live ones mean".
    """
    class _Target:
        x = y = 0.0
        rigidbody = None
        components: list = []

        def move(self, delta_x, delta_y=0.0):
            type(self).x += delta_x
            type(self).y += delta_y

    graph = normalize_logic_graph({
        "format": "zennity.logic_graph",
        "version": 1,
        "name": "MoveByOnly",
        "nodes": [
            {"id": "e", "type": "event_update", "position": [0.0, 0.0]},
            {"id": "m", "type": NODE, "position": [200.0, 0.0],
             "properties": {"x": 120.0, "y": 60.0}},
        ],
        "edges": [{"from_node": "e", "from_port": "next", "to_node": "m", "to_port": "in"}],
    })
    target = _Target()
    LogicGraphRuntime(graph).update(target, 1.0 / 60.0)
    assert target.x == pytest.approx(2.0)
    assert target.y == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# 3/4. Nothing outside the engine depends on it
# ---------------------------------------------------------------------------


def test_no_shipping_asset_wires_velocity():
    """Measured on normalized graphs: the raw files hide aliases and defaults."""
    offenders = []
    seen = 0
    for path, graph in _shipping_graphs():
        ids = _move_by_ids(graph)
        seen += len(ids)
        for edge in graph["edges"]:
            if str(edge.get("to_node")) in ids and str(edge.get("to_port")) == "velocity":
                offenders.append(f"{path.name}: edge into velocity")
    assert seen > 0, "no move_by instances found; this sweep would be vacuous"
    assert offenders == [], offenders


#: The legacy "stop" idiom: ``physics.set_velocity`` authored with a zero
#: vector. Three graphs carry it in their raw ``config``, and the migration
#: preserves unknown authored data verbatim -- so the property outlives the pin.
LEGACY_STOP_NODES = {
    "BossAILogic.zlogic": "stop_boss",
    "EnemyAILogic.zlogic": "stop_enemy",
}


def test_the_only_stored_velocity_left_is_the_legacy_zero_stop():
    """A property can outlive its pin, and here three do -- harmlessly.

    Removing the pin does not strip authored data: the migration copies a
    legacy node's ``config`` into ``properties`` verbatim, which is the
    pre-existing policy for values the contract does not declare. Item 14F does
    not change that policy and does not edit the assets to tidy it.

    What matters is that every survivor is the zero vector -- the legacy way of
    spelling "stop" -- so nothing was ever authored that the removal could
    discard. Each of these nodes also has ``x``/``y`` at zero, which is what the
    executor actually reads, so their behaviour is identical either way. Naming
    them keeps this honest: a fourth graph, or a non-zero value, fails here.
    """
    found = {}
    for path, graph in _shipping_graphs():
        ids = _move_by_ids(graph)
        for node in graph["nodes"]:
            if str(node["id"]) not in ids:
                continue
            properties = node.get("properties", {})
            if "velocity" in properties:
                found[path.name] = str(node["id"])
                assert list(properties["velocity"]) == [0, 0], (path.name, properties)
                assert float(properties.get("x", 0.0)) == 0.0
                assert float(properties.get("y", 0.0)) == 0.0
    assert found == LEGACY_STOP_NODES, found


def test_every_shipping_graph_still_loads_and_builds_a_runtime():
    """Removing a declared pin must not break a graph that never used it."""
    seen = 0
    for path, graph in _shipping_graphs():
        assert LogicGraphRuntime(graph) is not None, path.name
        seen += 1
    assert seen > 0


def test_removing_the_pin_created_no_orphan_edge():
    """The failure mode of deleting a port: an edge that named it dangles."""
    for path, graph in _shipping_graphs():
        nodes = {str(n["id"]): n for n in graph["nodes"]}
        for edge in graph["edges"]:
            target = nodes.get(str(edge.get("to_node")))
            if target is None or str(target["type"]) != NODE:
                continue
            inputs = {n for n, _k in node_port_definitions(target)["inputs"]}
            assert str(edge["to_port"]) in inputs, f"{path.name}: {edge['to_port']}"


# ---------------------------------------------------------------------------
# 4/4. No alias invented in its place
# ---------------------------------------------------------------------------


def test_velocity_does_not_resolve_to_another_port():
    """Removing is better than lying.

    Mapping ``velocity`` onto ``x`` (or onto a synthesized pair) would invent a
    semantics no commit ever implemented, on a pin that fed nothing. It stays
    unresolved, so a graph naming it surfaces as an unknown port instead of
    silently moving an object in a direction nobody authored.
    """
    from engine.logic import port_aliases
    from engine.logic.node_definitions.catalogue import NODE_ID_ALIASES

    assert port_aliases.resolve_input_port("velocity", ["in"]) == "velocity"
    assert "velocity" not in NODE_ID_ALIASES
    assert "velocity" not in set(NODE_ID_ALIASES.values())


# ---------------------------------------------------------------------------
# Authoring: save, reopen, and a legacy graph that still names the pin
# ---------------------------------------------------------------------------


def test_a_new_graph_saves_and_reopens_without_velocity(tmp_path):
    graph = normalize_logic_graph({
        "format": "zennity.logic_graph",
        "version": 1,
        "name": "MoveByAuthoring",
        "nodes": [
            {"id": "e", "type": "event_update", "position": [0.0, 0.0]},
            {"id": "m", "type": NODE, "position": [200.0, 0.0],
             "properties": {"x": 42.0, "y": -7.5}},
        ],
        "edges": [{"from_node": "e", "from_port": "next", "to_node": "m", "to_port": "in"}],
    })
    node = next(n for n in graph["nodes"] if n["id"] == "m")
    assert "velocity" not in node["properties"]
    assert node["properties"]["x"] == 42.0

    destination = tmp_path / "MoveByAuthoring.zlogic"
    save_logic_graph(destination, graph)
    reloaded = normalize_logic_graph(load_logic_graph(destination))
    assert reloaded == graph

    reopened = next(n for n in reloaded["nodes"] if n["id"] == "m")
    assert "velocity" not in reopened["properties"]
    assert reopened["properties"]["y"] == -7.5


def test_a_legacy_graph_naming_velocity_follows_the_existing_unknown_port_policy(tmp_path):
    """Documented, not changed: this item does not touch the global policy.

    A hand-made legacy document wiring something into ``move_by.velocity`` is
    the case that no longer exists in the repository. The loader keeps the edge
    verbatim -- it does not drop it, rewrite it, or refuse the file -- so the
    edge shows up as an unknown port, exactly like any other edge naming a pin
    the contract does not declare. That is the pre-existing policy for unknown
    ports; inventing a migration here is what section 10 forbids.
    """
    legacy = {
        "format": "zennity.generic_graph",
        "category": "Logic",
        "name": "LegacyVelocity",
        "nodes": [
            {"id": "loop", "type": "event.every_frame", "position": [0, 0]},
            {"id": "speed", "type": "math.multiply", "position": [150, 0]},
            {"id": "mover", "type": "physics.set_velocity", "position": [300, 0]},
        ],
        "edges": [
            {"from": "loop", "from_pin": "frame", "to": "mover", "to_pin": "execute"},
            {"from": "speed", "from_pin": "result", "to": "mover", "to_pin": "velocity"},
        ],
    }
    source = tmp_path / "LegacyVelocity.zlogic"
    source.write_text(__import__("json").dumps(legacy), encoding="utf-8")

    graph = normalize_logic_graph(load_logic_graph(source))

    mover = next(n for n in graph["nodes"] if str(n["id"]) == "mover")
    assert str(mover["type"]) == NODE, "the node id still migrates"
    assert "velocity" not in mover.get("properties", {})

    # Preserved as an unknown port: still there, still named, resolving to
    # nothing -- which is what makes it visible to the orphan-edge gate.
    velocity_edges = [e for e in graph["edges"] if str(e.get("to_port")) == "velocity"]
    assert len(velocity_edges) == 1
    declared = {n for n, _k in node_port_definitions(mover)["inputs"]}
    assert "velocity" not in declared

    # And the graph still loads and runs: an unknown port is not fatal.
    assert LogicGraphRuntime(graph) is not None


# ---------------------------------------------------------------------------
# The two assets item 14E reauthored, revalidated rather than re-edited
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("asset", ("BossAILogic", "EnemyAILogic"))
def test_the_reauthored_ai_graphs_are_unaffected(asset: str):
    graph = normalize_logic_graph(
        load_logic_graph(REPO_ROOT / "Assets" / "Logic" / f"{asset}.zlogic")
    )
    ids = _move_by_ids(graph)
    assert ids, asset

    driven = {
        str(e["to_port"])
        for e in graph["edges"]
        if str(e.get("to_node")) in ids and str(e.get("kind")) != "flow"
    }
    assert "velocity" not in driven
    assert {"x", "y"} <= driven
