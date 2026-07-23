from __future__ import annotations

from types import SimpleNamespace

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
    )
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


def test_stats_render_real_profiler_metrics() -> None:
    host, _ = _host()
    label = SimpleNamespace(text="", setText=lambda value: setattr(label, "text", value))
    host.profiler_label = label
    host._commands = SimpleNamespace(
        stats=lambda: {"sent": 4, "coalesced": 2}
    )

    ViewportEventController(host).stats({
        "fps": 60,
        "frame_ms": 16.67,
        "p95_frame_ms": 18.2,
        "cpu_ms": 7.5,
        "memory_mb": 128.25,
        "physics_bodies": 3,
        "objects": 8,
        "subsystems_ms": {"physics": 1.2, "render": 2.4},
    })

    assert "Frame: 16.67 ms" in label.text
    assert "P95: 18.20 ms" in label.text
    assert "Memória: 128.2 MB" in label.text
    assert "physics: 1.20 ms" in label.text
    assert "render: 2.40 ms" in label.text
