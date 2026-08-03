from types import SimpleNamespace

from editor.runtime.viewport_transform_events import ViewportTransformEventHandler, ViewportTransformState


class _Key:
    @staticmethod
    def get_mods():
        return 0


class _Pygame:
    MOUSEBUTTONDOWN = 1
    MOUSEBUTTONUP = 2
    MOUSEMOTION = 3
    KMOD_ALT = 4
    KMOD_SHIFT = 8
    key = _Key()


def test_transform_handler_selects_and_moves_without_render_loop_state() -> None:
    objects = {"Player": {"name": "Player", "x": 0.0, "y": 0.0, "w": 20.0, "h": 20.0, "rotation": 0.0}}
    emitted = []
    handler = ViewportTransformEventHandler(_Pygame, objects, emitted.append, lambda x, y: (x, y))
    state = ViewportTransformState(False, None, (0.0, 0.0))

    down = SimpleNamespace(type=_Pygame.MOUSEBUTTONDOWN, button=1, pos=(0, 0))
    handled, state = handler.handle(
        down, state, playing=False, view_mode="scene", active_tool="move", zoom=1.0,
        snap_enabled=False, snap_size=16.0, snap_angle=15.0,
    )
    motion = SimpleNamespace(type=_Pygame.MOUSEMOTION, pos=(12, 7))
    handled, state = handler.handle(
        motion, state, playing=False, view_mode="scene", active_tool="move", zoom=1.0,
        snap_enabled=False, snap_size=16.0, snap_angle=15.0,
    )

    assert handled and state.selected_name == "Player"
    assert (objects["Player"]["x"], objects["Player"]["y"]) == (12.0, 7.0)
    assert [event["type"] for event in emitted][:2] == ["selected", "transform_begin"]


def test_transform_handler_snaps_rotation() -> None:
    objects = {"Player": {"name": "Player", "x": 0.0, "y": 0.0, "w": 20.0, "h": 20.0, "rotation": 0.0}}
    handler = ViewportTransformEventHandler(_Pygame, objects, lambda event: None, lambda x, y: (x, y))
    state = ViewportTransformState(True, "Player", (0.0, 0.0), dict(objects["Player"]))
    event = SimpleNamespace(type=_Pygame.MOUSEMOTION, pos=(10, 8))

    handler.handle(
        event, state, playing=False, view_mode="scene", active_tool="rotate", zoom=1.0,
        snap_enabled=True, snap_size=16.0, snap_angle=15.0,
    )
    assert objects["Player"]["rotation"] == 45.0


def test_transform_handler_moves_only_selected_gizmo_axis() -> None:
    objects = {"Player": {"name": "Player", "x": 0.0, "y": 0.0, "w": 20.0, "h": 20.0, "rotation": 0.0}}
    handler = ViewportTransformEventHandler(_Pygame, objects, lambda event: None, lambda x, y: (x, y))
    state = ViewportTransformState(False, "Player", (0.0, 0.0))

    down = SimpleNamespace(type=_Pygame.MOUSEBUTTONDOWN, button=1, pos=(92, 0))
    handled, state = handler.handle(
        down, state, playing=False, view_mode="scene", active_tool="move", zoom=1.0,
        snap_enabled=False, snap_size=16.0, snap_angle=15.0,
    )
    motion = SimpleNamespace(type=_Pygame.MOUSEMOTION, pos=(132, 40))
    handled, state = handler.handle(
        motion, state, playing=False, view_mode="scene", active_tool="move", zoom=1.0,
        snap_enabled=False, snap_size=16.0, snap_angle=15.0,
    )

    assert handled and state.move_axis == "x"
    assert (objects["Player"]["x"], objects["Player"]["y"]) == (40.0, 0.0)


def test_transform_handler_scales_from_body_with_snap() -> None:
    objects = {"Player": {"name": "Player", "x": 0.0, "y": 0.0, "w": 20.0, "h": 20.0, "rotation": 0.0}}
    handler = ViewportTransformEventHandler(_Pygame, objects, lambda event: None, lambda x, y: (x, y))
    state = ViewportTransformState(False, None, (0.0, 0.0))

    down = SimpleNamespace(type=_Pygame.MOUSEBUTTONDOWN, button=1, pos=(0, 0))
    handled, state = handler.handle(
        down, state, playing=False, view_mode="scene", active_tool="scale", zoom=1.0,
        snap_enabled=True, snap_size=16.0, snap_angle=15.0,
    )
    motion = SimpleNamespace(type=_Pygame.MOUSEMOTION, pos=(21, 30))
    handled, state = handler.handle(
        motion, state, playing=False, view_mode="scene", active_tool="scale", zoom=1.0,
        snap_enabled=True, snap_size=16.0, snap_angle=15.0,
    )

    assert handled and state.drag_handle == 8
    assert (objects["Player"]["w"], objects["Player"]["h"]) == (64.0, 80.0)


