from pathlib import Path
from types import SimpleNamespace

import pytest

from editor.editor_bootstrap_controller import EditorBootstrapController


def test_configuration_requires_composition(tmp_path: Path) -> None:
    controller = EditorBootstrapController(SimpleNamespace(), tmp_path)

    with pytest.raises(RuntimeError, match="composed"):
        controller.configure()


def test_viewport_handler_map_is_complete(tmp_path: Path) -> None:
    handler = lambda message: message
    host = SimpleNamespace(
        _handle_selected_event=handler,
        _handle_transform_event=handler,
        _handle_play_state_event=handler,
        _handle_scene_snapshot_event=handler,
        _handle_runtime_objects_event=handler,
        _handle_viewport_mode_event=handler,
        _handle_script_log_event=handler,
        _handle_logic_trace_event=handler,
        _handle_animator_state_event=handler,
        _handle_animation_event=handler,
        _handle_attach_script_event=handler,
        _handle_stats_event=handler,
    )
    handlers = EditorBootstrapController(host, tmp_path)._viewport_handlers()

    assert set(handlers) == {
        "selected", "transform_begin", "transform_end", "transform", "play_state",
        "scene_snapshot", "runtime_objects", "viewport_mode", "script_log",
        "logic_trace", "logic_trace_clear", "animator_state", "animation_event",
        "attach_script", "stats",
    }
