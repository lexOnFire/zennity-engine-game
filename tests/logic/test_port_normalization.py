"""Legacy flow ports resolve against each node's contract, and only then.

PHASE 9 recovery item 5.

The tempting rule is ``in -> exec``. Measured across every shipping ``.zlogic``
it would be a disaster:

    input  "in"    302 edges across 47 node types -- correct for 44 of them
    input  "exec"   18 edges across  7 node types -- correct for all 7
    output "next"  245 edges across 35 node types -- correct for 34 of them

``move_by`` really declares ``in``; ``play_animation`` really declares ``exec``.
Neither is "the legacy spelling", so the node's own contract is the only thing
that can decide, and the rewrite has to be relative to it.

What the resolver refuses to do matters as much as what it does: it never
guesses between two flow inputs, never touches a data pin, and never attaches an
edge to a semantic branch that happens to be first in the list.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from engine.logic.graph_asset import (
    NODE_PORT_DEFINITIONS,
    load_logic_graph,
    node_port_definitions,
    normalize_logic_graph,
    save_logic_graph,
)
from engine.logic.port_aliases import (
    FLOW_INPUT_SYNONYMS,
    FLOW_OUTPUT_SYNONYMS,
    flow_pins,
    is_ambiguous_input,
    resolve_input_port,
    resolve_output_port,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def _flow(node_id: str, key: str) -> list[str]:
    return flow_pins(NODE_PORT_DEFINITIONS[node_id][key])


# ---------------------------------------------------------------------------
# The rule
# ---------------------------------------------------------------------------

def test_a_synonym_resolves_to_the_pin_the_node_declares():
    assert resolve_input_port("in", ["exec"]) == "exec"
    assert resolve_input_port("exec", ["in"]) == "in"


def test_both_directions_are_real_on_real_nodes():
    """Not symmetric by accident: two shipping nodes disagree with each other."""
    assert resolve_input_port("in", _flow("play_animation", "inputs")) == "exec"
    assert resolve_input_port("exec", _flow("move_by", "inputs")) == "in"


def test_a_declared_name_is_never_rewritten():
    assert resolve_input_port("in", ["in"]) == "in"
    assert resolve_output_port("next", ["next", "exec_failure"]) == "next"


@pytest.mark.parametrize("port", ["value", "target", "text", "a", "b", "condition", "state"])
def test_a_data_pin_is_never_folded_into_a_flow_pin(port: str):
    assert resolve_input_port(port, ["exec"]) == port
    assert resolve_output_port(port, ["next"]) == port


def test_two_flow_inputs_are_not_guessed():
    assert resolve_input_port("in", ["in", "exec"]) == "in"
    assert resolve_input_port("enter", ["in", "exec"]) == "enter"
    assert is_ambiguous_input("enter", ["in", "exec"])


def test_an_unknown_contract_is_left_alone():
    assert resolve_input_port("in", []) == "in"
    assert resolve_output_port("next", []) == "next"


def test_a_semantic_outcome_is_never_treated_as_a_continuation():
    """has_save declares three different outcomes; "next" names none of them."""
    outcomes = ["exec_exists", "exec_not_exists", "exec_failure"]
    assert resolve_output_port("next", outcomes) == "next"
    assert resolve_output_port("exec_done", outcomes) == "exec_done"


def test_no_synonym_is_also_a_semantic_outcome():
    outcomes = {"exec_failure", "true", "false", "exec_exists", "grounded", "held"}
    assert not (FLOW_INPUT_SYNONYMS | FLOW_OUTPUT_SYNONYMS) & outcomes


@pytest.mark.parametrize("declared", [["in"], ["exec"], ["in", "exec"], []])
def test_resolution_is_idempotent(declared):
    candidates = sorted(FLOW_INPUT_SYNONYMS | FLOW_OUTPUT_SYNONYMS) + ["value", "", "unknown"]
    for port in candidates:
        once = resolve_input_port(port, declared)
        assert resolve_input_port(once, declared) == once, (port, declared)
        once_out = resolve_output_port(port, declared)
        assert resolve_output_port(once_out, declared) == once_out, (port, declared)


def test_every_rewrite_lands_on_a_declared_pin():
    """Across the whole catalogue, a rewrite may only produce a real pin."""
    for node_id in NODE_PORT_DEFINITIONS:
        declared_in = _flow(node_id, "inputs")
        declared_out = _flow(node_id, "outputs")
        for port in FLOW_INPUT_SYNONYMS:
            resolved = resolve_input_port(port, declared_in)
            if resolved != port:
                assert resolved in declared_in, (node_id, port, resolved)
        for port in FLOW_OUTPUT_SYNONYMS:
            resolved = resolve_output_port(port, declared_out)
            if resolved != port:
                assert resolved in declared_out, (node_id, port, resolved)


# ---------------------------------------------------------------------------
# Load, save, order
# ---------------------------------------------------------------------------

def _graph(edges, nodes):
    return {
        "format": "zennity.logic_graph", "version": 1, "name": "PortNorm",
        "nodes": nodes, "edges": edges,
    }


def test_legacy_play_animation_in_resolves_to_exec():
    graph = _graph(
        [{"from_node": "e", "from_port": "next", "to_node": "a", "to_port": "in"}],
        [{"id": "e", "type": "event_start", "position": [0.0, 0.0]},
         {"id": "a", "type": "play_animation", "position": [1.0, 0.0]}],
    )
    assert normalize_logic_graph(graph)["edges"][0]["to_port"] == "exec"


def test_a_node_that_really_uses_in_keeps_it():
    graph = _graph(
        [{"from_node": "e", "from_port": "next", "to_node": "m", "to_port": "exec"}],
        [{"id": "e", "type": "event_start", "position": [0.0, 0.0]},
         {"id": "m", "type": "move_by", "position": [1.0, 0.0]}],
    )
    assert normalize_logic_graph(graph)["edges"][0]["to_port"] == "in"


def test_port_resolution_happens_after_node_id_resolution():
    """A legacy node id must resolve first, or the wrong contract is consulted.

    ``load_scene`` resolves to ``scene.load_scene``; only that definition can
    say which entry pin the edge should land on.
    """
    graph = _graph(
        [{"from_node": "e", "from_port": "next", "to_node": "s", "to_port": "exec"}],
        [{"id": "e", "type": "event_start", "position": [0.0, 0.0]},
         {"id": "s", "type": "load_scene", "position": [1.0, 0.0]}],
    )
    normalized = normalize_logic_graph(graph)
    assert normalized["nodes"][1]["type"] == "scene.load_scene"
    declared = flow_pins(NODE_PORT_DEFINITIONS["scene.load_scene"]["inputs"])
    assert normalized["edges"][0]["to_port"] in declared


def test_normalizing_twice_changes_nothing():
    graph = _graph(
        [{"from_node": "e", "from_port": "next", "to_node": "a", "to_port": "in"}],
        [{"id": "e", "type": "event_start", "position": [0.0, 0.0]},
         {"id": "a", "type": "play_animation", "position": [1.0, 0.0]}],
    )
    once = normalize_logic_graph(graph)
    assert normalize_logic_graph(once) == once


def test_a_legacy_graph_is_saved_with_the_canonical_port(tmp_path: Path):
    graph = _graph(
        [{"from_node": "e", "from_port": "next", "to_node": "a", "to_port": "in"}],
        [{"id": "e", "type": "event_start", "position": [0.0, 0.0]},
         {"id": "a", "type": "play_animation", "position": [1.0, 0.0]}],
    )
    destination = tmp_path / "Legacy.zlogic"
    save_logic_graph(destination, normalize_logic_graph(graph))
    written = json.loads(destination.read_text(encoding="utf-8"))
    assert written["edges"][0]["to_port"] == "exec"


def test_opening_a_shipping_asset_does_not_rewrite_it():
    """Normalization is in memory. Nothing on disk changes by being read."""
    checked = 0
    for path in sorted(REPO_ROOT.rglob("*.zlogic")):
        if ".git" in path.parts:
            continue
        before = path.read_bytes()
        normalize_logic_graph(load_logic_graph(path))
        assert path.read_bytes() == before, path.name
        checked += 1
    assert checked


# ---------------------------------------------------------------------------
# The shipping graphs
# ---------------------------------------------------------------------------

def _orphans(graph) -> list[str]:
    nodes = {str(n["id"]): n for n in graph["nodes"]}
    found = []
    for edge in graph["edges"]:
        source, target = nodes.get(str(edge["from_node"])), nodes.get(str(edge["to_node"]))
        if source is not None:
            outputs = {n for n, _k in node_port_definitions(source)["outputs"]}
            if str(edge["from_port"]) not in outputs:
                found.append(f"{source['type']}.{edge['from_port']}>out")
        if target is not None:
            inputs = {n for n, _k in node_port_definitions(target)["inputs"]}
            if str(edge["to_port"]) not in inputs:
                found.append(f"{target['type']}.{edge['to_port']}>in")
    return found


#: Every edge this item was expected to repair, and the asset it lives in.
RESOLVED_EDGES = {
    "play_animation": ("in", "exec", 4),
    "load_game": ("in", "exec", 1),
    "start_behavior_tree": ("in", "exec", 1),
}


@pytest.mark.parametrize("node_id", sorted(RESOLVED_EDGES))
def test_the_legacy_edges_for_this_node_are_all_resolved(node_id: str):
    legacy, canonical, expected_count = RESOLVED_EDGES[node_id]
    seen = 0
    for path in sorted(REPO_ROOT.rglob("*.zlogic")):
        if ".git" in path.parts or ".pytest_tmp" in path.parts:
            continue
        raw = json.loads(path.read_text(encoding="utf-8"))
        types = {str(n["id"]): str(n.get("type", "")) for n in raw.get("nodes", [])}
        from engine.logic.node_definitions.catalogue import resolve_node_id

        saved = [
            edge for edge in raw.get("edges", [])
            if resolve_node_id(types.get(str(edge.get("to_node")), "")) == node_id
            and str(edge.get("to_port", "in")) == legacy
        ]
        if not saved:
            continue
        normalized = normalize_logic_graph(load_logic_graph(path))
        nodes = {str(n["id"]): n for n in normalized["nodes"]}
        for edge in normalized["edges"]:
            target = nodes.get(str(edge["to_node"]))
            if target is not None and target["type"] == node_id:
                assert edge["to_port"] == canonical, f"{path.name}: {edge}"
                seen += 1
    assert seen == expected_count, f"expected {expected_count} edges, resolved {seen}"


def test_no_shipping_graph_gains_an_orphan_edge():
    from tests.logic.stage2.test_shipping_graphs_still_work import ORPHAN_BASELINE

    for path in sorted(REPO_ROOT.rglob("*.zlogic")):
        if ".git" in path.parts:
            continue
        key = path.relative_to(REPO_ROOT).as_posix()
        recorded = set(ORPHAN_BASELINE["orphan_edges_by_asset"].get(key, []))
        actual = set(_orphans(normalize_logic_graph(load_logic_graph(path))))
        assert not actual - recorded, f"{key} gained {sorted(actual - recorded)}"


def test_every_shipping_graph_still_builds_a_runtime():
    from engine.logic.runtime import LogicGraphRuntime

    for path in sorted(REPO_ROOT.rglob("*.zlogic")):
        if ".git" in path.parts:
            continue
        LogicGraphRuntime(normalize_logic_graph(load_logic_graph(path)))


# ---------------------------------------------------------------------------
# What is deliberately NOT resolved
# ---------------------------------------------------------------------------

def test_has_save_next_is_left_as_a_real_mismatch():
    """It names no outcome, and the node has three.

    ``has_save`` declares exec_exists / exec_not_exists / exec_failure. An edge
    saved as ``next`` does not say which branch was meant, so attaching it to
    one would silently pick a behaviour. It stays orphaned and visible.

    Its executor returns ``["false"]``, which the contract does not declare
    either -- a contract/executor mismatch of the same kind item 4.2 fixed for
    the animation nodes, and not something port normalization can repair.
    """
    declared = _flow("has_save", "outputs")
    assert declared == ["exec_exists", "exec_not_exists", "exec_failure"]
    assert resolve_output_port("next", declared) == "next"


def test_a_pure_data_node_gets_no_entry_pin_invented():
    """get_position declares no flow input at all; "in" has nowhere to go."""
    assert _flow("get_position", "inputs") == []
    assert resolve_input_port("in", []) == "in"


def test_the_current_palette_needs_no_normalization(tmp_path: Path):
    """A graph authored today must already use canonical ports."""
    chain = ["event_update", "input_axis", "raycast", "play_animation",
             "set_ui_text", "scene.load_scene"]
    nodes = [{"id": f"n{i}", "type": t, "position": [i * 200.0, 0.0]}
             for i, t in enumerate(chain)]
    edges = []
    for index in range(len(chain) - 1):
        outputs = flow_pins(NODE_PORT_DEFINITIONS[chain[index]]["outputs"])
        inputs = flow_pins(NODE_PORT_DEFINITIONS[chain[index + 1]]["inputs"])
        edges.append({"from_node": f"n{index}", "from_port": outputs[0],
                      "to_node": f"n{index + 1}", "to_port": inputs[0], "kind": "flow"})
    graph = _graph(edges, nodes)

    normalized = normalize_logic_graph(graph)
    authored = {(e["from_port"], e["to_port"]) for e in graph["edges"]}
    resolved = {(e["from_port"], e["to_port"]) for e in normalized["edges"]}
    assert resolved == authored, "normalization rewrote a freshly authored graph"
    assert not _orphans(normalized)

    destination = tmp_path / "Fresh.zlogic"
    save_logic_graph(destination, normalized)
    assert normalize_logic_graph(load_logic_graph(destination)) == normalized
