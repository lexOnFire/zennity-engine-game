from __future__ import annotations

import pytest

from editor.application import EditorState, SceneManager


def _objects() -> list[dict]:
    return [
        {"id": "floor", "name": "Chao", "x": 0.0, "y": 150.0},
        {"id": "player", "name": "Player", "x": 0.0, "y": 0.0},
    ]


def test_scene_manager_indexes_and_finds_objects() -> None:
    manager = SceneManager(_objects())

    assert manager.find("Player") is manager.objects_by_name["Player"]
    assert manager.contains("Chao")
    assert manager.find("Missing") is None


def test_scene_manager_snapshot_is_defensive_copy() -> None:
    manager = SceneManager(_objects())

    snapshot = manager.snapshot()
    snapshot[0]["name"] = "ChangedOutside"

    assert manager.contains("Chao")
    assert not manager.contains("ChangedOutside")


def test_scene_manager_rename_keeps_index_consistent() -> None:
    manager = SceneManager(_objects())

    renamed = manager.rename("Player", "Hero")

    assert renamed["name"] == "Hero"
    assert manager.find("Player") is None
    assert manager.find("Hero") is renamed


def test_scene_manager_rejects_duplicate_names() -> None:
    manager = SceneManager(_objects())

    with pytest.raises(ValueError, match="Duplicate"):
        manager.add({"id": "other", "name": "Player"})

    with pytest.raises(ValueError, match="Duplicate"):
        manager.rename("Chao", "Player")


def test_scene_manager_reset_restores_initial_scene() -> None:
    manager = SceneManager(_objects())
    manager.remove("Player")

    manager.reset()

    assert [item["name"] for item in manager.objects] == ["Chao", "Player"]


def test_editor_state_owns_selection_and_play_mode() -> None:
    state = EditorState(runtime_objects_by_name={"Player": {"name": "Player"}})

    state.select("Player")
    state.begin_play_mode()

    assert state.selected_name == "Player"
    assert state.runtime_playing is True
    assert state.runtime_objects_by_name == {}

    state.runtime_objects_by_name["Player"] = {"name": "Player"}
    state.end_play_mode()

    assert state.runtime_playing is False
    assert state.runtime_objects_by_name == {}
