from __future__ import annotations

import json
from pathlib import Path

import pytest

from engine.logic.graph_asset import create_logic_node, node_port_definitions
from engine.prefabs.prefab_asset import create_prefab_variant, load_prefab_asset
from engine.runtime.runtime_world import RuntimeWorld


def _base_prefab(root: Path) -> Path:
    path = root / "Assets/Prefabs/Projectile.zprefab"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps({
        "format_version": 2,
        "prefab_name": "Projectile",
        "exposed_properties": [
            {"name": "speed", "label": "Velocidade", "type": "number", "default": 300, "target": "gameplay.speed"},
            {"name": "damage", "label": "Dano", "type": "number", "default": 1, "target": "gameplay.damage"},
            {"name": "color", "label": "Cor", "type": "color", "default": [10, 20, 30], "target": "color"},
            {"name": "tag", "label": "Tag", "type": "text", "default": "Projectile", "target": "tag"},
        ],
        "object": {
            "name": "Projectile", "x": 0, "y": 0, "w": 20, "h": 8,
            "color": [255, 255, 255], "tag": "Untagged", "gameplay": {},
        },
    }), encoding="utf-8")
    return path


def test_variant_inherits_base_and_only_overrides_selected_defaults(tmp_path: Path) -> None:
    base = _base_prefab(tmp_path)
    variant = tmp_path / "Assets/Prefabs/Missile.zprefab"
    create_prefab_variant(
        base, variant,
        property_overrides={"speed": 180, "damage": 4},
        object_overrides={"name": "Missile", "w": 38},
        project_root=tmp_path,
    )

    loaded = load_prefab_asset(variant, tmp_path)
    defaults = {item["name"]: item["default"] for item in loaded["exposed_properties"]}

    assert loaded["object"]["name"] == "Missile"
    assert loaded["object"]["w"] == 38
    assert defaults == {"speed": 180.0, "damage": 4.0, "color": [10, 20, 30], "tag": "Projectile"}


def test_runtime_applies_typed_parameters_and_preserves_debug_values(tmp_path: Path) -> None:
    base = _base_prefab(tmp_path)
    world = RuntimeWorld({})

    projectile = world.instantiate_prefab(
        base, project_root=tmp_path,
        parameters={"speed": "520", "damage": 3, "color": [80, 160, 240], "tag": "Missile"},
    )

    assert projectile["gameplay"] == {"speed": 520.0, "damage": 3.0}
    assert projectile["color"] == (80, 160, 240)
    assert projectile["tag"] == "Missile"
    assert projectile["prefab_parameters"]["speed"] == 520.0
    assert len(projectile["prefab_exposed"]) == 4


def test_logic_node_ports_follow_only_the_exposed_prefab_properties() -> None:
    node = create_logic_node("create_prefab")
    node["properties"]["exposed_properties"] = [
        {"name": "speed", "type": "number", "port": "param_speed"},
        {"name": "sound", "type": "audio", "port": "param_sound"},
        {"name": "homing", "type": "bool", "port": "param_homing"},
    ]

    inputs = dict(node_port_definitions(node)["inputs"])

    assert inputs["param_speed"] == "number"
    assert inputs["param_sound"] == "text"
    assert inputs["param_homing"] == "bool"
    assert "damage" not in inputs


def test_prefab_inheritance_cycle_is_rejected(tmp_path: Path) -> None:
    directory = tmp_path / "Assets/Prefabs"
    directory.mkdir(parents=True)
    first = directory / "First.zprefab"
    second = directory / "Second.zprefab"
    first.write_text(json.dumps({"base_prefab": "Assets/Prefabs/Second.zprefab"}), encoding="utf-8")
    second.write_text(json.dumps({"base_prefab": "Assets/Prefabs/First.zprefab"}), encoding="utf-8")

    with pytest.raises(ValueError, match="circular"):
        load_prefab_asset(first, tmp_path)
