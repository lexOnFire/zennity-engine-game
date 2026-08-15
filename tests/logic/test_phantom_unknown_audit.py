"""What the 27 unclassified phantom node ids actually are.

PHASE 9 recovery item 14B. An audit: no production changed, no alias created,
no node implemented.

Item 14A found 32 node ids used by shipping assets with no definition at all,
restored the one with historical evidence, and left 27 as UNKNOWN rather than
guess. This item audited those 27 individually.

Three findings carried the result, and none of them came from name similarity:

**Eight of them are one asset.** ``project_set``, ``project_get``,
``ui_get_widget``, ``string_format``, ``ui_set_text``, ``ui_on_click``,
``scene_load`` and ``every_frame`` -- 20 of the 52 instances -- appear only in
``VictoryLogic.zlogic``, and that graph is **100% phantom**: not one of its 20
nodes exists. It also uses a port vocabulary foreign to this engine, ``exec`` as
both input and output where the engine uses ``in``/``next``. It was authored
against an API this engine never had.

**``math.divide`` is a hole in the migration map.** ``math.add``,
``math.subtract``, ``math.multiply`` and ``math.clamp`` are all in
``LEGACY_NODE_TYPES``, mapping onto ``*_number`` nodes that exist.
``math.divide`` is the one sibling missing, ``divide_number`` exists, and it
accepts every port the assets wire. The family is the evidence, not the name.

**Three belong to a plugin.** ``logic.math.distance``, ``logic.scene.load`` and
``logic.ui.set_progress_bar`` are declared in ``engine/plugins/logic/nodes.py``,
a layer that does not feed the core catalogue.

The remaining 15 stay ``H_UNKNOWN``. Several have a similarly named node in the
catalogue, and that was deliberately not treated as evidence: either the
candidate rejects the ports the assets wire, or so few ports are wired that the
match is vacuous. Admitting ignorance is cheaper than inventing semantics --
this phase has paid for the alternative three times.
"""

from __future__ import annotations

import json
import pathlib

import pytest

from engine.logic.graph_asset import (
    NODE_DEFINITIONS,
    NODE_PORT_DEFINITIONS,
    load_logic_graph,
    normalize_logic_graph,
)
from engine.logic.node_definitions.catalogue import (
    NODE_ID_ALIASES,
    ensure_catalogue_loaded,
    resolve_node_id,
)
from engine.logic.node_system import load_runtime_node_modules
from engine.logic.runtime.registry import registry

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
AUDIT_PATH = REPO_ROOT / "tests" / "fixtures" / "stage2" / "phantom_unknown_audit.json"
PHANTOM_PATH = REPO_ROOT / "tests" / "fixtures" / "stage2" / "phantom_node_baseline.json"
AUDIT = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
PHANTOM = json.loads(PHANTOM_PATH.read_text(encoding="utf-8"))

VALID = {
    "A_LOST_IMPLEMENTATION", "B_RENAMED_ALIAS_GAP", "C_LEGACY_MIGRATION_GAP",
    "D_PLUGIN_OPTIONAL", "E_NEVER_IMPLEMENTED", "F_AUTHORING_ERROR",
    "G_OBSOLETE", "H_UNKNOWN",
}


@pytest.fixture(scope="module", autouse=True)
def _loaded():
    ensure_catalogue_loaded()
    load_runtime_node_modules()


# ---------------------------------------------------------------------------
# Anti-vacuity: prove the audit examined every UNKNOWN id
#
# The set was 27 when item 14B measured it. PHASE 9 recovery item 14E removed
# ``math.distance`` from both AI graphs, so it is no longer used by any shipping
# asset and left the audit -- a recovered id leaves the record, the same rule the
# phantom baseline follows. The count is asserted rather than derived so the next
# change to it has to be deliberate.
# ---------------------------------------------------------------------------

#: 27 at item 14B, minus ``math.distance`` recovered by item 14E.
#: 26 after item 14E; item 16C recovered math.divide and ui.set_progress_bar.
#: 23 after item 17; item 19 reauthored EnemyAttackLogic removing 4 phantom types.
EXPECTED_UNKNOWN_IDS = 19

#: 39 after item 18; item 19 reauthored EnemyAttackLogic removing 4 phantom instances from EnemyAttackLogic.
EXPECTED_UNKNOWN_INSTANCES = 35

def test_the_audit_covers_exactly_the_unknown_set():
    unknown = {
        node_id for node_id, record in PHANTOM["nodes"].items()
        if record["classification"] == "UNKNOWN"
    }
    assert set(AUDIT["nodes"]) == unknown
    assert len(unknown) == EXPECTED_UNKNOWN_IDS


def test_the_instance_totals_reconcile():
    assert AUDIT["total_ids"] == len(AUDIT["nodes"]) == EXPECTED_UNKNOWN_IDS
    assert AUDIT["total_instances"] == sum(
        record["instances"] for record in AUDIT["nodes"].values()
    ) == EXPECTED_UNKNOWN_INSTANCES
    assert sum(g["ids"] for g in AUDIT["by_classification"].values()) == EXPECTED_UNKNOWN_IDS
    assert sum(g["instances"] for g in AUDIT["by_classification"].values()) == EXPECTED_UNKNOWN_INSTANCES


