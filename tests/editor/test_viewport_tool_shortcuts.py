from types import SimpleNamespace

from editor.runtime.viewport_tool_shortcuts import ViewportToolShortcutHandler


class _Pygame:
    KEYDOWN = 1
    KEYUP = 2
    K_q = 10
    K_w = 11
    K_e = 12
    K_r = 13


def test_viewport_shortcuts_select_transform_tools_in_edit_scene_mode() -> None:
    emitted = []
    handler = ViewportToolShortcutHandler(_Pygame, emitted.append)

    assert handler.handle(
        SimpleNamespace(type=_Pygame.KEYDOWN, key=_Pygame.K_w),
        playing=False,
        view_mode="scene",
    ) == "move"
    assert emitted == [{"type": "tool_changed", "tool": "move"}]


def test_viewport_shortcuts_do_not_steal_runtime_or_game_input() -> None:
    emitted = []
    handler = ViewportToolShortcutHandler(_Pygame, emitted.append)
    event = SimpleNamespace(type=_Pygame.KEYDOWN, key=_Pygame.K_r)

    assert handler.handle(event, playing=True, view_mode="scene") is None
    assert handler.handle(event, playing=False, view_mode="game") is None
    assert emitted == []
