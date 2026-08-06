"""Delegate methods that forward Inspector component toggles/actions to
self._inspector_components. Extracted from IsolatedEditorWindow to keep that
class under the release size budget (tests/editor/test_editor_window_boundaries.py) --
purely mechanical move, no behavior change.
"""
from __future__ import annotations


class InspectorComponentDelegatesMixin:
    def _toggle_renderer_component(self, checked: bool) -> None:
        self._inspector_components.toggle_renderer(checked)

    def _choose_sprite_texture(self) -> None:
        self._inspector_components.choose_sprite_texture()

    def _choose_sprite_color(self) -> None:
        self._inspector_components.choose_sprite_color()

    def _send_inspector_renderer(self, record_history: bool = True) -> None:
        self._inspector_components.send_renderer(record_history)

    def _toggle_audio_component(self, checked: bool) -> None:
        self._inspector_components.toggle_audio(checked)

    def _get_available_audio_files(self) -> list[str]:
        return self._inspector_components.available_audio_files()

    def _get_available_audio_outputs(self) -> list[str]:
        return self._inspector_components.available_audio_outputs()

    def _send_inspector_audio(self) -> None:
        self._inspector_components.send_audio()

    def _test_selected_audio(self) -> None:
        self._inspector_components.preview_audio()

    def _toggle_rigidbody_component(self, checked: bool) -> None:
        self._inspector_components.toggle_rigidbody(checked)

    def _toggle_collider_component(self, checked: bool) -> None:
        self._inspector_components.toggle_collider(checked)

    def _toggle_camera_component(self, checked: bool) -> None:
        self._inspector_components.toggle_camera(checked)

    def _send_inspector_camera(self) -> None:
        self._inspector_components.send_camera()

    def _choose_camera_color(self) -> None:
        self._inspector_components.choose_camera_color()

    def _toggle_ui_visibility(self, checked: bool) -> None:
        self._inspector_components.toggle_ui_visibility(checked)

    def _delete_ui_component(self) -> None:
        self._inspector_components.delete_ui()

    def _choose_ui_color(self) -> None:
        self._inspector_components.choose_ui_color()

    def _choose_ui_layout(self) -> None:
        self._inspector_components.choose_ui_layout()

    def _choose_ui_image(self) -> None:
        self._inspector_components.choose_ui_image()

    def _send_inspector_ui(self) -> None:
        self._inspector_components.send_ui()

    def _ensure_canvas(self) -> None:
        self._inspector_components.ensure_canvas()

    def _send_inspector_physics(self) -> None:
        self._inspector_components.send_physics()

    def _send_inspector_collider(self) -> None:
        self._inspector_components.send_collider()
