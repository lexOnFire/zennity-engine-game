from pathlib import Path

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
