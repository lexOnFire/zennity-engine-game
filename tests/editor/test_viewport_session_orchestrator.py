from pathlib import Path


def test_viewport_delegates_logic_behavior_lifecycle_and_restart() -> None:
    viewport = (\n        Path("editor/isolated_viewport.py").read_text(encoding="utf-8")\n        + Path("editor/runtime/viewport_session.py").read_text(encoding="utf-8")\n    )
    orchestrator = Path("editor/runtime/viewport_session_orchestrator.py").read_text(encoding="utf-8")

    assert "session_orchestrator.update_logic(" in viewport
    assert "session_orchestrator.update_behaviors(" in viewport
    assert "session_orchestrator.finish_frame(" in viewport
    assert "session_orchestrator.restart(" in viewport
    assert "class ViewportSessionOrchestrator" in orchestrator
    assert "self.runtime_world.update_lifecycle(delta_time)" in orchestrator
    assert "runtime.consume_event_trace()" in orchestrator
