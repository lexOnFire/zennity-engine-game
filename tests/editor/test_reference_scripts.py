from __future__ import annotations

from pathlib import Path

from engine.runtime.script_runtime import ScriptRuntime
from engine.runtime.script_behaviour import ScriptBehaviour


REFERENCE_SCRIPTS = [
    "examples/GettingStarted/Assets/Scripts/player_controller.py",
    "examples/GettingStarted/Assets/Scripts/auto_rotate.py",
    "examples/GettingStarted/Assets/Scripts/ping_pong_movement.py",
    "examples/GettingStarted/Assets/Scripts/click_logger.py",
]


def test_reference_scripts_define_runtime_behaviour() -> None:
    runtime = ScriptRuntime(runtime_scene=None, project_root=Path.cwd())

    for script_path in REFERENCE_SCRIPTS:
        module = runtime._load_module(Path(script_path).resolve())
        behaviour_type = runtime._find_behaviour_type(module)
        assert issubclass(behaviour_type, ScriptBehaviour)
        assert behaviour_type is not ScriptBehaviour


def test_reference_scripts_use_explicit_script_class() -> None:
    runtime = ScriptRuntime(runtime_scene=None, project_root=Path.cwd())

    for script_path in REFERENCE_SCRIPTS:
        module = runtime._load_module(Path(script_path).resolve())
        assert hasattr(module, "Script")
        assert issubclass(module.Script, ScriptBehaviour)
