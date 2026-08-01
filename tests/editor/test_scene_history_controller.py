from __future__ import annotations

from types import SimpleNamespace

from editor.runtime.scene_history import SceneHistory
from editor.scene_history_controller import SceneHistoryController


class _SceneBridge:
    def __init__(self) -> None:
        self.snapshots = []
        self.selected = []

    def publish_snapshot(self, snapshot) -> None:
        self.snapshots.append(snapshot)

    def select(self, name: str) -> None:
        self.selected.append(name)


def _host():
    obj = {"id": "p", "name": "Player", "x": 0.0}
    bridge = _SceneBridge()
    host = SimpleNamespace(
        _scene_snapshot=[obj], _objects_by_name={"Player": obj},
        _selected_name="Player", _scene_history=SceneHistory(),
        _scene_controller=bridge, refreshed=0, inspected=[], cleared=0,
    )
    host._refresh_hierarchy = lambda: setattr(host, "refreshed", host.refreshed + 1)
    host._update_inspector = lambda name: host.inspected.append(name)
    host._clear_inspector_view = lambda: setattr(host, "cleared", host.cleared + 1)
    return host, bridge


def test_history_controller_undo_redo_restores_and_publishes_scene() -> None:
    host, bridge = _host()
    controller = SceneHistoryController(host)
    controller.record()
    host._scene_snapshot[0]["x"] = 8.0

    assert controller.undo() is True
    assert host._scene_snapshot[0]["x"] == 0.0
    assert controller.redo() is True
    assert host._scene_snapshot[0]["x"] == 8.0
    assert len(bridge.snapshots) == 2
    assert bridge.selected == ["Player", "Player"]


def test_history_controller_clears_invalid_selection_on_restore() -> None:
    host, _ = _host()

    SceneHistoryController(host).restore([{"id": "e", "name": "Enemy"}])

    assert host._selected_name is None
    assert host._objects_by_name == {"Enemy": {"id": "e", "name": "Enemy"}}
    assert host.cleared == 1


def test_history_controller_reports_empty_undo_redo() -> None:
    host, _ = _host()
    controller = SceneHistoryController(host)

    assert controller.undo() is False
    assert controller.redo() is False
