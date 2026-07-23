from __future__ import annotations

from engine.prefabs.prefab_overrides import (
    apply_prefab_overrides,
    build_prefab_overrides,
    override_paths,
    revert_prefab_instance,
    update_prefab_instance,
)


def _prefab() -> dict:
    return {
        "name": "Crate",
        "transform": {"position": {"x": 2.0, "y": 3.0}, "scale": [1, 1]},
        "visual": {"color": "#ffffff", "texture": "crate.png"},
        "gameplay": {"health": 10, "drop/item": "coin"},
    }


def test_nested_instance_changes_round_trip_as_portable_patch() -> None:
    instance = _prefab()
    instance["transform"]["position"]["x"] = 20.0
    instance["visual"].pop("texture")
    instance["gameplay"]["drop/item"] = "gem"
    instance["id"] = "scene-only"
    instance["prefab_source"] = "Assets/Prefabs/Crate.zprefab"

    overrides = build_prefab_overrides(_prefab(), instance)
    restored = apply_prefab_overrides(_prefab(), overrides)

    assert overrides["values"] == {
        "/gameplay/drop~1item": "gem",
        "/transform/position/x": 20.0,
    }
    assert overrides["removed"] == ["/visual/texture"]
    assert "id" not in restored
    assert restored["gameplay"]["drop/item"] == "gem"
    assert "texture" not in restored["visual"]


def test_update_pulls_new_prefab_values_and_retains_instance_overrides() -> None:
    instance = _prefab()
    instance["visual"]["color"] = "#ff0000"
    instance["prefab_guid"] = "guid-1"
    instance["prefab_source"] = "Assets/Prefabs/Crate.zprefab"
    instance["prefab_overrides"] = build_prefab_overrides(_prefab(), instance)
    updated_prefab = _prefab()
    updated_prefab["gameplay"]["health"] = 25

    refreshed = update_prefab_instance(updated_prefab, instance)

    assert refreshed["visual"]["color"] == "#ff0000"
    assert refreshed["gameplay"]["health"] == 25
    assert refreshed["prefab_guid"] == "guid-1"


def test_revert_discards_changes_but_preserves_instance_linkage() -> None:
    instance = _prefab()
    instance.update({
        "id": "instance-1",
        "name": "Changed",
        "prefab_guid": "guid-1",
        "prefab_source": "Assets/Prefabs/Crate.zprefab",
        "prefab_overrides": {"values": {"/name": "Changed"}, "removed": []},
    })

    reverted = revert_prefab_instance(_prefab(), instance)

    assert reverted["name"] == "Changed"
    assert reverted["id"] == "instance-1"
    assert reverted["prefab_guid"] == "guid-1"
    assert override_paths(reverted["prefab_overrides"]) == []


def test_invalid_or_private_override_paths_are_ignored() -> None:
    patched = apply_prefab_overrides(
        _prefab(),
        {
            "values": {"invalid": 1, "/__class__/danger": True},
            "removed": ["/__dict__"],
        },
    )

    assert patched == _prefab()
