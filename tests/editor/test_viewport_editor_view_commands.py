from editor.runtime.viewport_editor_view_commands import (
    ViewportEditorViewCommandHandler,
    ViewportEditorViewState,
)


def test_toggle_grid_flips_visibility_without_moving_camera() -> None:
    handler = ViewportEditorViewCommandHandler({}, lambda: (800, 600))
    state = ViewportEditorViewState("Player", 10.0, 20.0, 2.0, True)

    off = handler.handle({"type": "toggle_grid"}, state)
    on = handler.handle({"type": "toggle_grid"}, off)

    assert off == ViewportEditorViewState("Player", 10.0, 20.0, 2.0, False)
    assert on == state


def test_focus_selected_centers_camera_on_selected_object() -> None:
    objects = {"Player": {"x": 500.0, "y": 360.0}}
    handler = ViewportEditorViewCommandHandler(objects, lambda: (800, 600))
    state = ViewportEditorViewState("Player", 0.0, 0.0, 2.0, True)

    focused = handler.handle({"type": "focus_selected"}, state)

    assert focused == ViewportEditorViewState("Player", 300.0, 210.0, 2.0, True)


def test_focus_selected_without_selection_is_handled_but_noop() -> None:
    handler = ViewportEditorViewCommandHandler({}, lambda: (800, 600))
    state = ViewportEditorViewState(None, 10.0, 20.0, 1.0, False)

    assert handler.handle({"type": "focus_selected"}, state) == state
    assert handler.handle({"type": "unknown"}, state) is None
