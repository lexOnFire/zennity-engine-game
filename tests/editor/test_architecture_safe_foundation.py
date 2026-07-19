from __future__ import annotations

from queue import Queue

import pytest

from editor.controllers.play_mode import PlayModeController
from editor.controllers.viewport_process import ViewportProcessController
from editor.core.scene_document import SceneDocument
from editor.entrypoints import OFFICIAL_ENTRYPOINT, supported_entrypoints


class _Process:
    def __init__(self) -> None:
        self.joined = []
        self.terminated = False

    def join(self, timeout=None) -> None:
        self.joined.append(timeout)

    def is_alive(self) -> bool:
        return False

    def terminate(self) -> None:
        self.terminated = True


def test_official_entrypoint_is_explicit() -> None:
    assert OFFICIAL_ENTRYPOINT.module == "editor.phase1_main"
    assert OFFICIAL_ENTRYPOINT.status == "official"
    assert len([entry for entry in supported_entrypoints() if entry.status == "official"]) == 1


def test_scene_document_round_trip_and_indexes_are_stable() -> None:
    source = {"format_version": 2, "scene_name": "Level", "objects": [{"id": "a", "name": "Player", "x": 1}], "custom": 7}
    document = SceneDocument.from_mapping(source)
    assert document.find_by_id("a") is document.find_by_name("Player")
    document.rename("a", "Hero")
    assert document.find_by_name("Player") is None
    assert document.to_mapping()["custom"] == 7
    assert document.to_mapping()["objects"][0]["name"] == "Hero"


def test_scene_document_rejects_duplicate_identity() -> None:
    with pytest.raises(ValueError):
        SceneDocument(objects=[{"id": "a", "name": "One"}, {"id": "a", "name": "Two"}])
    with pytest.raises(ValueError):
        SceneDocument(objects=[{"id": "a", "name": "One"}, {"id": "b", "name": "One"}])


def test_viewport_controller_coalesces_state_and_drains_events() -> None:
    commands, events = Queue(), Queue()
    controller = ViewportProcessController(_Process(), commands, events)
    assert controller.send("set_tool", tool="move")
    assert not controller.send("set_tool", tool="move")
    events.put({"type": "selected", "name": "Player"})
    assert list(controller.drain_events()) == [{"type": "selected", "name": "Player"}]
    assert controller.stats().commands_coalesced == 1


def test_play_controller_restores_edit_snapshot_after_runtime_snapshot() -> None:
    viewport = ViewportProcessController(_Process(), Queue(), Queue())
    play = PlayModeController(viewport)
    original = [{"id": "p", "name": "Player", "x": 0}]
    play.play(original, "Player")
    play.stop()
    result = play.accept_runtime_snapshot([{"id": "p", "name": "Player", "x": 99}])
    assert result.objects == original
    assert result.selected_name == "Player"
