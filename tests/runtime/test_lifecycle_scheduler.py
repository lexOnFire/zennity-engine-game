from engine.runtime.lifecycle import RuntimeLifecycleScheduler


class _Component:
    enabled = True
    game_object = None

    def __init__(self, name, events, scheduler=None):
        self.name, self.events, self.scheduler = name, events, scheduler

    def on_runtime_start(self): self.events.append((self.name, "start"))
    def on_runtime_update(self, dt): self.events.append((self.name, "update", dt))
    def on_runtime_late_update(self, dt): self.events.append((self.name, "late", dt))
    def on_runtime_stop(self): self.events.append((self.name, "stop"))


def test_scheduler_preserves_order_and_reverses_stop():
    events = []
    scheduler = RuntimeLifecycleScheduler()
    scheduler.start([_Component("a", events), _Component("b", events)])
    scheduler.update(0.25)
    scheduler.late_update(0.25)
    scheduler.stop()
    assert events == [
        ("a", "start"), ("b", "start"),
        ("a", "update", 0.25), ("b", "update", 0.25),
        ("a", "late", 0.25), ("b", "late", 0.25),
        ("b", "stop"), ("a", "stop"),
    ]


def test_scheduler_defers_removal_until_dispatch_finishes():
    events = []
    scheduler = RuntimeLifecycleScheduler()
    first = _Component("a", events)
    second = _Component("b", events)
    original = first.on_runtime_update
    def update(dt):
        original(dt)
        scheduler.unregister(second)
    first.on_runtime_update = update
    scheduler.start([first, second])
    scheduler.update(1.0)
    scheduler.update(2.0)
    assert ("b", "update", 1.0) not in events
    assert ("b", "update", 2.0) not in events
