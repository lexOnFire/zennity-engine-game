from types import SimpleNamespace

from editor.viewport_event_controller import ViewportEventController


def test_viewport_delete_request_removes_selected_edit_object() -> None:
    removed = []
    host = SimpleNamespace(
        _play_session=SimpleNamespace(is_running=False),
        _selected_name="Player",
        _objects_by_name={"Player": {"name": "Player"}},
        _scene_objects=SimpleNamespace(delete=removed.append),
    )

    ViewportEventController(host).delete_selected_requested({})

    assert removed == ["Player"]


def test_viewport_delete_request_is_blocked_during_play() -> None:
    removed = []
    host = SimpleNamespace(
        _play_session=SimpleNamespace(is_running=True),
        _selected_name="Player",
        _objects_by_name={"Player": {"name": "Player"}},
        _scene_objects=SimpleNamespace(delete=removed.append),
    )

    ViewportEventController(host).delete_selected_requested({})

    assert removed == []
