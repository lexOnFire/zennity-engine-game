from pathlib import Path


def test_viewport_delegates_runtime_initialization_and_spawn_discovery() -> None:
    viewport = (
        Path("editor/isolated_viewport.py").read_text(encoding="utf-8")
        + Path("editor/runtime/viewport_session.py").read_text(encoding="utf-8")
    )
    initializer = Path("editor/runtime/viewport_runtime_initializer.py").read_text(encoding="utf-8")

    assert "runtime_initializer = ViewportRuntimeInitializer(" in viewport
    assert "runtime_initializer.start(scene_blackboard_config)" in viewport
    assert "runtime_initializer.stop(active_contacts)" in viewport
    assert "runtime_initializer.start_spawned_objects()" in viewport
    assert "class ViewportRuntimeInitializer" in initializer
    assert "self.runtime_world.reset_session()" in initializer
    assert "self.initialized_ids" in initializer
    assert "self._initialize_animation(name, obj)" in initializer
    assert "self._initialize_logic(name, obj)" in initializer


def test_run_viewport_is_below_original_large_method_threshold() -> None:
    import ast

    source = (
        Path("editor/isolated_viewport.py").read_text(encoding="utf-8")
        + Path("editor/runtime/viewport_session.py").read_text(encoding="utf-8")
    )
    tree = ast.parse(source)
    run_viewport = next(
        node for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "run_viewport"
    )

    assert run_viewport.end_lineno - run_viewport.lineno + 1 < 500
