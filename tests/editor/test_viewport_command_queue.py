from queue import Queue

from editor.runtime.viewport_command_queue import ViewportCommandQueue


def test_command_queue_drains_available_dictionary_commands() -> None:
    source = Queue()
    source.put({"type": "play"})
    source.put("invalid")
    source.put({"type": "stop"})

    assert list(ViewportCommandQueue(source).drain()) == [
        {"type": "play"},
        {"type": "stop"},
    ]


def test_command_queue_bounds_work_per_frame_without_dropping_commands() -> None:
    source = Queue()
    for index in range(5):
        source.put({"index": index})
    commands = ViewportCommandQueue(source, maximum_per_frame=2)

    assert [item["index"] for item in commands.drain()] == [0, 1]
    assert [item["index"] for item in commands.drain()] == [2, 3]
    assert [item["index"] for item in commands.drain()] == [4]


def test_command_queue_accepts_missing_source() -> None:
    assert list(ViewportCommandQueue(None).drain()) == []

