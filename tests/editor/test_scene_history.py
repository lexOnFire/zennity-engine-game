from editor.runtime.scene_history import SceneHistory


def _scene(count: int) -> list[dict]:
    return [
        {"id": str(index), "name": f"Object {index}", "x": float(index), "payload": "x" * 1000}
        for index in range(count)
    ]


def test_history_retains_only_changed_objects() -> None:
    history = SceneHistory()
    scene = _scene(100)
    history.begin(scene)
    scene[50]["x"] = 999.0

    restored = history.undo(scene)

    assert restored is not None
    assert restored[50]["x"] == 50.0
    assert history.snapshot().changed_objects == 1
    assert history.snapshot().retained_bytes < 10_000


def test_history_preserves_create_delete_and_order() -> None:
    history = SceneHistory()
    original = _scene(3)
    changed = [original[2], original[0], {"id": "new", "name": "New", "x": 4.0}]
    history.commit(original, changed)

    undone = history.undo(changed)
    redone = history.redo(undone)

    assert [item["id"] for item in undone] == ["0", "1", "2"]
    assert [item["id"] for item in redone] == ["2", "0", "new"]


def test_history_evicts_oldest_deltas_to_respect_memory_budget() -> None:
    history = SceneHistory(max_commands=100, max_bytes=2500)
    scene = _scene(1)
    for index in range(10):
        history.begin(scene)
        scene[0]["payload"] = str(index) * 1000

    history.undo(scene)
    stats = history.snapshot()

    assert stats.retained_bytes <= 2500
    assert stats.evicted_entries > 0


def test_history_exposes_available_undo_and_redo_transitions() -> None:
    history = SceneHistory()
    scene = _scene(1)

    assert history.can_undo is False
    assert history.can_redo is False

    history.begin(scene)
    assert history.can_undo is True

    scene[0]["x"] = 10.0
    restored = history.undo(scene)
    assert restored is not None
    assert history.can_undo is False
    assert history.can_redo is True

    history.redo(restored)
    assert history.can_undo is True
    assert history.can_redo is False
