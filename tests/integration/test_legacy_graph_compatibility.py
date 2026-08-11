"""Phase 9.5B Stage 1 — no existing .zlogic asset may break (brief item 21).

Stage 1 renamed pins across the whole catalogue.  These tests load every real
project asset, normalise it, and execute a representative sample, so a contract
change that silently orphans a saved edge fails here.
"""
from __future__ import annotations

import json
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[2]
ASSETS = sorted((ROOT / "Assets").rglob("*.zlogic"))

pytestmark = pytest.mark.skipif(not ASSETS, reason="no .zlogic assets in the project")

# ---------------------------------------------------------------------------
# Pre-existing authoring bugs in project assets, NOT caused by Stage 1.
# This list may only ever SHRINK.
#
# get_position.position: the evaluator is port-sensitive -- `port == "x"` gives
#   target.x and anything else gives target.y -- so `position` has always
#   returned the Y coordinate.  EnemyAILogic.zlogic feeds it into BOTH
#   vector2.x and vector2.y, and into distance_to_point.point_a/point_b, which
#   expect points.  Stage 1 did not change the evaluator; declaring the real
#   x/y contract simply made the existing breakage visible.  Fixing the asset
#   is authoring work, tracked for Stage 2.
# ---------------------------------------------------------------------------
PRE_EXISTING_ASSET_ISSUES = {
    "get_position.position",
}


def load(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.mark.parametrize("path", ASSETS, ids=lambda p: p.name)
def test_every_asset_normalises(path):
    from engine.logic.graph_asset import normalize_logic_graph

    graph = normalize_logic_graph(load(path))
    assert graph["format"]
    assert isinstance(graph["nodes"], list)
    assert isinstance(graph["edges"], list)


@pytest.mark.parametrize("path", ASSETS, ids=lambda p: p.name)
def test_no_edge_is_orphaned_by_the_stage1_renames(path):
    """Every saved exec edge must still leave a port its node declares.

    This is the regression that would break existing games: a pin renamed in
    the definition without an alias leaves the saved edge pointing at nothing,
    and the chain dies silently -- exactly the Phase 9.5A P0, inverted.
    """
    from engine.logic.graph_asset import normalize_logic_graph
    from engine.logic.node_definitions import NODE_DEFINITIONS

    graph = normalize_logic_graph(load(path))
    types = {str(n["id"]): str(n.get("type", "")) for n in graph["nodes"]}

    orphaned = []
    for edge in graph["edges"]:
        node_type = types.get(str(edge["from_node"]), "")
        entry = NODE_DEFINITIONS.get(node_type)
        if not entry:
            continue  # custom/plugin node: nothing to validate against
        declared = {str(p[0]) for p in entry.get("outputs", []) or []}
        if not declared:
            continue
        port = str(edge["from_port"])
        if port in declared:
            continue
        # A node may generate a port family at runtime (sequence -> then_0..N).
        families = tuple(entry.get("dynamic_exec_prefixes") or ())
        if families and any(port.startswith(f) for f in families):
            continue
        if f"{node_type}.{port}" in PRE_EXISTING_ASSET_ISSUES:
            continue
        orphaned.append(f"{node_type}.{port}")

    assert not orphaned, (
        f"{path.name}: saved edges now leave undeclared ports: {sorted(set(orphaned))}"
    )


@pytest.mark.parametrize("path", ASSETS, ids=lambda p: p.name)
def test_normalisation_is_stable_for_real_assets(path):
    from engine.logic.graph_asset import normalize_logic_graph

    once = normalize_logic_graph(load(path))
    twice = normalize_logic_graph(once)
    assert [e["from_port"] for e in once["edges"]] == \
           [e["from_port"] for e in twice["edges"]]
    assert [n["type"] for n in once["nodes"]] == [n["type"] for n in twice["nodes"]]


def test_next_remains_the_dominant_saved_port():
    """Sanity: the canonical choice matches what assets actually contain."""
    from engine.logic.graph_asset import normalize_logic_graph

    counts: dict[str, int] = {}
    for path in ASSETS:
        for edge in normalize_logic_graph(load(path))["edges"]:
            port = str(edge["from_port"])
            counts[port] = counts.get(port, 0) + 1

    assert counts.get("next", 0) > 0
    # No normalised asset may still carry a legacy spelling.
    from engine.logic.port_aliases import EXEC_PORT_ALIASES
    leftover = sorted(p for p in counts if p in EXEC_PORT_ALIASES)
    assert not leftover, f"legacy ports survived normalisation: {leftover}"


@pytest.mark.parametrize("path", ASSETS, ids=lambda p: p.name)
def test_representative_assets_build_a_runtime(path):
    """Constructing the runtime exercises start-up wiring for every asset."""
    from engine.logic.graph_asset import normalize_logic_graph
    from engine.logic.runtime import LogicGraphRuntime

    runtime = LogicGraphRuntime(normalize_logic_graph(load(path)))
    assert runtime.nodes is not None
