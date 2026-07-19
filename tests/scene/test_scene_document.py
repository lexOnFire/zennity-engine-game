from __future__ import annotations

import json
from pathlib import Path

import pytest

from engine.scene import SceneDocument, load_scene_document, serialize_scene


ROOT = Path(__file__).resolve().parents[2]
SCENE_PATHS = sorted(
    [
        *ROOT.glob("Assets/Scenes/*.zscene"),
        *ROOT.glob("examples/*/Assets/Scenes/*.zscene"),
    ]
)


@pytest.mark.parametrize("scene_path", SCENE_PATHS, ids=lambda path: path.stem)
def test_repository_scenes_have_lossless_document_round_trip(scene_path) -> None:
    source = json.loads(scene_path.read_text(encoding="utf-8"))

    document = SceneDocument.load(scene_path)

    assert document.to_dict() == source
    assert json.loads(document.to_json()) == source


def test_unknown_fields_survive_round_trip() -> None:
    source = {
        "format_version": 99,
        "scene_name": "FutureScene",
        "engine_version": "future",
        "blackboard": {"variables": {"score": {"type": "int", "value": 7}}},
        "future_root": {"keep": True},
        "objects": [
            {
                "id": "player",
                "name": "Player",
                "future_object": [1, 2, 3],
                "components": {
                    "future_component": {"enabled": True, "payload": "keep"}
                },
            }
        ],
    }

    restored = SceneDocument.from_json(json.dumps(source)).to_dict()

    assert restored == source


def test_document_does_not_share_mutable_state_with_callers() -> None:
    source = {"objects": [{"id": "player", "components": {}}]}
    document = SceneDocument.from_dict(source)

    source["objects"][0]["id"] = "mutated-source"
    exported = document.to_dict()
    exported["objects"][0]["id"] = "mutated-export"

    assert document.objects[0]["id"] == "player"


def test_atomic_save_retains_previous_document_as_backup(tmp_path) -> None:
    path = tmp_path / "level.zscene"
    SceneDocument.empty("Before").save(path)
    SceneDocument.empty("After").save(path)

    assert load_scene_document(path).scene_name == "After"
    assert load_scene_document(path.with_suffix(".zscene.bak")).scene_name == "Before"
    assert not path.with_suffix(".zscene.tmp").exists()


def test_serializer_accepts_document_without_losing_extensions() -> None:
    source = {"objects": [], "extension": {"keep": True}}
    document = SceneDocument.from_dict(source)

    assert serialize_scene(document) == document.to_dict()


def test_official_editor_uses_scene_document_boundary() -> None:
    source = (ROOT / "editor/isolated_editor_main.py").read_text(encoding="utf-8")

    assert "SceneDocument.from_dict(payload).save(path)" in source
    assert "payload = SceneDocument.load(filename).to_dict()" in source
    assert "json.loads(Path(filename).read_text" not in source


@pytest.mark.parametrize(
    ("payload", "error", "message"),
    [
        ([], TypeError, "mapping"),
        ({"objects": {}}, ValueError, "must be a list"),
        ({"objects": ["invalid"]}, ValueError, "must be a mapping"),
    ],
)
def test_invalid_document_shape_is_rejected(payload, error, message) -> None:
    with pytest.raises(error, match=message):
        SceneDocument.from_dict(payload)
