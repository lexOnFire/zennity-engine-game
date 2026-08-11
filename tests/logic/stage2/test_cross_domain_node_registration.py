"""One real node per domain must exist, with and without a provider.

Whole domains used to vanish depending on the load path: the non-provider path
never imported the dialogue, audio, camera, save/load, pathfinding or advanced
input modules at all.
"""

from __future__ import annotations

import pytest

from ._probe import SNAPSHOT_SOURCE, run_in_fresh_process
from .test_registration_parity import BOOT_PROVIDER

#: domain -> (node id, runtime module that must own it)
DOMAIN_NODES = {
    "Input": ("input_axis", "engine.logic.runtime.nodes.event_nodes"),
    "Math": ("add_number", "engine.logic.runtime.nodes.math_nodes"),
    "Physics": ("apply_force", "engine.logic.runtime.nodes.physics_nodes"),
    "Animation": ("play_animation", "engine.logic.runtime.nodes.animation_nodes"),
    "UI": ("set_ui_text", "engine.logic.runtime.nodes.ui_nodes"),
    "Audio": ("set_volume", "engine.logic.runtime.nodes.audio_advanced_nodes"),
    "Scene": ("load_scene", "engine.logic.runtime.nodes.scene_nodes"),
    "Dialogue": ("show_dialog", "engine.logic.runtime.nodes.dialog_nodes"),
    "SaveLoad": ("save_game", "engine.logic.runtime.nodes.save_load_nodes"),
    "Camera": ("camera_shake", "engine.logic.runtime.nodes.camera_nodes"),
}


@pytest.mark.parametrize("domain", sorted(DOMAIN_NODES))
def test_domain_node_has_a_contract_and_an_implementation(domain):
    from engine.logic.node_system import describe_node

    node_id, owner = DOMAIN_NODES[domain]
    described = describe_node(node_id)
    assert described["exists"], f"{domain}: node '{node_id}' is missing entirely"
    assert described["has_executor"] or described["has_evaluator"], (
        f"{domain}: node '{node_id}' has a contract but nothing implements it"
    )
    assert described["runtime_owner_module"] == owner, (
        f"{domain}: '{node_id}' is implemented by {described['runtime_owner_module']}, "
        f"expected {owner}"
    )


def test_every_domain_survives_both_load_paths():
    without = run_in_fresh_process(SNAPSHOT_SOURCE)
    with_provider = run_in_fresh_process(BOOT_PROVIDER + SNAPSHOT_SOURCE)
    missing_without = []
    missing_with = []
    for domain, (node_id, _owner) in sorted(DOMAIN_NODES.items()):
        if node_id not in without["executors"] and node_id not in without["evaluators"]:
            missing_without.append(f"{domain}:{node_id}")
        if node_id not in with_provider["executors"] and node_id not in with_provider["evaluators"]:
            missing_with.append(f"{domain}:{node_id}")
    assert not missing_without, f"missing without a provider: {missing_without}"
    assert not missing_with, f"missing with a provider: {missing_with}"
