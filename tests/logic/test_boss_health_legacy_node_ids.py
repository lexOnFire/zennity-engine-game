"""Two legacy node ids resolve now, and BossHealthLogic is clean.

PHASE 9 recovery item 16C. Item 16A's RC-04 and RC-05 were the smallest defects
in the whole orphan audit, and both were omissions rather than gaps in
capability:

* ``math.add``, ``math.subtract``, ``math.multiply`` and ``math.clamp`` were all
  in the legacy migration map. ``math.divide`` was not -- while
  ``divide_number`` exists, declares the same ``a``/``b`` -> ``value`` contract
  as its siblings, and shares their evaluator.
* ``ui.update_progress`` already mapped onto ``set_ui_progress_bar``, so the
  canonical target for the legacy ``ui.*`` progress bar was established. The two
  health graphs simply spell it ``ui.set_progress_bar``.

Both fixes are one line each in the migration map. No node was created, no
executor changed, and **no asset was edited** -- which is the point: the graphs
were authored correctly against a family whose map had a hole in it.
"""

from __future__ import annotations

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
from engine.logic.legacy_visual_script import LEGACY_NODE_TYPES
from engine.logic.node_definitions.catalogue import resolve_node_id
from engine.logic.runtime.registry import registry

REPO_ROOT = Path(__file__).resolve().parents[2]
#: Both graphs author both spellings; neither was touched by this item.
USERS = ("BossHealthLogic", "PlayerHealthLogic")


def graph(name: str) -> dict:
    return normalize_logic_graph(load_logic_graph(REPO_ROOT / "Assets" / "Logic" / f"{name}.zlogic"))


def _orphans(g: dict) -> list[str]:
    nodes = {str(n["id"]): n for n in g["nodes"]}
    out = []
    for edge in g["edges"]:
        s, t = nodes.get(str(edge.get("from_node") or "")), nodes.get(str(edge.get("to_node") or ""))
        if s is None or t is None:
            continue
        fp, tp = str(edge.get("from_port") or ""), str(edge.get("to_port") or "")
        if fp and fp not in {n for n, _k in node_port_definitions(s)["outputs"]}:
            out.append(f"{s['type']}.{fp}>out")
        if tp and tp not in {n for n, _k in node_port_definitions(t)["inputs"]}:
            out.append(f"{t['type']}.{tp}>in")
    return sorted(set(out))


# ---------------------------------------------------------------------------
# math.divide
# ---------------------------------------------------------------------------


def test_math_divide_migrates_like_its_siblings():
    """The evidence for the fix is the family, not the name.

    Three siblings mapped and one did not. Asserting all four together is what
    keeps this a rule rather than a special case.
    """
    assert LEGACY_NODE_TYPES["math.add"] == "add_number"
    assert LEGACY_NODE_TYPES["math.subtract"] == "subtract_number"
    assert LEGACY_NODE_TYPES["math.multiply"] == "multiply_number"
    assert LEGACY_NODE_TYPES["math.divide"] == "divide_number"


def test_divide_number_has_the_same_contract_as_its_siblings():
    divide = NODE_PORT_DEFINITIONS["divide_number"]
    for sibling in ("subtract_number", "multiply_number"):
        assert NODE_PORT_DEFINITIONS[sibling] == divide, sibling


def test_the_canonical_target_exists_and_computes():
    assert "divide_number" in NODE_DEFINITIONS
    assert "divide_number" in registry.evaluators

    class _Runtime:
        values: dict = {}

        def _read_input(self, node_id, port, default, game, dt, branch):
            return default

    node = {"id": "n", "type": "divide_number", "properties": {"a": 10.0, "b": 4.0}}
    assert registry.evaluators["divide_number"](
        _Runtime(), "n", "value", node, object(), 1 / 60, set()
    ) == pytest.approx(2.5)


def test_a_zero_divisor_keeps_the_runtime_s_existing_semantics():
    """Not changed here: the evaluator already raises, and it still does.

    Recorded so "fix the migration" cannot quietly become "change what division
    by zero means".
    """
    class _Runtime:
        values: dict = {}

        def _read_input(self, node_id, port, default, game, dt, branch):
            return default

    node = {"id": "n", "type": "divide_number", "properties": {"a": 1.0, "b": 0.0}}
    with pytest.raises(RuntimeError):
        registry.evaluators["divide_number"](
            _Runtime(), "n", "value", node, object(), 1 / 60, set()
        )


# ---------------------------------------------------------------------------
# ui.set_progress_bar
# ---------------------------------------------------------------------------


def test_both_legacy_progress_bar_spellings_reach_the_same_node():
    assert LEGACY_NODE_TYPES["ui.update_progress"] == "set_ui_progress_bar"
    assert LEGACY_NODE_TYPES["ui.set_progress_bar"] == "set_ui_progress_bar"


