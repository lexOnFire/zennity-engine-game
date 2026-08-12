"""Every shipping ``.zlogic`` asset still loads, normalizes and builds a runtime.

The port schema is now derived rather than hand-maintained.  That is only a safe
refactor if every graph that shipped against the old table still resolves every
one of its edges against the new one -- a dropped pin would show up here as an
orphan edge, which is exactly how the Stage 1 regressions manifested.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from engine.logic.graph_asset import (
    load_logic_graph,
    node_port_definitions,
    normalize_logic_graph,
    save_logic_graph,
)
from engine.logic.runtime import LogicGraphRuntime

REPO_ROOT = Path(__file__).resolve().parents[3]


def _shipping_graphs() -> list[Path]:
    return sorted(
        path
        for path in REPO_ROOT.rglob("*.zlogic")
        if ".git" not in path.parts and "node_modules" not in path.parts
    )


SHIPPING_GRAPHS = _shipping_graphs()


def test_the_repository_still_ships_graphs():
    assert SHIPPING_GRAPHS, "no .zlogic assets found; the sweep below would be vacuous"


ORPHAN_BASELINE = json.loads(
    (REPO_ROOT / "tests" / "fixtures" / "stage2" / "orphan_edge_baseline.json").read_text(
        encoding="utf-8"
    )
)


def _orphan_edges(graph: dict) -> list[str]:
    """Edges naming a port that the node's contract does not declare."""
    nodes = {str(node["id"]): node for node in graph.get("nodes", [])}
    orphans: list[str] = []
    for edge in graph.get("edges", []):
        source = nodes.get(str(edge.get("from_node") or edge.get("source") or ""))
        target = nodes.get(str(edge.get("to_node") or edge.get("target") or ""))
        from_port = str(edge.get("from_port") or edge.get("source_port") or "")
        to_port = str(edge.get("to_port") or edge.get("target_port") or "")
        if source is not None and from_port:
            outputs = {name for name, _kind in node_port_definitions(source)["outputs"]}
            if from_port not in outputs:
                orphans.append(f"{source.get('type')}.{from_port}>out")
        if target is not None and to_port:
            inputs = {name for name, _kind in node_port_definitions(target)["inputs"]}
            if to_port not in inputs:
                orphans.append(f"{target.get('type')}.{to_port}>in")
    return sorted(set(orphans))


@pytest.mark.parametrize("path", SHIPPING_GRAPHS, ids=lambda p: p.stem)
def test_graph_loads_normalizes_and_builds_a_runtime(path: Path):
    graph = load_logic_graph(path)
    assert graph["format"] == "zennity.logic_graph"

    normalized = normalize_logic_graph(graph)
    assert normalize_logic_graph(normalized) == normalized, "normalize is not idempotent"

    runtime = LogicGraphRuntime(normalized)
    assert runtime.graph["nodes"] is not None


@pytest.mark.parametrize(
    "path", SHIPPING_GRAPHS, ids=lambda p: p.relative_to(REPO_ROOT).as_posix()
)
def test_graph_introduces_no_new_orphan_edges(path: Path):
    """No edge may lose its port because the schema is now derived.

    11 assets already carried orphan edges before Stage 2 -- graphs saved
    against node types that no longer exist.  Fixing those is asset work, not
    node-system work, so they are pinned to a recorded baseline: this test fails
    on any *new* orphan, and also on an orphan that silently disappears, since
    both mean the port contract moved.
    """
    # PHASE 9 recovery item 4.2: keyed by repo-relative path, not file name.
    # Three different assets are called PlayerMovement.zlogic, so a name key
    # made all three read the same recorded list -- invisible while they all had
    # zero orphans, wrong the moment one of them differed.
    key = path.relative_to(REPO_ROOT).as_posix()
    recorded = set(ORPHAN_BASELINE["orphan_edges_by_asset"].get(key, []))
    actual = set(_orphan_edges(normalize_logic_graph(load_logic_graph(path))))
    assert actual == recorded, (
        f"{path.name} orphan edges changed\n"
        f"  new:       {sorted(actual - recorded)}\n"
        f"  no longer: {sorted(recorded - actual)}"
    )


def test_the_orphan_edge_baseline_did_not_grow():
    total = sum(
        len(_orphan_edges(normalize_logic_graph(load_logic_graph(path))))
        for path in SHIPPING_GRAPHS
    )
    assert total == ORPHAN_BASELINE["total_orphan_edges"]


def test_round_trip_through_save_preserves_the_graph(tmp_path: Path):
    for path in SHIPPING_GRAPHS:
        original = normalize_logic_graph(load_logic_graph(path))
        destination = tmp_path / path.name
        save_logic_graph(destination, original)
        assert normalize_logic_graph(load_logic_graph(destination)) == original, path.name


# ---------------------------------------------------------------------------
# Golden graph authored with the current palette
# ---------------------------------------------------------------------------

GOLDEN_GRAPH = {
    "format": "zennity.logic_graph",
    "version": 1,
    "name": "Stage2Golden",
    "target": {"type": "name", "value": "Player"},
    "nodes": [
        {"id": "n_event", "type": "event_update", "position": [0.0, 0.0]},
        {"id": "n_axis", "type": "input_axis", "position": [240.0, 0.0],
         "properties": {"axis": "horizontal"}},
        {"id": "n_move", "type": "move_by", "position": [480.0, 0.0],
         "properties": {"x": 0.0, "y": 0.0}},
    ],
    "edges": [
        {"from_node": "n_event", "from_port": "next", "to_node": "n_axis", "to_port": "in"},
        {"from_node": "n_axis", "from_port": "next", "to_node": "n_move", "to_port": "in"},
        {"from_node": "n_axis", "from_port": "value", "to_node": "n_move", "to_port": "x"},
    ],
}


def test_golden_graph_ports_exist_in_the_derived_schema():
    """event_update -> input_axis -> move_by, wired with current-palette pins."""
    for node in GOLDEN_GRAPH["nodes"]:
        ports = node_port_definitions(node)
        assert ports["inputs"] or ports["outputs"], node["type"]
    assert not _orphan_edges(normalize_logic_graph(GOLDEN_GRAPH))


def test_golden_graph_saves_loads_and_executes(tmp_path: Path):
    destination = tmp_path / "Stage2Golden.zlogic"
    save_logic_graph(destination, GOLDEN_GRAPH)
    reloaded = load_logic_graph(destination)
    assert not _orphan_edges(normalize_logic_graph(reloaded))

    runtime = LogicGraphRuntime(reloaded)

    class _Game:
        """Minimal host, and its own move target.

        ``_read_target`` falls back to the game object when a node has no
        ``target`` edge, so the game is what ``move_by`` writes to.  Everything
        is declared explicitly rather than through ``__getattr__``: a catch-all
        would make ``rigidbody`` truthy and send the executor down a branch the
        graph never asks for.
        """

        def __init__(self):
            self.x = 0.0
            self.y = 0.0
            self.rigidbody = None
            self.components: list = []
            self.moved: list[tuple[float, float]] = []

        def axis(self, negative, positive):
            return 1.0

        def move(self, delta_x, delta_y):
            self.moved.append((delta_x, delta_y))
            self.x += delta_x
            self.y += delta_y

    game = _Game()
    # One tick must run the whole chain: the event fires, the axis evaluates to
    # a number, and move_by consumes it.  Dispatching at all is what Stage 2
    # unified, and the moved target is the proof the data edge resolved too.
    runtime.update(game, 1.0 / 60.0)
    assert game.moved, "move_by never ran"
    assert game.x != 0.0, "move_by did not consume the input_axis value"
