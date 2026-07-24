from __future__ import annotations

import numpy as np

from editor.viewport.scene_view_polish import SceneViewPolishState, focus_selected_camera_position


class _Transform:
    def __init__(self) -> None:
        self.position = np.array([120.0, -32.0, 0.0], dtype=np.float32)


class _Object:
    def __init__(self) -> None:
        self.transform = _Transform()


def test_scene_view_polish_toolbar_state_defaults() -> None:
    state = SceneViewPolishState()

    assert state.toolbar_state() == {
        "tool": "select",
        "grid_visible": True,
        "gizmos_visible": True,
        "overlays_visible": True,
        "selection_outline_visible": True,
        "grid_size": 32,
        "view_mode": "scene",
        "hidden_gizmo_types": [],
    }


def test_scene_view_polish_toggles_are_explicit() -> None:
    state = SceneViewPolishState()

    state.set_grid_visible(False)
    state.set_gizmos_visible(False)
    state.set_overlays_visible(False)
    state.set_selection_outline_visible(False)
    state.set_grid_size(8)
    state.set_active_tool("Move")

    snapshot = state.toolbar_state()
    assert snapshot["grid_visible"] is False
    assert snapshot["gizmos_visible"] is False
    assert snapshot["overlays_visible"] is False
    assert snapshot["selection_outline_visible"] is False
    assert snapshot["grid_size"] == 8
    assert snapshot["tool"] == "move"


def test_scene_view_polish_gizmos_hidden_in_play_and_game_view() -> None:
    state = SceneViewPolishState()

    assert state.should_draw_gizmo("Camera")
    assert not state.should_draw_gizmo("Camera", is_playing=True)

    state.set_view_mode("game")
    assert state.is_game_view()
    assert not state.should_draw_gizmo("Camera")


def test_scene_view_polish_can_hide_gizmo_by_type() -> None:
    state = SceneViewPolishState()

    state.hide_gizmo_type("AudioSource")

    assert not state.should_draw_gizmo("AudioSource")
    assert state.should_draw_gizmo("Camera")
    assert state.toolbar_state()["hidden_gizmo_types"] == ["AudioSource"]

    state.show_gizmo_type("AudioSource")
    assert state.should_draw_gizmo("AudioSource")


def test_focus_selected_camera_position_is_safe() -> None:
    assert focus_selected_camera_position(None) is None
    assert focus_selected_camera_position(object()) is None
    assert focus_selected_camera_position(_Object()) == (120.0, -32.0)
