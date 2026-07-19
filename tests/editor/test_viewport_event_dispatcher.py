from __future__ import annotations

from pathlib import Path

from editor.runtime.viewport_event_dispatcher import ViewportEventDispatcher


def test_dispatcher_routes_known_event_once() -> None:
    messages = []
    dispatcher = ViewportEventDispatcher({"selected": messages.append})
    message = {"type": "selected", "name": "Player"}

    assert dispatcher.dispatch(message)
    assert messages == [message]


def test_dispatcher_ignores_unknown_event() -> None:
    dispatcher = ViewportEventDispatcher({})

    assert not dispatcher.dispatch({"type": "future_event"})


def test_event_polling_only_drains_queue_and_dispatches() -> None:
    source = Path("editor/isolated_editor_main.py").read_text(encoding="utf-8")
    polling = source.split("    def _read_viewport_events", 1)[1].split(
        "    def closeEvent", 1
    )[0]

    assert "self._viewport_events.dispatch(message)" in polling
    assert 'message.get("type")' not in polling
    assert "elif " not in polling
