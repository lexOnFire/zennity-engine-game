"""Node-id aliases: one table, one direction, and never a second palette row.

PHASE 9 recovery item 2.

The canonical spelling is the dotted one, because that is what the shipping
assets actually contain. Measured on this branch, not assumed:

    scene.load_scene       5 uses    load_scene       0
    ui.button_clicked      5 uses    button_clicked   0
    app.quit               1 use     quit_game        0
    ui.set_widget_enabled  1 use     set_ui_enabled   0

The table used to point the other way, which made every one of those saved ids
resolve onto an id no asset uses. Renaming ids that assets already carry buys
nothing, so the dotted form owns the definition, the palette entry and the port
contract, and the flat form is a load-time alias.

A node-id alias (``load_scene`` -> ``scene.load_scene``) is a different thing
from a port alias (``in`` -> ``exec``) and the two are deliberately not mixed:
one maps node identity, the other maps pin names.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from engine.logic.graph_asset import (
    NODE_DEFINITIONS,
    NODE_PORT_DEFINITIONS,
    load_logic_graph,
    normalize_logic_graph,
    save_logic_graph,
)
from engine.logic.node_definitions.catalogue import (
    NODE_ID_ALIASES,
    ensure_catalogue_loaded,
    get_aliases_for,
    get_node_aliases,
    resolve_node_id,
    validate_node_id_aliases,
)

REPO_ROOT = Path(__file__).resolve().parents[2]

CANONICAL_IDS = ("scene.load_scene", "ui.button_clicked", "app.quit", "ui.set_widget_enabled")

LEGACY_TO_CANONICAL = {
    "load_scene": "scene.load_scene",
    "open_scene": "scene.load_scene",
    "button_clicked": "ui.button_clicked",
    "on_ui_click": "ui.button_clicked",
    "quit_game": "app.quit",
    "exit_game": "app.quit",
    "set_ui_enabled": "ui.set_widget_enabled",
}


# ---------------------------------------------------------------------------
# Resolution
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("legacy,canonical", sorted(LEGACY_TO_CANONICAL.items()))
def test_a_legacy_id_resolves_to_the_canonical_one(legacy: str, canonical: str):
    assert resolve_node_id(legacy) == canonical


@pytest.mark.parametrize("node_id", CANONICAL_IDS)
def test_a_canonical_id_resolves_to_itself(node_id: str):
    assert resolve_node_id(node_id) == node_id


def test_an_unknown_id_is_returned_unchanged():
    assert resolve_node_id("definitely_not_a_node") == "definitely_not_a_node"


def test_resolution_is_idempotent():
    ensure_catalogue_loaded()
    candidates = set(NODE_ID_ALIASES) | set(NODE_ID_ALIASES.values()) | set(NODE_DEFINITIONS)
    for node_id in candidates:
        once = resolve_node_id(node_id)
        assert resolve_node_id(once) == once, node_id


def test_the_table_has_no_cycles_self_aliases_or_dangling_targets():
    ensure_catalogue_loaded()
    assert validate_node_id_aliases(set(NODE_DEFINITIONS)) == []


def test_no_alias_target_is_itself_an_alias():
    """What makes one-step resolution enough."""
    overlapping = set(NODE_ID_ALIASES) & set(NODE_ID_ALIASES.values())
    assert not overlapping, f"both a legacy key and a canonical target: {sorted(overlapping)}"


def test_the_reverse_lookup_agrees_with_the_table():
    for canonical in set(NODE_ID_ALIASES.values()):
        for alias in get_aliases_for(canonical):
            assert NODE_ID_ALIASES[alias] == canonical


def test_the_table_is_read_only():
    with pytest.raises((TypeError, AttributeError)):
        get_node_aliases()["injected"] = "x"  # type: ignore[index]


def test_there_is_one_node_id_alias_table():
    """No module may keep its own node-id mapping beside the catalogue's."""
    import engine.logic.graph_normalizer as normalizer
    import engine.logic.node_system as node_system

    for module in (normalizer, node_system):
        for name in dir(module):
            if "ALIAS" not in name.upper():
                continue
            value = getattr(module, name)
            if isinstance(value, dict) and value:
                pytest.fail(f"{module.__name__}.{name} is a second node-id alias table")


