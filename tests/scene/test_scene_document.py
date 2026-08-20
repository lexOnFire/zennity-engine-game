from __future__ import annotations

import json
from pathlib import Path

import pytest

from engine.scene import SceneDocument, load_scene_document, serialize_scene


ROOT = Path(__file__).resolve().parents[2]
ALL_SCENE_PATHS = sorted(
    [
        *ROOT.glob("Assets/Scenes/*.zscene"),
        *ROOT.glob("examples/*/Assets/Scenes/*.zscene"),
    ]
)

#: Pre-migration backups kept by 6a3fb0a7 when the benchmark scenes moved to the
#: canonical format. They are still on the old schema (``format``/``name``, no
#: ``format_version``), which is the whole reason they were kept, so the loader
#: upgrades them on read and byte-identity is the wrong contract for them.
#: They get their own test below.
LEGACY_SCENE_PATHS = [p for p in ALL_SCENE_PATHS if p.stem.endswith("_legacy")]
SCENE_PATHS = [p for p in ALL_SCENE_PATHS if p not in LEGACY_SCENE_PATHS]

#: What the migration is allowed to add to a pre-canonical document.
MIGRATION_HEADER_FIELDS = {"format_version", "scene_name", "engine_version"}


@pytest.mark.parametrize("scene_path", SCENE_PATHS, ids=lambda path: path.stem)
def test_repository_scenes_have_lossless_document_round_trip(scene_path) -> None:
    source = json.loads(scene_path.read_text(encoding="utf-8"))

    document = SceneDocument.load(scene_path)

    assert document.to_dict() == source
    assert json.loads(document.to_json()) == source


@pytest.mark.parametrize("scene_path", LEGACY_SCENE_PATHS, ids=lambda path: path.stem)
def test_legacy_scenes_migrate_without_losing_anything(scene_path) -> None:
    """Reading a pre-canonical scene may add the header, never drop content.

    The strict gate above cannot cover these: ``SceneDocument.load`` exists to
    upgrade them, so it necessarily returns something the file does not contain.
    What must still hold is that the upgrade is purely additive -- every key and
    every value present before the migration survives it.
    """
    source = json.loads(scene_path.read_text(encoding="utf-8"))

    migrated = SceneDocument.load(scene_path).to_dict()

    assert set(migrated) - set(source) <= MIGRATION_HEADER_FIELDS, (
        "the migration invented fields beyond the canonical header: "
        f"{sorted((set(migrated) - set(source)) - MIGRATION_HEADER_FIELDS)}"
    )
    for key, value in source.items():
        assert key in migrated, f"the migration dropped {key!r}"
        assert migrated[key] == value, f"the migration rewrote {key!r}"


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
    source += (ROOT / "editor/scene_persistence.py").read_text(encoding="utf-8")

    assert "SceneDocument.from_dict(payload).save(path)" in source
    assert "payload = SceneDocument.load(path).to_dict()" in source
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
