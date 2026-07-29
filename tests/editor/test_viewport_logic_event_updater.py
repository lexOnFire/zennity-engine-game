from __future__ import annotations

from types import SimpleNamespace

from editor.runtime.viewport_logic_event_updater import ViewportLogicEventUpdater


class StubAPI:
    def __init__(self) -> None:
        self.frames: list[dict[str, bool]] = []

    def begin_frame(self, state: dict[str, bool]) -> None:
        self.frames.append(state)


class StubHud:
    def __init__(self) -> None:
        self.entries: dict[str, dict] = {}

    def set_entry(self, value: dict) -> None:
        self.entries[str(value["key"])] = value

    def remove_entry(self, key: str) -> None:
        self.entries.pop(key, None)


def test_logic_event_updater_applies_instructions_and_preserves_hook_order() -> None:
    calls: list[tuple] = []
    obj = {"logic_events": [
        {"command": "play_animation", "value": "Run"},
        {"command": "set_hud", "value": {"key": "score", "text": "1"}},
        {"command": "restart_scene"},
    ]}
    api = StubAPI()
    module = SimpleNamespace(
        _zennity_update_mode="simple",
        on_instruction=lambda current_api, instruction: calls.append(("instruction", instruction["command"])),
        _zennity_update_hook=lambda current_api, dt: calls.append(("update", dt)),
    )
    hud = StubHud()
    updater = ViewportLogicEventUpdater(
        {"Player": obj}, {"Player": [("player.py", module)]}, {"Player": api}, {}, hud,
        lambda value: value, lambda *args: None, lambda *args: None, lambda event: None,
    )

    restarted = updater.update({"jump": False}, 0.25, {}, {})

    assert restarted is True
    assert obj["_current_animation_name"] == "Run"
    assert hud.entries["score"]["text"] == "1"
    assert calls == [
        ("instruction", "play_animation"),
        ("instruction", "set_hud"),
        ("instruction", "restart_scene"),
        ("update", 0.25),
    ]


def test_logic_event_updater_isolates_failed_modules_and_applies_jump() -> None:
    events: list[dict] = []
    obj = {"_jump_requested": True, "_jump_force": 500.0}
    module = SimpleNamespace(
        _zennity_update_mode="simple",
        _zennity_update_hook=lambda api, dt: (_ for _ in ()).throw(RuntimeError("boom")),
    )
    instances = {"Player": [("broken.py", module)]}
    updater = ViewportLogicEventUpdater(
        {"Player": obj}, instances, {"Player": StubAPI()}, {}, StubHud(),
        lambda value: value, lambda *args: None, lambda *args: None, events.append,
    )
    velocities: dict[str, float] = {}
    grounded = {"Player": True}

    updater.update({}, 0.1, velocities, grounded)

    assert instances["Player"] == []
    assert velocities["Player"] == -500.0
    assert grounded["Player"] is False
    assert events[0]["level"] == "ERROR"
