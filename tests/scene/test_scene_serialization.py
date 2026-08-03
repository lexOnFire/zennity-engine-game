from __future__ import annotations

import json
from types import SimpleNamespace

import numpy as np
import pytest

from engine.game_object import GameObject
from engine.physics.collider import BoxCollider, CircleCollider
from engine.physics.rigidbody import RigidBody
from engine.scene import (
    deserialize_game_object,
    deserialize_scene,
    load_scene,
    save_scene,
    serialize_game_object,
    serialize_scene,
)


def _component_by_class_name(obj: GameObject, class_name: str):
    return next((comp for comp in obj.components if type(comp).__name__ == class_name), None)


def test_serialize_and_load_empty_scene(tmp_path) -> None:
    scene = SimpleNamespace(name="Empty", editable_objects=[])

    data = serialize_scene(scene)

    assert data["scene_name"] == "Empty"
    assert data["objects"] == []

    path = save_scene(scene, tmp_path / "empty.zscene")
    loaded = load_scene(path)

    assert loaded["scene_name"] == "Empty"
    assert loaded["objects"] == []


def test_save_scene_keeps_previous_version_as_backup(tmp_path) -> None:
    path = tmp_path / "level.zscene"
    save_scene(SimpleNamespace(name="Before", editable_objects=[]), path)
    save_scene(SimpleNamespace(name="After", editable_objects=[]), path)

    backup = path.with_suffix(".zscene.bak")
    assert json.loads(backup.read_text(encoding="utf-8"))["scene_name"] == "Before"
    assert json.loads(path.read_text(encoding="utf-8"))["scene_name"] == "After"
    assert not path.with_suffix(".zscene.tmp").exists()


def test_serialize_scene_with_object_transform() -> None:
    obj = GameObject("Player", tag="Player")
    obj._id = "player-id"
    obj.layer = 3
    obj.enabled = True
    obj.mesh_type = "rect"
    obj.sprite_path = "assets/player.png"
    obj.transform.position = np.array([10.0, 20.0, 0.0], dtype=np.float32)
    obj.transform.rotation = np.array([0.0, 0.0, 45.0], dtype=np.float32)
    obj.transform.scale = np.array([2.0, 3.0, 1.0], dtype=np.float32)
    scene = SimpleNamespace(name="Level", editable_objects=[obj])

    data = serialize_scene(scene)

    saved = data["objects"][0]
    assert saved["id"] == "player-id"
    assert saved["tag"] == "Player"
    # CONSOLIDATION: layer agora é sempre string (bate com o que o editor
    # real grava em produção — ver engine/scene/scene_format.py). Um int
    # de entrada ainda é aceito e convertido, não gera mais erro.
    assert saved["layer"] == "3"
    assert saved["transform"]["position"] == [10.0, 20.0, 0.0]
    assert saved["transform"]["rz"] == pytest.approx(45.0)
    assert saved["transform"]["scale"] == [2.0, 3.0, 1.0]
    assert saved["visual"]["mesh_type"] == "rect"
    assert saved["visual"]["sprite_path"] == "Assets/player.png"


def test_serialize_scene_canonicalizes_nested_asset_references() -> None:
    obj = GameObject("Player")
    obj.scripts = ["assets/scripts/player.py"]
    scene = SimpleNamespace(name="Level", editable_objects=[obj])

    saved = serialize_scene(scene)["objects"][0]

    assert saved["components"]["scripts"] == ["Assets/scripts/player.py"]


def test_deserialize_game_object_restores_transform_and_identity() -> None:
    data = {
        "id": "stable-id",
        "name": "Platform",
        "tag": "Ground",
        "layer": 2,
        "active": False,
        "enabled": False,
        "transform": {
            "position": [1.0, 2.0, 3.0],
            "rotation": [4.0, 5.0, 6.0],
            "rz": 90.0,
            "scale": [7.0, 8.0, 9.0],
        },
        "visual": {"mesh_type": "rect", "sprite_path": None},
        "components": {},
    }

    obj = deserialize_game_object(data)

    assert obj.id == "stable-id"
    assert obj.name == "Platform"
    assert obj.tag == "Ground"
    # CONSOLIDATION: layer é normalizado para string mesmo vindo de int.
    assert obj.layer == "2"
    assert not obj.active
    assert not obj.enabled
    assert obj.mesh_type == "rect"
    assert obj.transform.position.tolist() == [1.0, 2.0, 3.0]
    assert obj.transform.rotation.tolist() == [4.0, 5.0, 90.0]
    assert obj.transform.scale.tolist() == [7.0, 8.0, 9.0]


def test_serialize_and_deserialize_collider_and_rigidbody(tmp_path) -> None:
    obj = GameObject("Dynamic")
    obj.add_component(BoxCollider(width=40, height=50, offset_x=1, offset_y=2, is_trigger=True))
    rb = obj.add_component(RigidBody(mass=2.5, gravity_scale=0.5, drag=0.1, use_gravity=False))
    rb.velocity = np.array([3.0, 4.0], dtype=np.float32)
    rb.acceleration = np.array([5.0, 6.0], dtype=np.float32)
    scene = SimpleNamespace(name="Physics", editable_objects=[obj])

    path = save_scene(scene, tmp_path / "physics.zscene")
    raw = json.loads(path.read_text(encoding="utf-8"))
    assert raw["objects"][0]["components"]["collider"]["type"] == "box"
    assert raw["objects"][0]["components"]["rigidbody"]["mass"] == pytest.approx(2.5)

    loaded = deserialize_scene(raw)
    restored = loaded["objects"][0]

    collider = _component_by_class_name(restored, "BoxCollider")
    rigidbody = _component_by_class_name(restored, "RigidBody")

    assert collider is not None
    assert collider.width == pytest.approx(40.0)
    assert collider.height == pytest.approx(50.0)
    assert collider.offset_x == pytest.approx(1.0)
    assert collider.offset_y == pytest.approx(2.0)
    assert collider.is_trigger

    assert rigidbody is not None
    assert rigidbody.mass == pytest.approx(2.5)
    assert rigidbody.gravity_scale == pytest.approx(0.5)
    assert rigidbody.drag == pytest.approx(0.1)
    assert not rigidbody.use_gravity
    assert rigidbody.velocity.tolist() == [3.0, 4.0]
    assert rigidbody.acceleration.tolist() == [5.0, 6.0]


def test_circle_collider_round_trip() -> None:
    obj = GameObject("Trigger")
    obj.add_component(CircleCollider(radius=12, offset_x=3, offset_y=4, is_trigger=True))

    restored = deserialize_game_object(serialize_game_object(obj))
    collider = _component_by_class_name(restored, "CircleCollider")

    assert collider is not None
    assert collider.radius == pytest.approx(12.0)
    assert collider.offset_x == pytest.approx(3.0)
    assert collider.offset_y == pytest.approx(4.0)
    assert collider.is_trigger
