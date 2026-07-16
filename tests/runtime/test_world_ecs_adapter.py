from engine.runtime.world_ecs_adapter import RuntimeWorldECSAdapter


def test_runtime_world_ecs_adapter_round_trip_transform() -> None:
    runtime_object = {
        "name": "Player", "tag": "Hero", "active": True,
        "x": 12.0, "y": -4.0, "z": 2.0, "rotation": 30.0,
        "w": 48.0, "h": 64.0, "mesh_type": "Sprite",
    }
    game_object = RuntimeWorldECSAdapter.to_game_object(runtime_object)
    assert game_object.name == "Player"
    assert game_object.transform.x == 12.0
    assert game_object.transform.rz == 30.0

    game_object.transform.x = 99.0
    game_object.transform.sy = 80.0
    RuntimeWorldECSAdapter.update_runtime_object(game_object, runtime_object)
    assert runtime_object["x"] == 99.0
    assert runtime_object["h"] == 80.0