def test_the_progress_bar_target_exists_with_the_port_the_assets_use():
    assert "set_ui_progress_bar" in NODE_DEFINITIONS
    assert "set_ui_progress_bar" in registry.executors
    inputs = {n for n, _k in NODE_PORT_DEFINITIONS["set_ui_progress_bar"]["inputs"]}
    assert "value" in inputs, "the health graphs wire the percentage into value"


# ---------------------------------------------------------------------------
# No alias cycles, no palette duplicates
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("legacy", ["math.divide", "ui.set_progress_bar"])
def test_the_legacy_spelling_does_not_enter_the_palette(legacy: str):
    """A migration entry must not become a second node id."""
    assert legacy not in NODE_DEFINITIONS
    assert legacy not in NODE_PORT_DEFINITIONS


def test_no_migration_entry_points_at_another_migration_entry():
    """A map whose targets are themselves legacy ids would never settle."""
    for legacy, canonical in LEGACY_NODE_TYPES.items():
        assert canonical not in LEGACY_NODE_TYPES, f"{legacy} -> {canonical} -> ..."
        assert canonical in NODE_DEFINITIONS or canonical in NODE_PORT_DEFINITIONS, (
            f"{legacy} migrates to {canonical}, which does not exist"
        )


# ---------------------------------------------------------------------------
# The assets, which were not edited
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("name", USERS)
def test_neither_spelling_survives_normalization(name: str):
    types = {str(n["type"]) for n in graph(name)["nodes"]}
    assert "math.divide" not in types
    assert "ui.set_progress_bar" not in types
    assert {"divide_number", "set_ui_progress_bar"} <= types


def test_the_boss_percentage_chain_resolves_end_to_end():
    """health / max_health into the progress bar, every port declared."""
    g = graph("BossHealthLogic")
    nodes = {str(n["id"]): n for n in g["nodes"]}
    divide = [i for i, n in nodes.items() if str(n["type"]) == "divide_number"]
    assert len(divide) == 1

    wired = {str(e["to_port"]) for e in g["edges"] if str(e.get("to_node")) in divide}
    assert wired == {"a", "b"}, "both operands arrive on edges"
    consumers = [str(e["to_node"]) for e in g["edges"] if str(e.get("from_node")) in divide]
    assert consumers and nodes[consumers[0]]["type"] == "set_ui_progress_bar"


def test_the_player_divide_node_is_disconnected_and_that_is_recorded():
    """A finding, not something this item fixes.

    ``PlayerHealthLogic`` carries a ``divide_number`` with no edges at all and
    ``a``/``b`` both defaulting to 0.0. Migrating the id made the node real, so
    it is worth stating plainly that it is still wired to nothing: it never
    evaluates, so the zero divisor never raises, and no orphan edge is involved
    because there is no edge. Fixing it would be authoring, not migration.
    """
    g = graph("PlayerHealthLogic")
    nodes = {str(n["id"]): n for n in g["nodes"]}
    divide = [i for i, n in nodes.items() if str(n["type"]) == "divide_number"]
    assert len(divide) == 1

    touching = [
        e for e in g["edges"]
        if str(e.get("to_node")) in divide or str(e.get("from_node")) in divide
    ]
    assert touching == [], "the node gained wiring; update this record"
    assert nodes[divide[0]]["properties"]["a"] == 0.0
    assert nodes[divide[0]]["properties"]["b"] == 0.0


def test_boss_health_has_no_orphan_edge_left():
    """RC-04 and RC-05 were its entire orphan debt."""
    assert _orphans(graph("BossHealthLogic")) == []


def test_boss_health_still_carries_its_unrelated_phantom_debt():
    """Phantom nodes whose edges resolve: out of scope, and still recorded."""
    g = graph("BossHealthLogic")
    phantom = {str(n["type"]) for n in g["nodes"] if resolve_node_id(str(n["type"])) not in NODE_DEFINITIONS}
    # Item 17 recovered animator.set_trigger, so it left this set. The other
    # two stay: neither has a definition anywhere in history.
    assert phantom == {"component.set_property", "scene.load"}


@pytest.mark.parametrize("name", USERS)
def test_save_and_reopen_does_not_reintroduce_the_legacy_ids(name: str, tmp_path):
    original = graph(name)
    destination = tmp_path / f"{name}.zlogic"
    save_logic_graph(destination, original)
    reloaded = normalize_logic_graph(load_logic_graph(destination))

    assert reloaded == original
    types = {str(n["type"]) for n in reloaded["nodes"]}
    assert "math.divide" not in types and "ui.set_progress_bar" not in types


def test_the_assets_on_disk_were_not_edited():
    """The whole point: the graphs were right, the migration map had a hole."""
    import json

    for name in USERS:
        raw = json.loads((REPO_ROOT / "Assets" / "Logic" / f"{name}.zlogic").read_text(encoding="utf-8"))
        types = {str(n.get("type")) for n in raw.get("nodes", [])}
        assert "math.divide" in types, "the legacy spelling must still be on disk"
        assert "ui.set_progress_bar" in types
