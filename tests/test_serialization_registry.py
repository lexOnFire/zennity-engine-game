import json

from engine.serialization_registry import SerializationCodec, SerializationRegistry


def test_registry_round_trip_uses_atomic_json(tmp_path):
    registry = SerializationRegistry()
    registry.register(SerializationCodec("scene", (".zscene",), 2, lambda payload: payload, lambda value: value))
    path = tmp_path / "scene.zscene"
    registry.write(path, {"scene_name": "Demo"})
    assert registry.read(path)["scene_name"] == "Demo"
    assert json.loads(path.read_text(encoding="utf-8"))["format_version"] == 2
    assert not (tmp_path / ".scene.zscene.tmp").exists()
