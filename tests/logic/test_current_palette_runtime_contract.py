"""Phase 9.5B Stage 1 — the pins the palette shows are the pins the runtime accepts.

Brief item 19.  This walks the real palette catalogue and checks, per node, that
what an author can see and connect is what the executor actually reads, stores
and returns.
"""
from __future__ import annotations

import pytest

from engine.logic.node_definitions import NODE_DEFINITIONS

# The nodes the brief names explicitly, plus the ones Stage 1 changed most.
REQUIRED = [
    "move_by", "input_axis", "set_variable", "play_animation",
    "raycast", "set_ui_text", "scene.load_scene", "add_number",
]


@pytest.fixture(scope="module")
def registry():
    import engine.logic.provider  # noqa: F401
    for module in (
        "actions_nodes", "components_nodes", "event_nodes", "flow_nodes",
        "math_nodes", "misc_nodes", "movement_nodes", "prefab_nodes",
        "scene_nodes", "string_nodes", "dynamic_ui_nodes", "animation_nodes",
        "physics_nodes", "dialog_nodes", "audio_advanced_nodes",
        "particle_nodes", "camera_nodes", "state_machine_nodes",
        "save_load_nodes", "pathfinding_nodes", "input_advanced_nodes",
        "ui_binding_nodes", "ui_nodes",
    ):
        __import__(f"engine.logic.runtime.nodes.{module}")
    from engine.logic.runtime.registry import registry as reg
    return reg


@pytest.mark.parametrize("node_id", REQUIRED)
def test_required_node_is_in_the_palette(node_id):
    assert node_id in NODE_DEFINITIONS


@pytest.mark.parametrize("node_id", REQUIRED)
def test_required_node_has_a_runtime_handler(node_id, registry):
    from engine.logic.contracts import ExecutionModel

    entry = NODE_DEFINITIONS[node_id]
    model = entry.get("execution_model", "action")
    if model in (ExecutionModel.EVENT_SOURCE.value, ExecutionModel.PURE_DATA.value):
        has = node_id in registry.evaluators or node_id in registry.executors
    else:
        has = node_id in registry.executors
    assert has, f"{node_id} is offered in the palette with no runtime handler"


@pytest.mark.parametrize("node_id", REQUIRED)
def test_required_node_exec_pins_are_canonical(node_id):
    from engine.logic.port_aliases import EXEC_PORT_ALIASES

    entry = NODE_DEFINITIONS[node_id]
    for pin_id, pin_type in entry.get("outputs", []) or []:
        if pin_type == "flow":
            assert pin_id not in EXEC_PORT_ALIASES, (
                f"{node_id} still advertises the legacy exec pin {pin_id!r}"
            )


def test_no_palette_node_is_offered_without_a_runtime(registry):
    """Every non-deprecated, non-event node must be executable."""
    from engine.logic.contracts import ExecutionModel
    from engine.logic.port_aliases import canonical_node_id

    unusable = []
    for node_id, entry in NODE_DEFINITIONS.items():
        if entry.get("deprecated"):
            continue
        model = entry.get("execution_model", "action")
        if model == ExecutionModel.EVENT_SOURCE.value:
            continue
        resolved = canonical_node_id(node_id)
        if resolved in registry.executors or resolved in registry.evaluators:
            continue
        unusable.append(node_id)

    assert not unusable, f"palette offers nodes with no runtime: {sorted(unusable)}"


def test_palette_categories_are_reasonable():
    """No category may become a dumping ground (Phase 9.5A S4)."""
    counts: dict[str, int] = {}
    for entry in NODE_DEFINITIONS.values():
        cat = str(entry.get("category", "?"))
        counts[cat] = counts.get(cat, 0) + 1
    oversized = {c: n for c, n in counts.items() if n > 50}
    assert not oversized, f"categories need splitting: {oversized}"


def test_deprecated_nodes_are_marked_so_the_palette_can_hide_them():
    deprecated = [n for n, e in NODE_DEFINITIONS.items() if e.get("deprecated")]
    # animate_value and wait_until_condition have no runtime at all.
    assert set(deprecated) == {"animate_value", "wait_until_condition"}, deprecated


def test_alias_ids_do_not_get_their_own_palette_entry():
    """Five spellings of "load scene" must not appear as five nodes."""
    from engine.logic.port_aliases import NODE_ID_ALIASES

    leaked = sorted(a for a in NODE_ID_ALIASES if a in NODE_DEFINITIONS)
    assert not leaked, f"legacy aliases leaked into the palette: {leaked}"
