from __future__ import annotations

from types import SimpleNamespace

from editor.controllers.selection_controller import EditorSelectionController
from editor.viewport_event_controller import ViewportEventController


class _Status:
    def __init__(self) -> None:
        self.messages = []

    def showMessage(self, message: str) -> None:
        self.messages.append(message)


def _host():
    obj = {"name": "Player", "x": 0.0, "y": 0.0, "w": 10.0, "h": 20.0, "rotation": 0.0}
    status = _Status()
    host = SimpleNamespace(
        _scene_snapshot=[obj], _objects_by_name={"Player": obj},
        _selected_name="Player", _runtime_playing=False,
        _drag_history_snapshot=None, inspected=[], history=[],
        _runtime_objects_by_name={}, cleared=0, refreshed=0,
        selected=[],
    )
    host._scene_controller = SimpleNamespace(select=host.selected.append)
    host._selection = EditorSelectionController(host)
    host._update_inspector = lambda name: host.inspected.append(name)
    host._record_history = lambda snapshot: host.history.append(snapshot)
    host._refresh_hierarchy = lambda: setattr(host, "refreshed", host.refreshed + 1)
    host._clear_inspector_view = lambda: setattr(host, "cleared", host.cleared + 1)
    host.statusBar = lambda: status
    return host, status


def test_transform_events_commit_one_history_entry_per_drag() -> None:
    host, _ = _host()
    controller = ViewportEventController(host)

    controller.transform({"type": "transform_begin"})
    controller.transform({"type": "transform", "name": "Player", "x": 5, "y": 7})
    controller.transform({"type": "transform_end"})

    assert (host._objects_by_name["Player"]["x"], host._objects_by_name["Player"]["y"]) == (5.0, 7.0)
    assert len(host.history) == 1
    assert host.history[0][0]["x"] == 0.0


def test_runtime_objects_refresh_only_when_membership_changes() -> None:
    host, _ = _host()
    controller = ViewportEventController(host)

    controller.runtime_objects({"objects": [{"name": "Enemy", "x": 1}]})
    controller.runtime_objects({"objects": [{"name": "Enemy", "x": 2}]})

    assert host.refreshed == 1
    assert host._runtime_objects_by_name["Enemy"]["x"] == 2


def test_selected_event_updates_inspector_and_status() -> None:
    host, status = _host()

    ViewportEventController(host).selected({"name": "Player"})

    assert host.inspected == ["Player"]
    assert status.messages == ["Viewport: Player selecionado"]


def test_tool_changed_event_activates_editor_tool_controller() -> None:
    host, _ = _host()
    activated = []
    host._tool_controller = SimpleNamespace(activate_tool=activated.append)

    ViewportEventController(host).tool_changed({"tool": "rotate"})

    assert activated == ["rotate"]
