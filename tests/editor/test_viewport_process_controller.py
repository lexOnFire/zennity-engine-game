from __future__ import annotations

from editor.runtime.viewport_process_controller import ViewportProcessController


class FakeQueue:
    def __init__(self) -> None:
        self.items = []

    def put_nowait(self, item) -> None:
        self.items.append(item)


class FakeProcess:
    def __init__(self, *, target=None, args=(), name="") -> None:
        self.target = target
        self.args = args
        self.name = name
        self.started = False
        self.alive = False
        self.join_timeouts = []
        self.terminated = False

    def start(self) -> None:
        self.started = True
        self.alive = True

    def is_alive(self) -> bool:
        return self.alive

    def join(self, timeout=None) -> None:
        self.join_timeouts.append(timeout)

    def terminate(self) -> None:
        self.terminated = True
        self.alive = False


class FakeContext:
    def __init__(self) -> None:
        self.queues = []
        self.processes = []

    def Queue(self):
        queue = FakeQueue()
        self.queues.append(queue)
        return queue

    def Process(self, **kwargs):
        process = FakeProcess(**kwargs)
        self.processes.append(process)
        return process


def test_controller_creates_queues_and_starts_process() -> None:
    context = FakeContext()
    controller = ViewportProcessController.create(context)
    target = lambda: None

    process = controller.start(target, (1, 2), name="Viewport")

    assert len(context.queues) == 2
    assert process.started
    assert process.target is target
    assert process.args == (1, 2)
    assert process.name == "Viewport"


def test_shutdown_requests_graceful_exit_then_forces_stuck_process() -> None:
    queue = FakeQueue()
    process = FakeProcess()
    process.alive = True
    controller = ViewportProcessController.from_queues(queue, FakeQueue(), process)

    controller.shutdown()

    assert queue.items[0]["type"] == "shutdown"
    assert process.join_timeouts == [1.5, 2.0]
    assert process.terminated


def test_shutdown_is_idempotent() -> None:
    queue = FakeQueue()
    controller = ViewportProcessController.from_queues(queue, FakeQueue())

    controller.shutdown()
    controller.shutdown()

    assert [item["type"] for item in queue.items] == ["shutdown"]
