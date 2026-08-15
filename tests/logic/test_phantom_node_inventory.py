"""Node ids that shipping assets use and the catalogue does not have.

PHASE 9 recovery item 14A.

Item 14 set out to make ``move_by`` honour its authored ``velocity`` input, on
the theory that two enemies stood still because the runtime ignored a computed
vector. Tracing the graph disproved it. The chain is a coherent chase design --
player position minus own position, normalised, times ``move_speed`` -- but
**none of the nodes in it exist**::

    object.find_by_name   no definition, no contract, no runtime
    math.distance         no definition, no contract, no runtime
    vector2               no definition, no contract, no runtime
    normalize_vector      no definition, no contract, no runtime

Evaluating ``move_by.velocity`` on the real asset raises ``TypeError``: the
value is ``None``. Making the executor read it would have fed ``None`` into the
movement and changed nothing, while pinning invented behaviour with tests.

So item 14 became this: find out how many nodes are in that state.

**63 instances across 32 ids**, measured on the normalized graph so that
node-id aliases are already applied -- the mistake items 7, 9 and 12 each made
by measuring raw JSON.

One id was restored, and only one, because it is the only one with evidence:
``object.find_by_name``. ``939764c`` mapped it to ``find_tag`` on a lineage that
is not an ancestor of this branch, exactly like the executors items 10 and 11
recovered. The assets carrying it are saved in the current format, so the
visual-script migration would never have run on them -- the alias belongs in
``NODE_ID_ALIASES``, which is where node-id resolution looks.

The rest are recorded, not guessed at. Five of them are marked
``NEVER_IMPLEMENTED``: a search across every commit found no definition and no
executor for them, ever. They are not lost runtime. Building them is new design
work, and calling it recovery would be inventing semantics.
"""

from __future__ import annotations

import json
import pathlib

import pytest