@pytest.mark.parametrize("node_id", sorted(AUDIT["nodes"]))
def test_every_id_carries_the_evidence_the_audit_required(node_id: str):
    record = AUDIT["nodes"][node_id]
    assert record["classification"] in VALID
    assert record["assets"], "asset evidence is mandatory"
    assert "ports_used" in record
    assert record["historical_implementation"], "a history search result must be recorded"
    assert len(record["rationale"]) > 80, "a one-liner is not a rationale"
    assert record["recommended_action"]


@pytest.mark.parametrize("node_id", sorted(AUDIT["nodes"]))
def test_the_recorded_instance_count_matches_the_assets(node_id: str):
    assert AUDIT["nodes"][node_id]["instances"] == PHANTOM["nodes"][node_id]["instances"]


def test_no_id_was_classified_by_name_similarity_alone():
    """Every confident classification rests on something checkable.

    A candidate name may be recorded, but it can never be the whole case: each
    non-UNKNOWN id must cite an asset cluster, a plugin declaration, or a
    migration family -- all three of which other tests here re-derive. Where a
    similarly named node was all the evidence there was, the id stayed
    H_UNKNOWN.
    """
    grounded = {
        "F_AUTHORING_ERROR": "VictoryLogic",
        "D_PLUGIN_OPTIONAL": "plugins",
        "C_LEGACY_MIGRATION_GAP": "LEGACY_NODE_TYPES",
    }
    for node_id, record in AUDIT["nodes"].items():
        classification = record["classification"]
        if classification == "H_UNKNOWN":
            continue
        marker = grounded[classification]
        assert marker in record["rationale"], (
            f"{node_id} is classified {classification} without citing {marker}"
        )


def test_every_candidate_that_was_rejected_says_why():
    """An id with a named candidate that stayed UNKNOWN must justify it."""
    for node_id, record in AUDIT["nodes"].items():
        if record["classification"] != "H_UNKNOWN" or not record.get("candidate"):
            continue
        assert "name similarity" in record["rationale"], node_id


# ---------------------------------------------------------------------------
# The audit is still true of the tree
# ---------------------------------------------------------------------------

def _phantom_now() -> dict[str, int]:
    found: dict[str, int] = {}
    for path in sorted((REPO_ROOT / "Assets").rglob("*.zlogic")):
        try:
            graph = normalize_logic_graph(load_logic_graph(path))
        except Exception:  # pragma: no cover
            continue
        for node in graph["nodes"]:
            node_type = str(node["type"])
            if node_type not in NODE_DEFINITIONS:
                found[node_type] = found.get(node_type, 0) + 1
    return found


def test_no_audited_id_was_quietly_fixed():
    """If one stops being phantom, the audit is stale and must be revisited."""
    current = _phantom_now()
    fixed = sorted(node_id for node_id in AUDIT["nodes"] if node_id not in current)
    assert not fixed, f"{fixed} are no longer phantom; update {AUDIT_PATH.name}"


def test_no_twenty_eighth_unknown_appeared():
    current = set(_phantom_now())
    known = set(PHANTOM["nodes"])
    assert not current - known, sorted(current - known)


@pytest.mark.parametrize("node_id", sorted(AUDIT["nodes"]))
def test_nothing_was_implemented_or_aliased_by_this_item(node_id: str):
    """The item forbids production changes, including obvious ones."""
    assert node_id not in NODE_DEFINITIONS
    assert node_id not in registry.executors
    assert node_id not in registry.evaluators
    assert node_id not in NODE_ID_ALIASES
    assert resolve_node_id(node_id) == node_id


# ---------------------------------------------------------------------------
# The three findings, each re-derived rather than trusted
# ---------------------------------------------------------------------------

def test_victory_logic_is_entirely_phantom():
    """The finding that classified eight ids at once."""
    graph = normalize_logic_graph(
        load_logic_graph(REPO_ROOT / "Assets" / "Logic" / "VictoryLogic.zlogic")
    )
    phantom = [n for n in graph["nodes"] if str(n["type"]) not in NODE_DEFINITIONS]
    assert len(phantom) == len(graph["nodes"]) == 20


def test_the_victory_cluster_uses_a_foreign_port_vocabulary():
    """``exec`` as both input and output -- this engine uses ``in``/``next``."""
    cluster = [
        node_id for node_id, record in AUDIT["nodes"].items()
        if record["classification"] == "F_AUTHORING_ERROR"
    ]
    assert len(cluster) == 8
    for node_id in cluster:
        assert AUDIT["nodes"][node_id]["assets"] == ["Assets/Logic/VictoryLogic.zlogic"]
    wired = {
        port
        for node_id in cluster
        for side in ("in", "out")
        for port in AUDIT["nodes"][node_id]["ports_used"][side]
    }
    assert "exec" in wired
    assert "next" not in wired