# ---------------------------------------------------------------------------
# Palette
# ---------------------------------------------------------------------------

def test_no_alias_is_visible_in_the_palette():
    """The generic gate: visible ids and alias ids must not intersect."""
    ensure_catalogue_loaded()
    leaked = sorted(set(NODE_ID_ALIASES) & set(NODE_DEFINITIONS))
    assert not leaked, f"aliases with their own palette entry: {leaked}"


def test_no_alias_has_its_own_port_contract():
    ensure_catalogue_loaded()
    leaked = sorted(set(NODE_ID_ALIASES) & set(NODE_PORT_DEFINITIONS))
    assert not leaked, f"aliases with their own port contract: {leaked}"


@pytest.mark.parametrize("node_id", CANONICAL_IDS)
def test_the_canonical_id_is_in_the_palette(node_id: str):
    entry = NODE_DEFINITIONS.get(node_id)
    assert entry is not None, f"{node_id} has no palette entry; an author cannot place it"
    assert entry.get("title"), f"{node_id} has no display name"
    assert entry.get("category"), f"{node_id} has no category"


def test_button_clicked_appears_exactly_once():
    """It was added to a shadowed file once and never appeared at all."""
    spellings = [
        node_id for node_id in NODE_DEFINITIONS
        if node_id in ("ui.button_clicked", "button_clicked", "on_ui_click")
    ]
    assert spellings == ["ui.button_clicked"], spellings


@pytest.mark.parametrize("node_id", CANONICAL_IDS)
def test_the_palette_rescue_did_not_empty_the_port_contract(node_id: str):
    """Metadata rescue must never overwrite a good contract with nothing.

    A declarative definition carrying no pins was once written straight over the
    port schema, turning a working contract into an empty one.
    """
    entry = NODE_DEFINITIONS[node_id]
    schema = NODE_PORT_DEFINITIONS[node_id]
    assert schema["inputs"], f"{node_id} lost its inputs"
    assert [tuple(p) for p in entry["inputs"]] == [tuple(p) for p in schema["inputs"]]
    assert [tuple(p) for p in entry["outputs"]] == [tuple(p) for p in schema["outputs"]]


def test_the_rescued_nodes_have_a_runtime():
    from engine.logic.node_system import load_runtime_node_modules
    from engine.logic.runtime.registry import registry

    load_runtime_node_modules()
    for node_id in CANONICAL_IDS:
        assert node_id in registry.executors or node_id in registry.evaluators, node_id


# ---------------------------------------------------------------------------
# Load and save
# ---------------------------------------------------------------------------

LEGACY_GRAPH = {
    "format": "zennity.logic_graph",
    "version": 1,
    "name": "LegacyIds",
    "nodes": [
        {"id": f"n{index}", "type": legacy, "position": [index * 200.0, 0.0]}
        for index, legacy in enumerate(sorted(LEGACY_TO_CANONICAL))
    ],
    "edges": [],
}


def test_a_legacy_graph_loads_as_canonical_ids():
    normalized = normalize_logic_graph(LEGACY_GRAPH)
    resolved = [node["type"] for node in normalized["nodes"]]
    expected = [LEGACY_TO_CANONICAL[legacy] for legacy in sorted(LEGACY_TO_CANONICAL)]
    assert resolved == expected
    assert not set(resolved) & set(NODE_ID_ALIASES), "a legacy id survived the load"


def test_normalizing_a_legacy_graph_is_idempotent():
    once = normalize_logic_graph(LEGACY_GRAPH)
    assert normalize_logic_graph(once) == once


