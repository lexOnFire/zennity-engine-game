from __future__ import annotations

from editor.runtime.viewport_contact_processor import ViewportContactProcessor


def collider(x: float, y: float, *, trigger: bool = False) -> dict:
    return {
        "x": x, "y": y, "w": 16.0, "h": 16.0, "active": True,
        "collider": {"type": "box", "is_trigger": trigger},
    }


def test_contact_processor_preserves_enter_and_exit_events() -> None:
    objects = {"A": collider(0, 0), "B": collider(8, 0)}
    active: dict[tuple[str, str], bool] = {}
    events: list[tuple[str, str, str]] = []
    processor = ViewportContactProcessor(objects, active, lambda *event: events.append(event))

    processor.process()
    processor.process()
    objects["B"]["x"] = 500
    processor.process()

    assert events == [
        ("A", "B", "on_collision"), ("B", "A", "on_collision"),
        ("A", "B", "on_collision_exit"), ("B", "A", "on_collision_exit"),
    ]
    assert active == {}


def test_contact_processor_preserves_trigger_events() -> None:
    objects = {"A": collider(0, 0, trigger=True), "B": collider(8, 0)}
    events: list[tuple[str, str, str]] = []
    processor = ViewportContactProcessor(objects, {}, lambda *event: events.append(event))

    processor.process()

    assert events == [("A", "B", "on_trigger"), ("B", "A", "on_trigger")]


def test_contact_processor_culls_separated_pairs() -> None:
    objects = {str(index): collider(index * 256.0, 0) for index in range(100)}
    processor = ViewportContactProcessor(objects, {}, lambda *event: None, cell_size=64.0)

    processor.process()

    assert processor.stats.possible_pairs == 4950
    assert processor.stats.candidate_pairs == 0
    assert processor.stats.culled_pairs == 4950
