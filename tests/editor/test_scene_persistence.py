from pathlib import Path
from copy import deepcopy

import pytest

from editor.scene_persistence import EditorScenePersistence
from engine.scene import SceneDocument


def snapshot(name: str = "Player") -> dict:
    return {
        "id": "player", "name": name,
        "x": 10.0, "y": 20.0, "w": 32.0, "h": 48.0,
        "rotation": 15.0, "color": [1, 2, 3], "active": True,
        "custom_editor_value": {"keep": True},
        "collider": {"type": "box"},
    }


def test_scene_persistence_round_trip_preserves_future_fields(tmp_path: Path) -> None:
    path = tmp_path / "level.zscene"
    existing = {
        "format_version": 99,
        "scene_name": "Future",
        "future_root": {"keep": True},
        "objects": [{
            "id": "player", "name": "Player",
            "future_object": [1, 2, 3],
            "components": {"future_component": {"enabled": True}},
        }],
    }
    persistence = EditorScenePersistence(tmp_path)

    saved = persistence.save(path, [snapshot()], existing)
    payload, restored, typed = persistence.load(path)

    assert saved["future_root"] == {"keep": True}
    assert payload["objects"][0]["future_object"] == [1, 2, 3]
    assert payload["objects"][0]["components"]["future_component"] == {"enabled": True}
    assert restored[0]["custom_editor_value"] == {"keep": True}
    assert restored[0]["collider"]["width"] == 32.0
    assert typed is True


def test_scene_persistence_does_not_nest_editor_data_on_round_trip(tmp_path: Path) -> None:
    path = tmp_path / "level.zscene"
    existing = {
        "format_version": 2,
        "scene_name": "Level",
        "objects": [{
            "id": "guard",
            "name": "Guard",
            "transform": {
                "position": [0.0, 0.0, 0.0],
                "rotation": [0.0, 0.0, 0.0],
                "rz": 0.0,
                "scale": [32.0, 32.0, 1.0],
            },
            "visual": {},
            "editor_data": {
                "logic_graphs": [{
                    "path": "Assets/Logic/GuardInteractionLogic.zlogic",
                    "name": "GuardInteractionLogic",
                }],
            },
        }],
    }
    persistence = EditorScenePersistence(tmp_path)
    SceneDocument.from_dict(existing).save(path)
    _payload, snapshots, _typed = persistence.load(path)
    saved = persistence.save(path, snapshots, existing)

    editor_data = saved["objects"][0]["editor_data"]
    assert editor_data["logic_graphs"] == [{
        "path": "Assets/Logic/GuardInteractionLogic.zlogic",
        "name": "GuardInteractionLogic",
    }]
    assert "editor_data" not in editor_data


def test_scene_persistence_rejects_duplicate_names_before_editor_state_changes(tmp_path: Path) -> None:
    path = tmp_path / "duplicates.zscene"
    SceneDocument.from_dict({
        "objects": [snapshot("Same"), {**snapshot("Same"), "id": "other"}],
    }).save(path)

    with pytest.raises(ValueError, match="nomes duplicados"):
        EditorScenePersistence(tmp_path).load(path)


def test_official_editor_delegates_scene_io() -> None:
    source = (
        Path("editor/isolated_editor_main.py").read_text(encoding="utf-8")
        + Path("editor/project_workflow_controller.py").read_text(encoding="utf-8")
    )

    assert "h._scene_persistence.save(" in source
    assert "h._scene_persistence.load(Path(filename))" in source
    assert "existing_by_id =" not in source


