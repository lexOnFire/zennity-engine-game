"""Session-scoped services must be reset when Play stops.

PHASE 9.5B Stage 3.

``UIRuntimeService``, ``UIDataBindingManager``, ``UIManager``, ``SceneManager``
and ``DialogueManager`` all shipped a reset API.  None of them was called on
Stop, so runtime widgets, data bindings, dialogue sessions and -- worst of the
set -- a *pending scene transition* survived into the next Play.
"""

from __future__ import annotations

import pytest

from engine.core.scene_manager import SceneManager
from engine.dialogue.manager import get_dialogue_manager
from engine.runtime.ui_event_dispatcher import get_ui_event_dispatcher
from engine.ui.data_binding import UIDataBindingManager
from engine.ui.runtime_service import UIRuntimeService
from engine.ui.ui_manager import UIManager


def _reset_everything() -> None:
    UIRuntimeService.reset()
    UIDataBindingManager.reset()
    UIManager.reset()
    SceneManager.reset()
    get_ui_event_dispatcher().clear()
    get_dialogue_manager().reset()


@pytest.fixture(autouse=True)
def clean_services():
    _reset_everything()
    yield
    _reset_everything()


def test_every_session_service_exposes_a_reset():
    """The teardown depends on these; a rename must fail here, not silently."""
    assert callable(UIRuntimeService.reset)
    assert callable(UIDataBindingManager.reset)
    assert callable(UIManager.reset)
    assert callable(SceneManager.reset)
    assert callable(get_dialogue_manager().reset)
    assert callable(get_ui_event_dispatcher().clear)


def test_ui_runtime_service_reset_drops_the_singleton():
    service = UIRuntimeService.instance()
    assert UIRuntimeService._inst is service
    UIRuntimeService.reset()
    assert UIRuntimeService._inst is None
    assert UIRuntimeService.instance() is not service


def test_ui_manager_reset_drops_the_singleton():
    manager = UIManager.instance()
    assert UIManager._inst is manager
    UIManager.reset()
    assert UIManager._inst is None


def test_data_binding_reset_drops_the_singleton():
    UIDataBindingManager.instance()
    assert UIDataBindingManager._instance is not None
    UIDataBindingManager.reset()
    assert UIDataBindingManager._instance is None


def test_scene_manager_reset_cancels_a_pending_transition():
    """A scene change requested during Play must not fire in the next session."""
    manager = SceneManager.instance()
    manager._pending_scene = object()
    manager._pending_push = True
    manager._pending_pop = False

    SceneManager.reset()

    fresh = SceneManager.instance()
    assert fresh is not manager
    assert fresh._pending_scene is None
    assert fresh._pending_push is False
    assert fresh._pending_pop is False


def test_dialogue_reset_clears_sessions():
    manager = get_dialogue_manager()
    manager._sessions["session-1"] = object()
    manager._active_session_id = "session-1"

    manager.reset()

    assert manager._sessions == {}
    assert manager._active_session_id is None
    assert manager._owner_sessions == {}


def test_resetting_twice_is_safe():
    for _ in range(3):
        _reset_everything()
    assert UIRuntimeService._inst is None
    assert UIManager._inst is None
    assert get_ui_event_dispatcher().subscriber_count() == 0
