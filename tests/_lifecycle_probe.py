"""Shared lifecycle snapshot helpers for the PHASE 9.5B Stage 3 runtime tests.

Lives in ``tests/`` rather than ``tests/runtime/`` because ``tests`` is a package
and ``tests/runtime`` is not, so this is importable from every runtime and
integration test without adding a package marker that would change how pytest
names those modules.
"""

from __future__ import annotations

import threading
from pathlib import Path

from editor_legacy.editor_2d import Editor2DScene
from engine.game_object import GameObject
from engine.logic.animation_event_dispatch import _animation_event_handlers
from engine.logic.physics_event_dispatch import _physics_event_handlers
from engine.runtime.ui_event_dispatcher import get_ui_event_dispatcher
from engine.ui.data_binding import UIDataBindingManager
from engine.ui.runtime_service import UIRuntimeService
from engine.ui.ui_manager import UIManager

BASELINE_PATH = (
    Path(__file__).resolve().parent / "fixtures" / "stage3" / "lifecycle_baseline.json"
)

#: Threads that legitimately live for the whole process.  Anything else present
#: after a Stop is a session thread that was never shut down.  Note that
#: ``daemon = True`` is not cleanup: such a thread still runs and still holds
#: references, it is merely killed at interpreter exit.
ALLOWED_PERSISTENT_THREADS = (
    "MainThread",
    "pydevd",
    "QThread",
    "ThreadPoolExecutor",
    "asyncio",
)


def session_threads() -> list[str]:
    return sorted(
        thread.name
        for thread in threading.enumerate()
        if thread is not threading.main_thread()
        and not any(thread.name.startswith(allowed) for allowed in ALLOWED_PERSISTENT_THREADS)
    )


def lifecycle_snapshot() -> dict:
    """Everything that must return to baseline after a Stop.

    Counts and flags only -- no object ids or memory addresses -- so a snapshot
    stays comparable across processes and against the recorded fixture.
    """
    from engine.graphics.camera_manager import CameraManager

    return {
        "physics_handlers": len(_physics_event_handlers),
        "animation_handlers": len(_animation_event_handlers),
        "ui_dispatcher_subscribers": get_ui_event_dispatcher().subscriber_count(),
        "ui_runtime_service_live": UIRuntimeService._inst is not None,
        "ui_manager_live": UIManager._inst is not None,
        "ui_binding_manager_live": UIDataBindingManager._instance is not None,
        "cameras": len(getattr(CameraManager, "_cameras", []) or []),
        "runtime_threads": session_threads(),
    }


def empty_scene() -> Editor2DScene:
    scene = Editor2DScene()
    scene.start()
    for obj in list(scene.editable_objects):
        scene._remove_go(obj)
    scene.editable_objects.clear()
    scene.selected_index = -1
    return scene


def scene_with_objects(count: int = 3) -> Editor2DScene:
    """A scene whose objects are in ``editable_objects``, as authoring puts them.

    ``_add_go`` alone only reaches ``game_objects``; a test that relied on it
    would assert against an empty authoring list and pass vacuously.
    """
    scene = empty_scene()
    for index in range(count):
        obj = GameObject(f"Object{index}")
        scene._add_go(obj)
        scene.editable_objects.append(obj)
    return scene


def reset_session_services() -> None:
    """The same set the runtime teardown resets, for test setup/teardown."""
    from engine.core.scene_manager import SceneManager
    from engine.dialogue.manager import get_dialogue_manager

    UIRuntimeService.reset()
    UIDataBindingManager.reset()
    UIManager.reset()
    SceneManager.reset()
    get_ui_event_dispatcher().clear()
    get_dialogue_manager().reset()
