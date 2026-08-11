"""Phase 9.5B Stage 1 — legacy ports and ids converge on one canonical form."""
from __future__ import annotations

import pytest

from engine.logic.graph_normalizer import normalize_logic_graph
from engine.logic.port_aliases import (
    CANONICAL_SUCCESS_PORT,
    EXEC_PORT_ALIASES,
    NODE_EXEC_PORT_ALIASES,
    NODE_ID_ALIASES,
    canonical_exec_port,
    canonical_node_id,
)


def graph(nodes, edges):
    return {"format": "zennity.logic", "name": "t", "nodes": nodes, "edges": edges}


# ------------------------------------------------------------ the alias table
def test_canonical_success_port_is_next():
    assert CANONICAL_SUCCESS_PORT == "next"


def test_alias_table_is_one_way():
    """No alias value may itself be an alias key, or normalisation could chain."""
    assert not (set(EXEC_PORT_ALIASES) & set(EXEC_PORT_ALIASES.values()))
    for node_type, table in NODE_EXEC_PORT_ALIASES.items():
        assert not (set(table) & set(table.values())), node_type
    assert not (set(NODE_ID_ALIASES) & set(NODE_ID_ALIASES.values()))


@pytest.mark.parametrize("legacy", sorted(EXEC_PORT_ALIASES))
def test_resolution_is_idempotent(legacy):
    once = canonical_exec_port(legacy)
    assert canonical_exec_port(once) == once


def test_exec_done_resolves_to_next():
    assert canonical_exec_port("exec_done") == "next"
    assert canonical_exec_port("exec_success") == "next"


def test_semantic_ports_are_never_folded_into_next():
    for port in ("exec_failure", "limit_reached", "exec_hit", "grounded"):
        assert canonical_exec_port(port) == port


def test_true_false_stay_generic_without_a_node_type():
    """if_else/compare_* legitimately use true/false; 23 saved edges rely on it."""
    assert canonical_exec_port("true") == "true"
    assert canonical_exec_port("true", "if_else") == "true"
    assert canonical_exec_port("true", "compare_number") == "true"


def test_true_false_are_node_scoped_for_branch_nodes():
    assert canonical_exec_port("true", "is_grounded") == "grounded"
    assert canonical_exec_port("false", "is_grounded") == "airborne"
    assert canonical_exec_port("true", "key_held") == "held"
    assert canonical_exec_port("true", "key_pressed") == "exec_pressed"


def test_node_id_aliases_resolve():
    assert canonical_node_id("scene_load") == "scene.load_scene"
    assert canonical_node_id("open_scene") == "scene.load_scene"
    assert canonical_node_id("quit_game") == "app.quit"
    assert canonical_node_id("on_ui_click") == "ui.button_clicked"
    assert canonical_node_id("move_by") == "move_by"  # not an alias


# ------------------------------------------------------------- normalisation
def test_legacy_exec_done_edge_is_rewritten_on_load():
    """The Phase 9.5A P0: palette emitted exec_done, runtime followed next."""
    g = normalize_logic_graph(graph(
        [{"id": "a", "type": "move_by"}, {"id": "b", "type": "log_message"}],
        [{"from": "a", "from_port": "exec_done", "to": "b", "to_port": "exec"}],
    ))
    assert [e["from_port"] for e in g["edges"]] == ["next"]


def test_already_canonical_edges_are_untouched():
    g = normalize_logic_graph(graph(
        [{"id": "a", "type": "move_by"}, {"id": "b", "type": "log_message"}],
        [{"from": "a", "from_port": "next", "to": "b", "to_port": "exec"}],
    ))
    assert [e["from_port"] for e in g["edges"]] == ["next"]


def test_normalisation_is_idempotent():
    g1 = normalize_logic_graph(graph(
        [{"id": "a", "type": "move_by"}, {"id": "b", "type": "log_message"}],
        [{"from": "a", "from_port": "exec_done", "to": "b", "to_port": "exec"}],
    ))
    g2 = normalize_logic_graph(g1)
    assert [e["from_port"] for e in g1["edges"]] == [e["from_port"] for e in g2["edges"]]


def test_legacy_node_id_is_rewritten_on_load():
    g = normalize_logic_graph(graph([{"id": "a", "type": "scene_load"}], []))
    assert g["nodes"][0]["type"] == "scene.load_scene"


def test_branch_node_true_edge_is_remapped():
    """12 saved edges use `true` on key_held."""
    g = normalize_logic_graph(graph(
        [{"id": "a", "type": "key_held"}, {"id": "b", "type": "move_by"}],
        [{"from": "a", "from_port": "true", "to": "b", "to_port": "exec"}],
    ))
    assert [e["from_port"] for e in g["edges"]] == ["held"]


def test_if_else_true_edge_is_preserved():
    """The same literal must NOT be remapped on a node that owns it."""
    g = normalize_logic_graph(graph(
        [{"id": "a", "type": "if_else"}, {"id": "b", "type": "move_by"}],
        [{"from": "a", "from_port": "true", "to": "b", "to_port": "exec"}],
    ))
    assert [e["from_port"] for e in g["edges"]] == ["true"]


def test_data_port_named_out_is_not_folded_into_next():
    """The alias must only touch exec ports, never data edges."""
    g = normalize_logic_graph(graph(
        [{"id": "a", "type": "get_variable"}, {"id": "b", "type": "log_message"}],
        [{"from": "a", "from_port": "value", "to": "b", "to_port": "text"}],
    ))
    assert [e["from_port"] for e in g["edges"]] == ["value"]


# ----------------------------------------------------------------- execution
def test_normalised_legacy_graph_actually_runs_to_the_end():
    """End to end: exec_done in, flow reaches the last node."""
    from engine.logic.runtime import LogicGraphRuntime

    g = normalize_logic_graph(graph(
        [
            {"id": "start", "type": "event_start"},
            {"id": "l1", "type": "log_message", "properties": {"text": "one"}},
            {"id": "l2", "type": "log_message", "properties": {"text": "two"}},
        ],
        [
            {"from": "start", "from_port": "next", "to": "l1", "to_port": "exec"},
            {"from": "l1", "from_port": "exec_done", "to": "l2", "to_port": "exec"},
        ],
    ))

    class Game:
        name = "probe"
        def __init__(self): self.logged = []
        def log(self, message): self.logged.append(str(message))

    runtime = LogicGraphRuntime(g)
    game = Game()
    runtime.start(game)   # event_start fires here; update() resets the trace

    assert runtime.executed_nodes == ["start", "l1", "l2"], (
        f"flow stopped early; executed={runtime.executed_nodes}"
    )
    assert game.logged == ["one", "two"]
