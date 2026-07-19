from __future__ import annotations

import json
from pathlib import Path

import pytest

from engine.scene import SceneDocument


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