def test_locked_object_remains_selectable_but_cannot_be_transformed() -> None:
    objects = {"Floor": {
        "name": "Floor", "x": 0.0, "y": 0.0, "w": 100.0, "h": 20.0,
        "rotation": 0.0, "editor_locked": True,
    }}
    emitted = []
    handler = ViewportTransformEventHandler(_Pygame, objects, emitted.append, lambda x, y: (x, y))
    state = ViewportTransformState(False, None, (0.0, 0.0))

    down = SimpleNamespace(type=_Pygame.MOUSEBUTTONDOWN, button=1, pos=(0, 0))
    _, state = handler.handle(
        down, state, playing=False, view_mode="scene", active_tool="move", zoom=1.0,
        snap_enabled=False, snap_size=16.0, snap_angle=15.0,
    )
    motion = SimpleNamespace(type=_Pygame.MOUSEMOTION, pos=(40, 40))
    handled, state = handler.handle(
        motion, state, playing=False, view_mode="scene", active_tool="move", zoom=1.0,
        snap_enabled=False, snap_size=16.0, snap_angle=15.0,
    )

    assert state.selected_name == "Floor"
    assert state.dragging is False
    assert handled is False
    assert (objects["Floor"]["x"], objects["Floor"]["y"]) == (0.0, 0.0)
    assert emitted == [{"type": "selected", "name": "Floor"}]


def test_locked_background_does_not_capture_click_of_overlapping_unlocked_object() -> None:
    objects = {
        "cenario": {
            "name": "cenario", "x": 0.0, "y": 0.0, "w": 1000.0, "h": 1000.0,
            "rotation": 0.0, "render_layer": "Background", "sort_order": -10, "editor_locked": True,
        },
        "Player": {
            "name": "Player", "x": 0.0, "y": 0.0, "w": 40.0, "h": 40.0,
            "rotation": 0.0, "render_layer": "Default", "sort_order": 0, "editor_locked": False,
        },
    }
    emitted = []
    handler = ViewportTransformEventHandler(_Pygame, objects, emitted.append, lambda x, y: (x, y))
    state = ViewportTransformState(False, None, (0.0, 0.0))

    down = SimpleNamespace(type=_Pygame.MOUSEBUTTONDOWN, button=1, pos=(0, 0))
    handled, state = handler.handle(
        down, state, playing=False, view_mode="scene", active_tool="move", zoom=1.0,
        snap_enabled=False, snap_size=16.0, snap_angle=15.0,
    )

    assert state.selected_name == "Player"
    assert state.dragging is True
    assert emitted[0] == {"type": "selected", "name": "Player"}
    assert emitted[1] == {"type": "transform_begin", "name": "Player"}


def test_hit_testing_respects_sort_order_and_render_layer() -> None:
    objects = {
        "BackObj": {
            "name": "BackObj", "x": 0.0, "y": 0.0, "w": 100.0, "h": 100.0,
            "rotation": 0.0, "render_layer": "Default", "sort_order": 0,
        },
        "FrontObj": {
            "name": "FrontObj", "x": 0.0, "y": 0.0, "w": 100.0, "h": 100.0,
            "rotation": 0.0, "render_layer": "Default", "sort_order": 5,
        },
    }
    emitted = []
    handler = ViewportTransformEventHandler(_Pygame, objects, emitted.append, lambda x, y: (x, y))
    state = ViewportTransformState(False, None, (0.0, 0.0))

    down = SimpleNamespace(type=_Pygame.MOUSEBUTTONDOWN, button=1, pos=(0, 0))
    handler.handle(
        down, state, playing=False, view_mode="scene", active_tool="select", zoom=1.0,
        snap_enabled=False, snap_size=16.0, snap_angle=15.0,
    )

    assert state.selected_name == "FrontObj"


def test_clicking_only_locked_background_selects_it_without_drag() -> None:
    objects = {
        "cenario": {
            "name": "cenario", "x": 0.0, "y": 0.0, "w": 1000.0, "h": 1000.0,
            "rotation": 0.0, "render_layer": "Background", "sort_order": -10, "editor_locked": True,
        },
        "Player": {
            "name": "Player", "x": 0.0, "y": 0.0, "w": 40.0, "h": 40.0,
            "rotation": 0.0, "render_layer": "Default", "sort_order": 0, "editor_locked": False,
        },
    }
    emitted = []
    handler = ViewportTransformEventHandler(_Pygame, objects, emitted.append, lambda x, y: (x, y))
    state = ViewportTransformState(False, None, (0.0, 0.0))

    down = SimpleNamespace(type=_Pygame.MOUSEBUTTONDOWN, button=1, pos=(400, 400))
    handler.handle(
        down, state, playing=False, view_mode="scene", active_tool="move", zoom=1.0,
        snap_enabled=False, snap_size=16.0, snap_angle=15.0,
    )

    assert state.selected_name == "cenario"
    assert state.dragging is False
    assert emitted == [{"type": "selected", "name": "cenario"}]

