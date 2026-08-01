from editor.runtime.viewport_control_commands import (
    ViewportAudioCommandHandler,
    ViewportControlCommandHandler,
    ViewportControlSettings,
)


def test_control_commands_validate_tools_modes_and_snap_values() -> None:
    keys = {"left": False, "jump": False}
    handler = ViewportControlCommandHandler(keys)
    settings = ViewportControlSettings("select", "scene", False, 16.0, 15.0)

    settings = handler.handle({"type": "set_tool", "tool": "MOVE"}, settings)
    settings = handler.handle({"type": "set_view_mode", "mode": "game"}, settings)
    settings = handler.handle({"type": "set_snap", "enabled": True, "size": 0, "angle": -1}, settings)

    assert settings == ViewportControlSettings("move", "game", True, 0.01, 0.01)


def test_control_commands_update_forwarded_input_in_place() -> None:
    keys = {"left": False, "jump": True}
    handler = ViewportControlCommandHandler(keys)
    settings = ViewportControlSettings("select", "scene", False, 16.0, 15.0)

    assert handler.handle({"type": "runtime_input", "keys": {"left": True}}, settings) == settings
    assert keys == {"left": True, "jump": False}
    assert handler.handle({"type": "play"}, settings) is None


def test_audio_commands_route_preview_without_owning_play_state() -> None:
    calls = []
    handler = ViewportAudioCommandHandler(
        {}, {}, {}, calls.append, lambda: calls.append("start"),
        lambda: calls.append("stop"), lambda *args: calls.append(args),
        lambda device: calls.append(("device", device)),
    )

    assert handler.handle({"type": "preview_audio", "path": "tone.wav", "volume": 0.5})
    assert calls == [("device", ""), ("__preview__", "tone.wav", 0.5, False)]
    assert not handler.handle({"type": "play"})
