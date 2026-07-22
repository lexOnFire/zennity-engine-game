"""Animation workspace wiring and preview state orchestration."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from engine.animation.clip_asset import animation_asset_to_clip
from editor.ui.icons import editor_icon


class AnimationWorkspaceController:
    def __init__(self, host: Any) -> None:
        self.host = host
        self._connected = False

    def connect(self) -> bool:
        if self._connected:
            return False
        h = self.host
        h.animation_new_button.clicked.connect(h._new_animation_asset)
        h.animation_open_button.clicked.connect(h._open_animation_asset_dialog)
        h.animation_save_button.clicked.connect(h._save_animation_asset)
        h.animation_save_as_button.clicked.connect(lambda: h._save_animation_asset(save_as=True))
        h.animation_duplicate_button.clicked.connect(h._duplicate_animation_asset)
        h.animation_delete_button.clicked.connect(h._delete_animation_asset)
        h.animation_apply_button.clicked.connect(h._apply_current_animation_to_selected)
        h.animation_demo_button.clicked.connect(h._run_walk_animation_demo)
        h.animation_open_demo_button.clicked.connect(
            lambda _checked=False: h._load_scene_snapshot(
                scene_path=Path.cwd() / "Assets" / "Scenes" / "AnimatorControllerDemo.zscene"
            )
        )
        h.animation_library_tree.itemDoubleClicked.connect(h._open_animation_library_item)
        h.animation_controller_combo.currentIndexChanged.connect(h._select_animation_controller)
        h.animation_new_controller_button.clicked.connect(h._new_animator_controller)
        h.animation_edit_controller_button.clicked.connect(h._edit_animator_controller)
        h.animation_play_button.clicked.connect(h._toggle_animation_preview_playback)
        h.animation_first_frame_button.clicked.connect(lambda: h._set_animation_preview_frame(0))
        h.animation_previous_frame_button.clicked.connect(
            lambda: h._set_animation_preview_frame(h._animator_preview_index - 1)
        )
        h.animation_next_frame_button.clicked.connect(
            lambda: h._set_animation_preview_frame(h._animator_preview_index + 1)
        )
        h.animation_last_frame_button.clicked.connect(
            lambda: h._set_animation_preview_frame(h._animation_frame_count() - 1)
        )
        h.animation_timeline.valueChanged.connect(h._set_animation_preview_frame)
        h.animation_add_event_button.clicked.connect(h._add_animation_event)
        h.animation_remove_event_button.clicked.connect(h._remove_animation_event)
        for signal in (
            h.animator_clip_combo.currentTextChanged,
            h.animator_sheet_combo.currentIndexChanged,
            h.animator_frame_width.valueChanged,
            h.animator_frame_height.valueChanged,
            h.animator_start_frame.valueChanged,
            h.animator_frame_count.valueChanged,
            h.animator_fps_field.valueChanged,
            h.animator_loop_field.toggled,
        ):
            signal.connect(h._mark_animation_asset_dirty)
        self._connected = True
        h._refresh_animation_library()
        h._refresh_animator_controllers()
        h._refresh_animation_timeline(h._default_animation_clip())
        h._update_animation_asset_status()
        return True

    @staticmethod
    def assets_directory() -> Path:
        return Path.cwd() / "Assets" / "Animations"

    def mark_dirty(self) -> None:
        h = self.host
        if h._updating_inspector:
            return
        h._animation_asset_dirty = True
        self.update_status()

    def update_status(self) -> None:
        h = self.host
        name = h._current_animation_asset_path.name if h._current_animation_asset_path else h._animation_draft_name
        if h._current_animation_asset_path is None:
            suffix = "  •  ainda não salvo"
        elif h._animation_asset_dirty:
            suffix = "  •  alterações não salvas"
        else:
            suffix = "  •  salvo"
        h.animation_asset_label.setText(name + suffix)
        state = "dirty" if h._animation_asset_dirty or h._current_animation_asset_path is None else "saved"
        if h.animation_asset_label.property("uiState") != state:
            h.animation_asset_label.setProperty("uiState", state)
            h.animation_asset_label.style().unpolish(h.animation_asset_label)
            h.animation_asset_label.style().polish(h.animation_asset_label)

    def frame_count(self) -> int:
        return max(1, int(self.host.animator_frame_count.value()))

    def refresh_timeline(self, clip: dict) -> None:
        h = self.host
        frames = clip.get("frames")
        count = max(1, len(frames) if isinstance(frames, list) and frames else int(clip.get("frame_count", 1)))
        h.animation_timeline.blockSignals(True)
        h.animation_timeline.setRange(0, count - 1)
        h.animation_timeline.setValue(min(h._animator_preview_index, count - 1))
        h.animation_timeline.blockSignals(False)
        h.animation_frame_label.setText(
            f"Frame {min(h._animator_preview_index, count - 1) + 1} / {count}"
        )

    def set_preview_frame(self, index: int) -> None:
        h = self.host
        count = self.frame_count()
        h._animator_preview_index = max(0, min(int(index), count - 1))
        h.animation_timeline.blockSignals(True)
        h.animation_timeline.setValue(h._animator_preview_index)
        h.animation_timeline.blockSignals(False)
        h.animation_frame_label.setText(f"Frame {h._animator_preview_index + 1} / {count}")
        clip = animation_asset_to_clip(h._animation_asset_from_editor())
        h._update_animation_preview(clip, h._animator_preview_index)

    def toggle_preview(self) -> None:
        h = self.host
        h._animation_preview_playing = not h._animation_preview_playing
        h.animation_play_button.setIcon(
            editor_icon("pause" if h._animation_preview_playing else "play")
        )
