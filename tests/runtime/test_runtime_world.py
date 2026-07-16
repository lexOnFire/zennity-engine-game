from __future__ import annotations

import json

from engine.runtime.runtime_world import RuntimeWorld, normalize_color


def test_runtime_world_creates_unique_objects_and_tracks_lifecycle():
    objects = {}
    world = RuntimeWorld(objects)
    first = world.create_object(name="Moeda", color="#ff8040")
    second = world.create_object(name="Moeda")
    world.destroy_object(first)

    assert first["name"] == "Moeda"
    assert second["name"] == "Moeda_2"
    assert first["color"] == (255, 128, 64)
    assert first["active"] is False and first["destroyed"] is True
    assert world.stats() == {"objects": 1, "active": 1, "created": 2, "destroyed": 1, "reused": 0, "pooled": 0}


def test_runtime_world_clones_components_without_sharing_state():
    objects = {}
    world = RuntimeWorld(objects)
    source = world.create_object(name="Enemy", collider={"type": "box"})
    clone = world.clone_object(source)
    clone["collider"]["type"] = "circle"

    assert clone["name"] == "Enemy_Copia"
    assert source["collider"]["type"] == "box"
    world.add_component(clone, "RigidBody2D", {"gravity_scale": 2})
    assert clone["rigidbody"]["use_gravity"] is True
    assert world.remove_component(clone, "RigidBody2D") is True


def test_runtime_world_clone_preserves_every_public_property_independently():
    objects = {}
    world = RuntimeWorld(objects)
    source = world.create_object(
        name="Player",
        animator={"active_clip": "Idle", "parameters": {"speed": 0}},
        logic_graphs=[{"path": "Assets/Logic/Player.zlogic", "enabled": True}],
    )
    source["custom_gameplay"] = {"inventory": ["key"], "score": 10}

    clone = world.clone_object(source, "PlayerClone")
    clone["animator"]["parameters"]["speed"] = 5
    clone["logic_graphs"][0]["enabled"] = False
    clone["custom_gameplay"]["inventory"].append("coin")

    assert clone["name"] == "PlayerClone"
    assert clone["id"] != source["id"]
    assert source["animator"]["parameters"]["speed"] == 0
    assert source["logic_graphs"][0]["enabled"] is True
    assert source["custom_gameplay"]["inventory"] == ["key"]


def test_runtime_world_instantiates_prefab_with_runtime_components(tmp_path):
    prefab = tmp_path / "enemy.zprefab"
    prefab.write_text(json.dumps({
        "name": "EnemyPrefab",
        "source_object_name": "Enemy",
        "transform": {"position": [10, 20, 0], "rotation": [0, 0, 15], "scale": [32, 48, 1]},
        "visual": {"color": [220, 80, 80], "sprite_path": "Assets/enemy.png"},
        "components": {
            "collider": {"type": "box"}, "rigidbody": {"use_gravity": True},
            "items": [
                {"type": "Camera", "enabled": True, "properties": {"clear_color": [4, 8, 12]}},
                {"type": "AudioSource", "enabled": True, "properties": {"audio_clip": "Assets/Audio/hit.wav", "play_on_awake": True}},
            ],
        },
    }), encoding="utf-8")
    world = RuntimeWorld({})

    obj = world.instantiate_prefab(prefab, x=100, y=200)

    assert (obj["x"], obj["y"], obj["w"], obj["h"], obj["rotation"]) == (100, 200, 32, 48, 15)
    assert obj["texture"] == "Assets/enemy.png"
    assert obj["collider"]["type"] == "box"
    assert obj["camera"]["background_color"] == [4, 8, 12]
    assert obj["audio"]["path"] == "Assets/Audio/hit.wav"
    assert obj["audio"]["autoplay"] is True
    assert normalize_color("inválida") == (88, 166, 255)


def test_runtime_world_accepts_editor_prefab_wrapper(tmp_path):
    prefab = tmp_path / "platform.zprefab"
    prefab.write_text(json.dumps({
        "format_version": 1,
        "prefab_name": "Platform",
        "object": {
            "id": "editor-only-id", "name": "Ground", "x": 12, "y": 24,
            "w": 160, "h": 20, "texture": "Assets/Textures/ground.png",
            "collider": {"type": "box"}, "sort_order": 3,
        },
    }), encoding="utf-8")
    world = RuntimeWorld({})

    obj = world.instantiate_prefab(prefab, x=90)

    assert obj["id"] != "editor-only-id"
    assert (obj["x"], obj["y"], obj["w"], obj["h"]) == (90, 24, 160, 20)
    assert obj["texture"] == "Assets/Textures/ground.png"
    assert obj["collider"]["type"] == "box"
    assert obj["sort_order"] == 3


def test_prefab_instances_are_reused_after_destruction(tmp_path):
    prefab = tmp_path / "bullet.zprefab"
    prefab.write_text(json.dumps({"name": "Bullet", "transform": {"scale": [8, 8, 1]}}), encoding="utf-8")
    world = RuntimeWorld({})
    first = world.instantiate_prefab(prefab)
    world.destroy_object(first)
    second = world.instantiate_prefab(prefab)

    assert second is first
    assert world.stats()["reused"] == 1


def test_prefab_pool_has_a_memory_limit(tmp_path):
    prefab = tmp_path / "particle.zprefab"
    prefab.write_text(json.dumps({"name": "Particle"}), encoding="utf-8")
    world = RuntimeWorld({})
    instances = [world.instantiate_prefab(prefab) for _ in range(RuntimeWorld.MAX_POOLED_PER_PREFAB + 10)]

    for instance in instances:
        world.destroy_object(instance)

    assert world.stats()["pooled"] == RuntimeWorld.MAX_POOLED_PER_PREFAB
