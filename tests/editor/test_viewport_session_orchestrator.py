from pathlib import Path

from editor.runtime.viewport_session_orchestrator import ViewportSessionOrchestrator


def test_viewport_delegates_logic_behavior_lifecycle_and_restart() -> None:
    viewport = (
        Path("editor/isolated_viewport.py").read_text(encoding="utf-8")
        + Path("editor/runtime/viewport_session.py").read_text(encoding="utf-8")
        + Path("editor/runtime/viewport_session_lifecycle.py").read_text(encoding="utf-8")
    )
    orchestrator = Path("editor/runtime/viewport_session_orchestrator.py").read_text(encoding="utf-8")

    assert "session_orchestrator.update_logic(" in viewport
    assert "session_orchestrator.update_behaviors(" in viewport
    assert "session_orchestrator.finish_frame(" in viewport
    assert "session_orchestrator.restart(" in viewport
    assert "class ViewportSessionOrchestrator" in orchestrator
    assert "self.runtime_world.update_lifecycle(delta_time)" in orchestrator
    assert "runtime.consume_event_trace()" in orchestrator


def test_load_scene_instruction_emits_scene_change_without_old_scene_restart() -> None:
    emitted = []
    orchestrator = ViewportSessionOrchestrator(
        objects={"Player": {"name": "Player"}},
        logic_runtimes={},
        behavior_runners={},
        logic_modules={},
        logic_apis={},
        animator_controllers={},
        logic_event_bus=lambda: None,
        runtime_world=object(),
        hud_entries=object(),
        emit=emitted.append,
        play_audio=lambda *_args, **_kwargs: None,
        pause_audio=lambda _value: None,
        state_hook=lambda *_args: None,
    )
    player = {
        "logic_events": [{
            "command": "load_scene",
            "value": {"path": "Assets/Scenes/GameOver.zscene"},
        }],
    }

    restart = orchestrator._apply_logic_instructions("Player", player)

    assert restart is False
    assert emitted == [{
        "type": "load_scene",
        "scene_path": "Assets/Scenes/GameOver.zscene",
        "path": "Assets/Scenes/GameOver.zscene",
    }]
