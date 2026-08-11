"""Phase 9.5B Stage 1 — a duplicate node id is a loud failure (brief item 9).

Before Stage 1, catalogue construction was silent last-write-wins, which let
`play_animation` and `stop_animation` exist twice with incompatible port
contracts: the palette showed one definition and the MetadataManager held the
other.
"""
from __future__ import annotations

import pytest

from engine.logic.node_definitions import (
    NODE_DEFINITIONS,
    DuplicateNodeDefinitionError,
    assert_no_duplicate_definitions,
    definition_owner,
    duplicate_definition_conflicts,
)


def test_catalogue_has_no_duplicate_ids():
    assert duplicate_definition_conflicts() == []
    assert_no_duplicate_definitions()  # must not raise


def test_every_node_id_has_exactly_one_owning_module():
    for node_id in NODE_DEFINITIONS:
        owner = definition_owner(node_id)
        # Hardcoded legacy entries have no declarative owner; that is expected.
        if owner is not None:
            assert isinstance(owner, str) and owner


def test_play_animation_split_brain_is_resolved():
    """The Phase 9.5A P0 #2."""
    assert definition_owner("play_animation") == "animation_nodes"
    assert definition_owner("stop_animation") == "animation_nodes"

    entry = NODE_DEFINITIONS["play_animation"]
    inputs = {p[0] for p in entry["inputs"]}
    # `state` carries the real values in all four project assets ('Run',
    # 'Jump', 'Idle', 'PlayerAttack'); `animation_name` held a stale 'idle'.
    assert "state" in inputs, f"play_animation inputs are {sorted(inputs)}"
    assert "target" in inputs
    outputs = {p[0] for p in entry["outputs"]}
    assert outputs == {"next", "exec_failure", "animation"}, sorted(outputs)


def test_actions_nodes_no_longer_declares_the_animation_pair():
    import engine.logic.node_definitions.actions_nodes as actions

    assert not hasattr(actions, "PlayAnimationNode")
    assert not hasattr(actions, "StopAnimationNode")


def test_duplicate_registration_raises():
    """The detector must actually fire, not just be present."""
    import engine.logic.node_definitions as pkg

    conflicts = pkg._DEFINITION_CONFLICTS
    saved = list(conflicts)
    try:
        conflicts.append(("probe_node", "module_a", "module_b"))
        with pytest.raises(DuplicateNodeDefinitionError) as excinfo:
            assert_no_duplicate_definitions()
        message = str(excinfo.value)
        assert "probe_node" in message
        assert "module_a" in message
        assert "module_b" in message
    finally:
        conflicts[:] = saved


def test_boot_validation_raises_on_duplicates():
    import engine.logic.node_definitions as pkg
    from engine.logic.boot_validation import validate_catalogue_at_boot

    saved = list(pkg._DEFINITION_CONFLICTS)
    try:
        pkg._DEFINITION_CONFLICTS.append(("probe", "a", "b"))
        with pytest.raises(DuplicateNodeDefinitionError):
            validate_catalogue_at_boot()
    finally:
        pkg._DEFINITION_CONFLICTS[:] = saved


def test_boot_validation_is_clean_on_the_real_catalogue():
    from engine.logic.boot_validation import validate_catalogue_at_boot
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

    from engine.logic.contracts import Severity

    violations = validate_catalogue_at_boot()
    errors = [v for v in violations if v.severity is Severity.ERROR]
    assert not errors, f"boot validation reported errors: {[str(v) for v in errors]}"