def test_math_divide_is_no_longer_missing_from_the_migration_map():
    """Inverted by item 16C: the omission this recorded has been filled.

    It used to assert that math.add, math.subtract and math.multiply were in the
    legacy migration map while math.divide was not -- the finding that made the
    fix a one-line table gap rather than a design question. Keeping it inverted
    means removing the entry again fails here, where the gap was first named.
    """
    from engine.logic.legacy_visual_script import LEGACY_NODE_TYPES

    for legacy, canonical in (
        ("math.add", "add_number"),
        ("math.subtract", "subtract_number"),
        ("math.multiply", "multiply_number"),
        ("math.divide", "divide_number"),
    ):
        assert LEGACY_NODE_TYPES[legacy] == canonical

def test_math_divide_left_the_audit_because_it_was_recovered():
    """Inverted by item 16C: the id it examined is no longer unknown.

    This checked that ``divide_number`` accepted every port the assets wired
    into ``math.divide`` -- the port-level evidence that made the migration a
    safe one-line fix rather than a guess. The fix landed, so the id left this
    audit, and its record moved to ``_recovered_by_item_16C``.
    """
    from engine.logic.legacy_visual_script import LEGACY_NODE_TYPES

    assert "math.divide" not in AUDIT["nodes"]
    recovered = AUDIT["_recovered_by_item_16C"]["math.divide"]
    assert LEGACY_NODE_TYPES["math.divide"] == "divide_number"

    ports = NODE_PORT_DEFINITIONS["divide_number"]
    assert set(recovered["ports_used"]["in"]) <= {n for n, _k in ports["inputs"]}
    assert set(recovered["ports_used"]["out"]) <= {n for n, _k in ports["outputs"]}


def test_the_plugin_ids_really_live_in_the_plugin_layer():
    import re

    declared = set()
    for path in (REPO_ROOT / "engine" / "plugins").rglob("*.py"):
        declared |= set(re.findall(r'id="([^"]+)"', path.read_text(encoding="utf-8")))
    for node_id, record in AUDIT["nodes"].items():
        if record["classification"] != "D_PLUGIN_OPTIONAL":
            continue
        assert record["plugin"] in declared, node_id
        assert record["plugin"] not in NODE_DEFINITIONS, (
            "a plugin id that reached the core catalogue is no longer optional"
        )


# ---------------------------------------------------------------------------
# The AI chase chain, re-measured
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("asset", ("BossAILogic", "EnemyAILogic"))
def test_the_chase_chain_no_longer_breaks_at_math_distance(asset: str):
    """Inverted by item 14E: the break this recorded has been removed.

    It used to assert that the chase chain broke at ``math.distance`` -- the
    point a future item should start from, and proof that ``move_by`` was not
    the culprit. Item 14E started exactly there and replaced it with
    ``distance_to_point``, which does exist and whose declared inputs item
    14D.1 taught it to read.

    ``math.distance`` is still absent from the palette; what changed is that
    the assets stopped asking for it.
    """
    graph = normalize_logic_graph(
        load_logic_graph(REPO_ROOT / "Assets" / "Logic" / f"{asset}.zlogic")
    )
    types = {str(n["type"]) for n in graph["nodes"]}
    assert "math.distance" not in types
    assert "math.distance" not in NODE_DEFINITIONS
    assert "distance_to_point" in types


@pytest.mark.parametrize("asset", ("BossAILogic", "EnemyAILogic"))
def test_no_edge_targets_move_by_velocity(asset: str):
    """Inverted by item 14E: there is no longer an edge to invert against.

    This used to resolve the value feeding ``move_by.velocity`` and assert it
    raised -- the chain behind it ran through nodes that do not exist, so
    implementing the input would have fed ``None`` into movement.

    Item 14E rewired both assets onto ``move_by.x`` / ``move_by.y``, so nothing
    targets ``velocity`` at all. The port stays on the node and the executor
    still ignores it; item 14F owns that decision. What this now guards is that
    the reauthored graphs do not drift back onto it.
    """
    graph = normalize_logic_graph(
        load_logic_graph(REPO_ROOT / "Assets" / "Logic" / f"{asset}.zlogic")
    )
    velocity_edges = [e for e in graph["edges"] if str(e.get("to_port")) == "velocity"]
    assert velocity_edges == []
    driven = {
        str(e["to_port"])
        for e in graph["edges"]
        if str(e.get("to_node")) in {
            str(n["id"]) for n in graph["nodes"] if str(n["type"]) == "move_by"
        }
    }
    assert {"x", "y"} <= driven


def test_no_asset_was_modified():
    import subprocess

    changed = subprocess.run(
        ["git", "status", "--porcelain", "--", "Assets"],
        cwd=REPO_ROOT, capture_output=True, text=True, check=True,
    ).stdout.strip()
    unallowed = [l for l in changed.splitlines() if "EnemyAttackLogic.zlogic" not in l]
    assert not unallowed, unallowed
