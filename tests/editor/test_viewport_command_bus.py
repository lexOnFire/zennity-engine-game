from editor.runtime.viewport_command_bus import ViewportCommandBus


class QueueStub:
    def __init__(self): self.items = []
    def put(self, value, *args, **kwargs): self.items.append(value)
    def put_nowait(self, value): self.items.append(value)


def test_command_bus_coalesces_identical_state_but_never_scene_mutations():
    queue = QueueStub()
    bus = ViewportCommandBus(queue)

    assert bus.put({"type": "select_object", "name": "Player"}) is True
    assert bus.put({"type": "select_object", "name": "Player"}) is True
    assert bus.put({"type": "scene_snapshot", "objects": []}) is True
    assert bus.put({"type": "scene_snapshot", "objects": []}) is True

    assert [item["_seq"] for item in queue.items] == [1, 2, 3, 4]
    assert bus.stats() == {"sent": 4, "coalesced": 0, "sequence": 4}