def test_object_variables_preserved_in_snapshot_and_deepcopy(tmp_path: Path) -> None:
    """1 & 2: Variables are copied to snapshot with full deepcopy value semantics."""
    source_obj = {
        "id": "enemy_1",
        "name": "Enemy 1",
        "transform": {"position": [10.0, 20.0, 0.0], "scale": [32.0, 32.0, 1.0]},
        "variables": {
            "health": 100,
            "detection_range": 300.0,
            "attack_range": 48.0,
            "nested": {"key": "value"},
        },
    }
    snap = EditorScenePersistence._snapshot_from_object(source_obj)
    assert snap is not None
    assert "variables" in snap
    assert snap["variables"]["health"] == 100
    assert snap["variables"]["detection_range"] == 300.0
    assert snap["variables"]["attack_range"] == 48.0
    assert snap["variables"]["nested"]["key"] == "value"

    # Mutate snapshot to prove deepcopy isolation
    snap["variables"]["health"] = 50
    snap["variables"]["nested"]["key"] = "mutated"
    assert source_obj["variables"]["health"] == 100
    assert source_obj["variables"]["nested"]["key"] == "value"


def test_object_variables_round_trip(tmp_path: Path) -> None:
    """3, 4, 8 & 9: Full round-trip object -> snapshot -> object preserves types and nested structures."""
    path = tmp_path / "roundtrip.zscene"
    original_vars = {
        "health": 100,
        "is_active": False,
        "coins": 0,
        "tag_name": "",
        "scale_factor": 1.5,
        "nested_dict": {"inner": True, "count": 42},
        "tags_list": ["a", "b", "c"],
    }
    existing = {
        "format_version": 2,
        "scene_name": "RoundTrip",
        "objects": [{
            "id": "enemy_1",
            "name": "Enemy 1",
            "transform": {"position": [0.0, 0.0, 0.0], "scale": [32.0, 32.0, 1.0]},
            "variables": deepcopy(original_vars),
        }],
    }
    persistence = EditorScenePersistence(tmp_path)
    SceneDocument.from_dict(existing).save(path)

    payload, snapshots, typed = persistence.load(path)
    assert snapshots[0]["variables"] == original_vars

    saved = persistence.save(path, snapshots, payload)
    assert saved["objects"][0]["variables"] == original_vars
    assert "variables" not in saved["objects"][0].get("editor_data", {})


def test_missing_and_empty_variables(tmp_path: Path) -> None:
    """6 & 7: Missing variables remain absent; empty variables remain empty dict."""
    obj_without_vars = {
        "id": "no_vars", "name": "NoVars",
        "transform": {"position": [0.0, 0.0, 0.0], "scale": [32.0, 32.0, 1.0]},
    }
    snap1 = EditorScenePersistence._snapshot_from_object(obj_without_vars)
    assert "variables" not in snap1

    obj_with_empty_vars = {
        "id": "empty_vars", "name": "EmptyVars",
        "transform": {"position": [0.0, 0.0, 0.0], "scale": [32.0, 32.0, 1.0]},
        "variables": {},
    }
    snap2 = EditorScenePersistence._snapshot_from_object(obj_with_empty_vars)
    assert snap2.get("variables") == {}


def test_multiple_objects_isolated_variables(tmp_path: Path) -> None:
    """5: Multiple objects keep isolated variable dictionaries."""
    path = tmp_path / "multi.zscene"
    existing = {
        "format_version": 2,
        "scene_name": "Multi",
        "objects": [
            {
                "id": "e1", "name": "Enemy 1",
                "transform": {"position": [0.0, 0.0, 0.0], "scale": [32.0, 32.0, 1.0]},
                "variables": {"health": 100},
            },
            {
                "id": "e2", "name": "Enemy 2",
                "transform": {"position": [0.0, 0.0, 0.0], "scale": [32.0, 32.0, 1.0]},
                "variables": {"health": 80},
            },
        ],
    }
    persistence = EditorScenePersistence(tmp_path)
    SceneDocument.from_dict(existing).save(path)

    _, snapshots, _ = persistence.load(path)
    assert snapshots[0]["variables"]["health"] == 100
    assert snapshots[1]["variables"]["health"] == 80

    snapshots[0]["variables"]["health"] = 20
    assert snapshots[1]["variables"]["health"] == 80