def test_saving_a_legacy_graph_writes_canonical_ids(tmp_path: Path):
    destination = tmp_path / "LegacyIds.zlogic"
    save_logic_graph(destination, normalize_logic_graph(LEGACY_GRAPH))
    written = json.loads(destination.read_text(encoding="utf-8"))
    types = {str(node["type"]) for node in written["nodes"]}
    assert types == set(LEGACY_TO_CANONICAL.values())
    assert not types & set(NODE_ID_ALIASES)


def test_a_canonical_graph_round_trips_unchanged(tmp_path: Path):
    graph = {
        "format": "zennity.logic_graph", "version": 1, "name": "CanonicalIds",
        "nodes": [
            {"id": f"n{index}", "type": node_id, "position": [index * 200.0, 0.0]}
            for index, node_id in enumerate(CANONICAL_IDS)
        ],
        "edges": [],
    }
    destination = tmp_path / "CanonicalIds.zlogic"
    normalized = normalize_logic_graph(graph)
    save_logic_graph(destination, normalized)
    assert normalize_logic_graph(load_logic_graph(destination)) == normalized


# ---------------------------------------------------------------------------
# The evidence behind the decision
# ---------------------------------------------------------------------------

def _shipping_node_type_counts() -> dict[str, int]:
    counts: dict[str, int] = {}
    for path in REPO_ROOT.rglob("*.zlogic"):
        if ".git" in path.parts:
            continue
        for node in json.loads(path.read_text(encoding="utf-8")).get("nodes", []):
            node_type = str(node.get("type", ""))
            counts[node_type] = counts.get(node_type, 0) + 1
    return counts


@pytest.mark.parametrize("canonical", CANONICAL_IDS)
def test_the_assets_still_prefer_the_canonical_spelling(canonical: str):
    """If this ever fails, the direction is worth revisiting -- not before."""
    counts = _shipping_node_type_counts()
    legacy_uses = sum(counts.get(alias, 0) for alias in get_aliases_for(canonical))
    assert counts.get(canonical, 0) > 0, f"no asset uses {canonical}"
    assert legacy_uses == 0, (
        f"{canonical}: assets now use a legacy spelling {legacy_uses} time(s); "
        "the canonical direction was chosen from asset usage and should be re-checked"
    )


def test_every_alias_a_shipping_asset_uses_resolves_to_a_real_node():
    """Assets may carry an alias -- that is what the layer is for -- but it must land.

    Three assets do, and the measurement behind them is worth keeping visible:

        variables.set   4 uses   set_variable  10   -> flat is canonical, correct
        game.load_game  1 use    load_game      0   \\_ dotted is the only spelling
        game.has_save   1 use    has_save       0   /   used; recorded, not changed

    The bottom two match the pattern that made the scene/UI ids dotted, but they
    are outside this item's authorised set, so the direction is left alone and
    reported rather than quietly extended.
    """
    ensure_catalogue_loaded()
    counts = _shipping_node_type_counts()
    used_aliases = {t: n for t, n in counts.items() if t in NODE_ID_ALIASES}
    unresolvable = {
        alias: resolve_node_id(alias)
        for alias in used_aliases
        if resolve_node_id(alias) not in NODE_DEFINITIONS
    }
    assert not unresolvable, (
        f"shipping assets use aliases that resolve nowhere: {unresolvable}"
    )


def test_opening_a_shipping_asset_does_not_rewrite_it(tmp_path: Path):
    """Section 15: no asset may change merely by being opened and validated."""
    checked = 0
    for path in sorted(REPO_ROOT.rglob("*.zlogic")):
        if ".git" in path.parts:
            continue
        before = path.read_bytes()
        normalize_logic_graph(load_logic_graph(path))
        assert path.read_bytes() == before, f"{path.name} changed on load"
        checked += 1
    assert checked, "no shipping graphs found; this guard would be vacuous"
