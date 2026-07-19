from __future__ import annotations

from pathlib import Path

from editor.runtime.scene_selection_controller import SceneSelectionController


class RecordingCommands:
    def __init__(self) -> None:
        self.messages = []

    def put(self, message) -> bool:
        self.messages.append(message)
        return True


def test_snapshot_is_detached_before_async_publish() -> None:
    commands = RecordingCommands()
    controller = SceneSelectionController(commands)
    objects = [{"name": "Player", "transform": {"x": 10}}]

    controller.publish_snapshot(objects)
    objects[0]["transform"]["x"] = 99

    assert commands.messages == [
        {"type": "scene_snapshot", "objects": [{"name": "Player", "transform": {"x": 10}}]}
    ]


def test_selection_uses_single_protocol_boundary() -> None:
    commands = RecordingCommands()
    controller = SceneSelectionController(commands)

    controller.select("Player")
    controller.select(None)

    assert commands.messages == [
        {"type": "select_object", "name": "Player"},
        {"type": "select_object", "name": None},
    ]


def test_isolated_editor_routes_scene_and_selection_through_controller() -> None:
    source = Path("editor/isolated_editor_main.py").read_text(encoding="utf-8")

    assert 'self._commands.put({"type": "scene_snapshot"' not in source
    assert 'self._commands.put({"type": "select_object"' not in source
    assert "self._scene_controller.publish_snapshot" in source
    assert "self._scene_controller.select" in source