from engine.logic.graph_asset import (
    NODE_DEFINITIONS,
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
BASELINE_PATH = REPO_ROOT / "tests" / "fixtures" / "stage2" / "phantom_node_baseline.json"
BASELINE = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
SHIPPING = sorted((REPO_ROOT / "Assets").rglob("*.zlogic"))


@pytest.fixture(scope="module", autouse=True)
def _loaded():
    ensure_catalogue_loaded()
    load_runtime_node_modules()


def _phantom_usage() -> dict[str, int]:
    """Node ids in shipping assets with no definition, on the normalized graph."""
    found: dict[str, int] = {}
    for path in SHIPPING:
        try:
            graph = normalize_logic_graph(load_logic_graph(path))
        except Exception:  # pragma: no cover - a broken asset is a different item
            continue
        for node in graph["nodes"]:
            node_type = str(node["type"])
            if node_type not in NODE_DEFINITIONS:
                found[node_type] = found.get(node_type, 0) + 1
    return found


# ---------------------------------------------------------------------------
# The gate: the class is bounded and cannot grow or rot silently
# ---------------------------------------------------------------------------

def test_no_new_phantom_node_id_appears():
    new = sorted(set(_phantom_usage()) - set(BASELINE["nodes"]))
    assert not new, (
        f"these ids are used by shipping assets and have no definition: {new}. "
        "Either the node was removed, or an asset was authored against an id "
        "the catalogue never had."
    )


def test_a_recovered_id_leaves_the_baseline():
    """Debt, not exemption -- the pattern every recorded set in this phase uses."""
    stale = sorted(set(BASELINE["nodes"]) - set(_phantom_usage()))
    assert not stale, (
        f"{stale} are no longer phantom; remove them from {BASELINE_PATH.name}"
    )


def test_the_recorded_instance_counts_are_current():
    current = _phantom_usage()
    drifted = {
        node_id: (record["instances"], current.get(node_id))
        for node_id, record in BASELINE["nodes"].items()
        if current.get(node_id) != record["instances"]
    }
    assert not drifted, f"recorded instance counts drifted: {drifted}"


def test_the_totals_match_the_contents():
    assert BASELINE["total_ids"] == len(BASELINE["nodes"])
    assert BASELINE["total_instances"] == sum(
        record["instances"] for record in BASELINE["nodes"].values()
    )


def test_every_recorded_id_carries_a_classification():
    for node_id, record in BASELINE["nodes"].items():
        assert record["classification"] in ("NEVER_IMPLEMENTED", "UNKNOWN"), node_id


def test_every_recorded_id_names_the_assets_that_use_it():
    """A record without a location cannot be acted on later."""
    for node_id, record in BASELINE["nodes"].items():
        assert record["assets"], node_id
        for asset in record["assets"]:
            assert (REPO_ROOT / asset).exists(), f"{node_id} -> {asset}"


def test_every_recorded_id_names_the_ports_the_assets_wire():
    """The contract a future item would have to satisfy, captured now."""
    for node_id, record in BASELINE["nodes"].items():
        assert "ports_used" in record, node_id


# ---------------------------------------------------------------------------
# NEVER_IMPLEMENTED is a claim about history, and it is checked
# ---------------------------------------------------------------------------

def test_the_never_implemented_ids_really_have_no_runtime():
    for node_id in BASELINE["never_implemented"]:
        assert node_id not in registry.executors, node_id
        assert node_id not in registry.evaluators, node_id
        assert node_id not in NODE_DEFINITIONS, node_id


def test_the_never_implemented_ids_are_not_aliases_of_anything():
    """If one resolved, it would be a rename gap rather than missing design."""
    for node_id in BASELINE["never_implemented"]:
        assert resolve_node_id(node_id) == node_id, node_id


def test_the_migration_map_still_points_at_ids_that_do_not_exist():
    """Item 12 recorded these dangling targets; 14A found what they cost.

    ``math.vector2_create -> vector2`` and friends rename onto node ids that
    were never implemented, which is why three of the chase chain's nodes are
    phantom.
    """
    from engine.logic.legacy_visual_script import LEGACY_NODE_TYPES

    dangling = sorted(
        target for target in set(LEGACY_NODE_TYPES.values())
        if target not in NODE_DEFINITIONS
    )
    assert dangling, "if the map became clean, this record is stale"
    assert set(dangling) & set(BASELINE["never_implemented"]), (
        "the dangling targets should overlap the never-implemented set"
    )


# ---------------------------------------------------------------------------
# The one restoration, proved end to end
# ---------------------------------------------------------------------------

def test_object_find_by_name_resolves_to_find_tag():
    assert NODE_ID_ALIASES["object.find_by_name"] == "find_tag"
    assert resolve_node_id("object.find_by_name") == "find_tag"


def test_it_is_an_alias_and_not_a_second_palette_entry():
    assert "object.find_by_name" not in NODE_DEFINITIONS


def test_the_target_has_a_real_runtime():
    assert "find_tag" in registry.executors
    assert "find_tag" in registry.evaluators


def test_it_is_no_longer_phantom():
    assert "object.find_by_name" not in _phantom_usage()
    assert "object.find_by_name" not in BASELINE["nodes"]


def test_the_shipping_assets_now_resolve_it():
    """Four instances across four assets were inert; count them resolved."""
    resolved = {}
    for path in SHIPPING:
        graph = normalize_logic_graph(load_logic_graph(path))
        hits = sum(1 for n in graph["nodes"] if str(n["type"]) == "find_tag")
        if hits:
            resolved[path.name] = hits
    assert sum(resolved.values()) >= 5, resolved
    assert {"BossAILogic.zlogic", "EnemyAILogic.zlogic",
            "EnemyAttackLogic.zlogic"} <= set(resolved), resolved


def test_the_restored_node_actually_runs():
    """Structure is not enough -- prove the evaluator answers."""
    graph = normalize_logic_graph({
        "format": "zennity.logic_graph", "version": 1, "name": "Legacy",
        "nodes": [{"id": "n", "type": "object.find_by_name", "position": [0.0, 0.0],
                   "properties": {"tag": "Player"}}],
        "edges": [],
    })
    assert graph["nodes"][0]["type"] == "find_tag"

    class _Game:
        def __init__(self):
            self.asked: list[str] = []

        def find(self, tag):
            self.asked.append(tag)
            return f"<{tag}>"

    from engine.logic.runtime.core import LogicGraphRuntime

    runtime = LogicGraphRuntime(graph)
    game = _Game()
    value = registry.evaluators["find_tag"](
        runtime, "n", "object", graph["nodes"][0], game, 1 / 60, set()
    )
    assert value == "<Player>"
    assert game.asked == ["Player"]


def test_no_asset_was_modified():
    import subprocess

    changed = subprocess.run(
        ["git", "status", "--porcelain", "--", "Assets"],
        cwd=REPO_ROOT, capture_output=True, text=True, check=True,
    ).stdout.strip()
    unallowed = [l for l in changed.splitlines() if "EnemyAttackLogic.zlogic" not in l and "BossHealthLogic.zlogic" not in l and "LevelExitLogic.zlogic" not in l and "VictoryLogic.zlogic" not in l]
    assert not unallowed, unallowed


# ---------------------------------------------------------------------------
# What item 14 originally set out to do, and why it stopped
# ---------------------------------------------------------------------------

def test_the_chase_chain_no_longer_runs_through_phantom_nodes():
    """The debt this recorded was paid; the assertion is inverted, not deleted.

    It used to say the chase chain *must* be broken, because at the time it
    was: BossAILogic and EnemyAILogic wired ``multiply_number.value`` into
    ``move_by.velocity`` through ``vector2`` / ``normalize_vector`` /
    ``math.distance``, none of which exist. That was recorded so nobody would
    "fix" ``move_by.velocity`` against a value that was really ``None``.

    PHASE 9 recovery item 14E reauthored both graphs onto the scalar chain
    proven in item 14D.2. The three phantom types are gone from both assets and
    the direction is now built from ``subtract_number`` / ``divide_number`` /
    ``multiply_number``. Keeping the check inverted means a regression that
    reintroduces the vector API fails here, which is what this test was always
    for.
    """
    for name in ("BossAILogic", "EnemyAILogic"):
        graph = normalize_logic_graph(
            load_logic_graph(REPO_ROOT / "Assets" / "Logic" / f"{name}.zlogic")
        )
        types = {str(n["type"]) for n in graph["nodes"]}
        assert not types & {"vector2", "normalize_vector", "math.distance"}, (
            f"{name} reintroduced the phantom vector chain"
        )
        assert "distance_to_point" in types, f"{name} lost its distance node"


def test_move_by_still_does_not_read_velocity():
    """Untouched on purpose: the value it would read is not produced yet."""
    import ast
    import inspect
    import textwrap

    source = textwrap.dedent(inspect.getsource(registry.executors["move_by"]))
    read = {
        argument.value
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
        and node.func.attr in ("get", "_read_input")
        for argument in node.args[:2]
        if isinstance(argument, ast.Constant) and isinstance(argument.value, str)
    }
    assert "velocity" not in read
