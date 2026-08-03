from types import SimpleNamespace

from editor.runtime.viewport_navigation_events import ViewportNavigationEventHandler, ViewportNavigationState


class _Pygame:
    QUIT = 1
    MOUSEBUTTONDOWN = 2
    MOUSEBUTTONUP = 3
    MOUSEWHEEL = 4
    MOUSEMOTION = 5
    mouse = SimpleNamespace(get_pos=lambda: (100, 80))


class _NativeUI:
    def button_at(self, objects, position):
        return objects["Button"], {"target": "Player", "event": "jump"}


def _state():
    return ViewportNavigationState(True, False, (0, 0), 0.0, 0.0, 1.0)


def test_navigation_handler_zooms_around_mouse_position() -> None:
    handler = ViewportNavigationEventHandler(_Pygame, {}, _NativeUI(), lambda event: None, lambda x, y: (x, y))
    handled, state = handler.handle(SimpleNamespace(type=_Pygame.MOUSEWHEEL, y=1), _state(), playing=False, view_mode="scene")

    assert handled and state.zoom == 1.12
    assert round(state.camera_x, 4) == round(100 - 100 / 1.12, 4)


def test_navigation_handler_routes_game_ui_clicks() -> None:
    objects = {"Button": {"name": "Button"}, "Player": {"name": "Player"}}
    emitted = []
    handler = ViewportNavigationEventHandler(_Pygame, objects, _NativeUI(), emitted.append, lambda x, y: (x, y))
    event = SimpleNamespace(type=_Pygame.MOUSEBUTTONDOWN, button=1, pos=(20, 30))

    assert handler.handle(event, _state(), playing=True, view_mode="game")[0]
    assert objects["Player"]["logic_events"][0]["command"] == "jump"
    assert emitted[-1]["type"] == "runtime_log"
