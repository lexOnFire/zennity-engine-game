from editor.runtime.viewport_play_commands import ViewportPlayCommandHandler, ViewportProcessState


def _state(**changes):
    values = dict(
        running=True, screen=object(), camera_x=0.0, camera_y=0.0,
        edit_snapshot={}, selected_name=None, playing=False, paused=False,
        velocities_y={}, grounded={}, scene_blackboard_config={},
    )
    values.update(changes)
    return ViewportProcessState(**values)


def _handler(objects, events, calls):
    return ViewportPlayCommandHandler(
        objects, {}, {}, events.append,
        lambda width, height: (width, height), lambda: 2.0,
        lambda paused: calls.append(("audio_pause", paused)),
        lambda: calls.append("audio_stop"), lambda: calls.append("physics_reset"),
        lambda: calls.append("hud_clear"), lambda config: calls.append(("logic_start", config)),
        lambda: calls.append("logic_stop"),
    )


def test_play_commands_own_session_transition_and_restore_edit_snapshot() -> None:
    objects = {"Player": {"name": "Player", "x": 1}}
    events, calls = [], []
    handler = _handler(objects, events, calls)

    state = handler.handle({"type": "play", "scene_blackboard": {"score": 0}}, _state())
    assert state.playing and not state.paused
    assert ("logic_start", {"score": 0}) in calls

    objects["Player"]["x"] = 99
    state = handler.handle({"type": "stop"}, state)
    assert not state.playing and objects["Player"]["x"] == 1
    assert [event["state"] for event in events if event["type"] == "play_state"] == ["play", "edit"]


def test_play_commands_resize_and_bound_camera_to_world_origin() -> None:
    handler = _handler({}, [], [])
    state = handler.handle({"type": "viewport_size", "w": 800, "h": 600}, _state())

    assert state.screen == (800, 600)
    assert (state.camera_x, state.camera_y) == (-200.0, -150.0)


def test_play_commands_ignore_unowned_commands() -> None:
    assert _handler({}, [], []).handle({"type": "set_tool"}, _state()) is None

