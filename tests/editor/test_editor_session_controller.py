from types import SimpleNamespace

from editor.editor_session_controller import EditorSessionController


class Commands:
    def __init__(self) -> None:
        self.values: list[dict] = []

    def put(self, value: dict) -> None:
        self.values.append(value)


class ViewportController:
    def __init__(self) -> None:
        self.attached = None
        self.shutdown_calls = 0

    def attach(self, process) -> None:
        self.attached = process

    def shutdown(self) -> None:
        self.shutdown_calls += 1


def _editor():
    return SimpleNamespace(
        _pending_viewport_size=None,
        _last_viewport_size_sent=None,
        _commands=Commands(),
        _viewport_controller=ViewportController(),
        _viewport_process=None,
    )


def test_resize_flush_coalesces_and_deduplicates_sizes() -> None:
    editor = _editor()
    controller = EditorSessionController(editor)

    editor._pending_viewport_size = (800, 600)
    controller.flush_viewport_resize()
    editor._pending_viewport_size = (800, 600)
    controller.flush_viewport_resize()

    assert editor._commands.values == [{"type": "viewport_size", "w": 800, "h": 600}]
    assert editor._pending_viewport_size is None


def test_process_attachment_and_shutdown_are_idempotent() -> None:
    editor = _editor()
    controller = EditorSessionController(editor)
    process = object()

    controller.attach_viewport_process(process)
    controller.shutdown()
    controller.shutdown()

    assert editor._viewport_controller.attached is process
    assert editor._viewport_process is process
    assert editor._viewport_controller.shutdown_calls == 1
