from __future__ import annotations

import pytest

from editor.application.commands import (
    AddObjectCommand,
    CommandHistory,
    RemoveObjectCommand,
    RenameObjectCommand,
)
from editor.application.scene_manager import SceneManager


def test_history_executes_undoes_and_redoes_rename() -> None:
    scene = SceneManager([{"name": "Player"}])
    history = CommandHistory()

    history.execute(RenameObjectCommand(scene, "Player", "Hero"))
    assert scene.contains("Hero")
    assert not scene.contains("Player")

    assert history.undo()
    assert scene.contains("Player")

    assert history.redo()
    assert scene.contains("Hero")


def test_new_command_clears_redo_stack() -> None:
    scene = SceneManager([{"name": "Player"}])
    history = CommandHistory()
    history.execute(RenameObjectCommand(scene, "Player", "Hero"))
    history.undo()

    history.execute(AddObjectCommand(scene, {"name": "Camera"}))

    assert not history.redo()
    assert scene.contains("Camera")


def test_remove_command_restores_removed_object() -> None:
    scene = SceneManager([{"name": "Player", "x": 12}])
    history = CommandHistory()

    history.execute(RemoveObjectCommand(scene, "Player"))
    assert not scene.contains("Player")

    history.undo()
    assert scene.find("Player") == {"name": "Player", "x": 12}


def test_duplicate_rename_keeps_history_clean() -> None:
    scene = SceneManager([{"name": "Player"}, {"name": "Camera"}])
    history = CommandHistory()

    with pytest.raises(ValueError):
        history.execute(RenameObjectCommand(scene, "Player", "Camera"))

    assert history.undo_stack == []
    assert history.redo_stack == []
