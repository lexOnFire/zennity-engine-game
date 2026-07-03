"""
tests/core/test_scene_manager.py
────────────────────────────────────────────────────────────────
Suite completa do SceneManager — 74 testes.

Fluxo real de SceneManager.update():
  1. Se tr is None ou tr.is_done  → executa cena normal e sai
  2. tr.update(dt)               → side_effect incrementa tick
  3. Se tr.should_swap           → _execute_pending_swap() (zera _pending_scene)
  4. Se tr.phase in (IN, DONE)   → atualiza cena
  5. Se tr.is_done               → limpa _transition e dispara on_transition_end

Grupos:
  TestSingleton              ( 5) instance(), reset(), isolamento
  TestLoad                   ( 7) load instantâneo
  TestPush                   ( 6) push instantâneo
  TestPop                    ( 6) pop instantâneo
  TestReplace                ( 2) load sobre pilha profunda
  TestProperties             ( 3) current, depth, is_transitioning
  TestLifecycle              ( 4) start, engine antes do start
  TestDelegation             ( 5) update/draw/handle_event
  TestBindEngine             ( 3) bind()
  TestCallbacks              ( 4) on_transition_start, handle bloqueado
  TestEdgeCases              ( 4) reload, cycles, manual clear
  TestRepr                   ( 3) __repr__
  TestPushPopWithTransition  ( 6) push/pop com transição
  TestTransitionFlow         ( 6) fluxo completo de transição
  TestUpdateDrawTopOfStack   ( 5) top-of-stack isolation
  TestDoSwapLoadResources    ( 5) colliders + audio em _do_swap_load
  TestDeprecatedShim         ( 4) import legado emite DeprecationWarning

Total: 74 testes.
"""
from __future__ import annotations

import sys
import warnings
import pytest
from unittest.mock import MagicMock, patch


# ---------------------------------------------------------------------------
# Stubs
# ---------------------------------------------------------------------------

def _make_scene(name="TestScene"):
    """Cena mock com a interface mínima esperada pelo SceneManager."""
    scene = MagicMock()
    scene.__class__.__name__ = name
    scene.engine = None
    return scene


def _make_transition(swap_after=1):
    """
    Transição fake controlada por ticks.

    swap_after=N: no tick N, seta should_swap=True E is_done=True
    simultaneamente, para que o SM execute o swap e limpe _transition
    no mesmo update().
    Para testes de 'ainda transitioning antes do swap', usar swap_after=99.
    """
    from engine.transitions import TransitionPhase

    tr = MagicMock()
    tr.is_done      = False
    tr.should_swap  = False
    tr.phase        = TransitionPhase.OUT
    tr.snapshot_out = None
    tr.snapshot_in  = None

    state = {"tick": 0, "swapped": False}

    def _upd(dt):
        state["tick"] += 1
        if state["tick"] >= swap_after and not state["swapped"]:
            state["swapped"] = True
            tr.should_swap = True
            tr.phase       = TransitionPhase.IN
            tr.is_done     = True
        else:
            tr.should_swap = False

    tr.update.side_effect = _upd
    return tr


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _patch_deps():
    """Moca UIManager e _run_physics em todos os testes."""
    patches = [
        patch("engine.core.scene_manager.UIManager"),
        patch("engine.core.scene_manager.SceneManager._run_physics"),
    ]
    mocks = [p.start() for p in patches]
    yield mocks
    for p in patches:
        try:
            p.stop()
        except RuntimeError:
            pass


@pytest.fixture
def sm():
    """Instância limpa para cada teste."""
    from engine.core.scene_manager import SceneManager
    SceneManager.reset()
    manager = SceneManager.instance()
    manager._engine = MagicMock()
    yield manager
    SceneManager.reset()


# ===========================================================================
# 1. Singleton
# ===========================================================================

class TestSingleton:
    def test_instance_returns_same_object(self, sm):
        from engine.core.scene_manager import SceneManager
        assert SceneManager.instance() is sm

    def test_reset_creates_new_instance(self):
        from engine.core.scene_manager import SceneManager
        SceneManager.reset()
        a = SceneManager.instance()
        SceneManager.reset()
        b = SceneManager.instance()
        assert a is not b

    def test_state_not_shared_after_reset(self):
        from engine.core.scene_manager import SceneManager
        sm1 = SceneManager.instance()
        sm1._engine = MagicMock()
        sm1.load(_make_scene("Old"))
        SceneManager.reset()
        sm2 = SceneManager.instance()
        assert sm2.current is None

    def test_fresh_instance_stack_empty(self):
        from engine.core.scene_manager import SceneManager
        SceneManager.reset()
        assert SceneManager.instance().stack_depth == 0

    def test_fresh_instance_not_transitioning(self):
        from engine.core.scene_manager import SceneManager
        SceneManager.reset()
        assert SceneManager.instance().is_transitioning is False


# ===========================================================================
# 2. load()
# ===========================================================================

class TestLoad:
    def test_load_sets_current(self, sm):
        scene = _make_scene("Game")
        sm.load(scene)
        assert sm.current is scene

    def test_load_calls_start(self, sm):
        scene = _make_scene()
        sm.load(scene)
        scene.start.assert_called_once()

    def test_load_sets_engine_on_scene(self, sm):
        scene = _make_scene()
        sm.load(scene)
        assert scene.engine is sm._engine

    def test_load_replaces_existing_scene(self, sm):
        s1, s2 = _make_scene("S1"), _make_scene("S2")
        sm.load(s1)
        sm.load(s2)
        assert sm.current is s2

    def test_load_resets_stack_to_depth_one(self, sm):
        sm.load(_make_scene())
        sm.load(_make_scene())
        assert sm.stack_depth == 1

    def test_load_not_transitioning(self, sm):
        sm.load(_make_scene())
        assert sm.is_transitioning is False

    def test_load_multiple_times_only_last_is_current(self, sm):
        for i in range(5):
            sm.load(_make_scene(f"S{i}"))
        assert sm.stack_depth == 1


# ===========================================================================
# 3. push()
# ===========================================================================

class TestPush:
    def test_push_increases_depth(self, sm):
        sm.load(_make_scene("Base"))
        sm.push(_make_scene("Pause"))
        assert sm.stack_depth == 2

    def test_push_sets_new_current(self, sm):
        sm.load(_make_scene("Base"))
        pause = _make_scene("Pause")
        sm.push(pause)
        assert sm.current is pause

    def test_push_preserves_base_scene(self, sm):
        base = _make_scene("Base")
        sm.load(base)
        sm.push(_make_scene("Pause"))
        assert sm._stack[0] is base

    def test_push_calls_start_on_new_scene(self, sm):
        sm.load(_make_scene())
        top = _make_scene()
        sm.push(top)
        top.start.assert_called_once()

    def test_multiple_pushes_accumulate(self, sm):
        sm.load(_make_scene("A"))
        sm.push(_make_scene("B"))
        sm.push(_make_scene("C"))
        assert sm.stack_depth == 3

    def test_push_from_empty_stack(self, sm):
        s = _make_scene("Solo")
        sm.push(s)
        assert sm.stack_depth == 1
        assert sm.current is s


# ===========================================================================
# 4. pop()
# ===========================================================================

class TestPop:
    def test_pop_decreases_depth(self, sm):
        sm.load(_make_scene("Base"))
        sm.push(_make_scene("Pause"))
        sm.pop()
        assert sm.stack_depth == 1

    def test_pop_restores_previous_scene(self, sm):
        base = _make_scene("Base")
        sm.load(base)
        sm.push(_make_scene("Pause"))
        sm.pop()
        assert sm.current is base

    def test_pop_with_single_scene_is_noop(self, sm):
        scene = _make_scene()
        sm.load(scene)
        sm.pop()
        assert sm.stack_depth == 1
        assert sm.current is scene

    def test_pop_empty_stack_is_safe(self, sm):
        sm.pop()  # sem crash

    def test_push_then_pop_returns_to_base(self, sm):
        base = _make_scene("Base")
        sm.load(base)
        for i in range(3):
            sm.push(_make_scene(f"Layer{i}"))
        for _ in range(3):
            sm.pop()
        assert sm.current is base
        assert sm.stack_depth == 1

    def test_pop_twice(self, sm):
        sm.load(_make_scene("A"))
        sm.push(_make_scene("B"))
        sm.push(_make_scene("C"))
        sm.pop()
        sm.pop()
        assert sm.stack_depth == 1


# ===========================================================================
# 5. load() sobre pilha profunda
# ===========================================================================

class TestReplace:
    def test_replace_deep_stack_resets_to_depth_one(self, sm):
        sm.load(_make_scene("A"))
        sm.push(_make_scene("B"))
        sm.push(_make_scene("C"))
        fresh = _make_scene("Fresh")
        sm.load(fresh)
        assert sm.stack_depth == 1
        assert sm.current is fresh

    def test_old_scenes_removed_from_stack(self, sm):
        old_a, old_b = _make_scene("A"), _make_scene("B")
        sm.load(old_a)
        sm.push(old_b)
        sm.load(_make_scene("New"))
        assert old_a not in sm._stack
        assert old_b not in sm._stack


# ===========================================================================
# 6. Propriedades
# ===========================================================================

class TestProperties:
    def test_current_is_none_when_empty(self, sm):
        assert sm.current is None

    def test_stack_depth_zero_when_empty(self, sm):
        assert sm.stack_depth == 0

    def test_is_transitioning_false_without_transition(self, sm):
        sm.load(_make_scene())
        assert sm.is_transitioning is False


# ===========================================================================
# 7. Ciclo de vida
# ===========================================================================

class TestLifecycle:
    def test_start_called_on_load(self, sm):
        s = _make_scene()
        sm.load(s)
        s.start.assert_called_once()

    def test_start_called_on_push(self, sm):
        sm.load(_make_scene("Base"))
        s = _make_scene("Pushed")
        sm.push(s)
        s.start.assert_called_once()

    def test_start_called_only_once_on_load(self, sm):
        s = _make_scene()
        sm.load(s)
        sm.load(_make_scene("Other"))
        s.start.assert_called_once()

    def test_engine_assigned_before_start(self, sm):
        from engine.core.scene import Scene as RealScene
        assigned = {}

        class _Spy(RealScene):
            def start(self_inner):
                assigned["engine"] = self_inner.engine

        spy = _Spy()
        sm.load(spy)
        assert assigned["engine"] is sm._engine


# ===========================================================================
# 8. update / draw / handle_event
# ===========================================================================

class TestDelegation:
    def test_update_delegates_to_current_scene(self, sm):
        scene = _make_scene()
        sm.load(scene)
        sm.update(0.016)
        scene.update.assert_called_once_with(0.016)

    def test_draw_delegates_to_current_scene(self, sm):
        scene = _make_scene()
        sm.load(scene)
        surface = MagicMock()
        sm.draw(surface)
        scene.draw.assert_called_once_with(surface)

    def test_handle_event_delegates_to_current_scene(self, sm):
        scene = _make_scene()
        sm.load(scene)
        event = MagicMock()
        sm.handle_event(event)
        scene.handle_event.assert_called_once_with(event)

    def test_update_does_nothing_when_empty(self, sm):
        sm.update(0.016)  # sem crash

    def test_draw_does_nothing_when_empty(self, sm):
        sm.draw(MagicMock())  # sem crash


# ===========================================================================
# 9. bind()
# ===========================================================================

class TestBindEngine:
    def test_bind_patches_change_scene(self, sm):
        engine = MagicMock()
        sm.bind(engine)
        assert engine.change_scene == sm.load

    def test_bind_stores_engine_reference(self, sm):
        engine = MagicMock()
        sm.bind(engine)
        assert sm._engine is engine

    def test_change_scene_via_patched_engine(self, sm):
        engine = MagicMock()
        sm.bind(engine)
        s = _make_scene("FromEngine")
        engine.change_scene(s)
        assert sm.current is s


# ===========================================================================
# 10. Callbacks
# ===========================================================================

class TestCallbacks:
    def test_on_transition_start_called(self, sm):
        cb = MagicMock()
        sm.on_transition_start = cb
        fake_tr = MagicMock()
        fake_tr.is_done = False
        fake_tr.should_swap = False
        fake_tr.phase = "out"
        sm._start_transition(fake_tr, _make_scene("Next"))
        cb.assert_called_once()

    def test_on_transition_start_receives_scene_name(self, sm):
        cb = MagicMock()
        sm.on_transition_start = cb
        fake_tr = MagicMock()
        fake_tr.is_done = False
        fake_tr.should_swap = False
        sm._start_transition(fake_tr, _make_scene("BossScene"))
        cb.assert_called_once_with("BossScene")

    def test_handle_event_blocked_during_transition(self, sm):
        scene = _make_scene()
        sm.load(scene)
        fake_tr = MagicMock()
        fake_tr.is_done = False
        sm._transition = fake_tr
        sm.handle_event(MagicMock())
        scene.handle_event.assert_not_called()

    def test_on_transition_end_none_by_default(self, sm):
        assert sm.on_transition_end is None


# ===========================================================================
# 11. Edge cases
# ===========================================================================

class TestEdgeCases:
    def test_reload_same_scene_replaces(self, sm):
        scene = _make_scene("Reused")
        sm.load(scene)
        sm.load(scene)
        assert sm.stack_depth == 1

    def test_depth_consistent_after_push_pop_cycles(self, sm):
        sm.load(_make_scene("Base"))
        for _ in range(5):
            sm.push(_make_scene())
        for _ in range(5):
            sm.pop()
        assert sm.stack_depth == 1

    def test_current_none_after_manual_stack_clear(self, sm):
        sm.load(_make_scene())
        sm._stack.clear()
        assert sm.current is None

    def test_is_transitioning_false_after_transition_done(self, sm):
        sm.load(_make_scene())
        done_tr = MagicMock()
        done_tr.is_done = True
        sm._transition = done_tr
        assert sm.is_transitioning is False


# ===========================================================================
# 12. __repr__
# ===========================================================================

class TestRepr:
    def test_repr_contains_current(self, sm):
        sm.load(_make_scene("GameScene"))
        assert "current=" in repr(sm)

    def test_repr_contains_depth(self, sm):
        sm.load(_make_scene())
        assert "depth=" in repr(sm)

    def test_repr_contains_transitioning(self, sm):
        sm.load(_make_scene())
        assert "transitioning=" in repr(sm)


# ===========================================================================
# 13. push/pop COM transição
# ===========================================================================

class TestPushPopWithTransition:
    def test_push_transition_increases_depth_after_swap(self, sm):
        sm.load(_make_scene("Base"))
        over = _make_scene("Over")
        tr = _make_transition(swap_after=1)
        sm.push(over, transition=tr)
        sm.update(0.016)
        assert sm.stack_depth == 2

    def test_push_transition_new_scene_becomes_current(self, sm):
        sm.load(_make_scene("Base"))
        over = _make_scene("Over")
        tr = _make_transition(swap_after=1)
        sm.push(over, transition=tr)
        sm.update(0.016)
        assert sm.current is over

    def test_push_transition_calls_start_after_swap(self, sm):
        sm.load(_make_scene("Base"))
        over = _make_scene("Over")
        tr = _make_transition(swap_after=1)
        sm.push(over, transition=tr)
        over.start.assert_not_called()
        sm.update(0.016)
        over.start.assert_called_once()

    def test_pop_transition_restores_base(self, sm):
        base = _make_scene("Base")
        sm.load(base)
        sm.push(_make_scene("Over"))
        tr = _make_transition(swap_after=1)
        sm.pop(transition=tr)
        sm.update(0.016)
        assert sm.current is base

    def test_pop_transition_decreases_depth(self, sm):
        sm.load(_make_scene("Base"))
        sm.push(_make_scene("Over"))
        tr = _make_transition(swap_after=1)
        sm.pop(transition=tr)
        sm.update(0.016)
        assert sm.stack_depth == 1

    def test_is_transitioning_true_before_swap(self, sm):
        sm.load(_make_scene("Base"))
        tr = _make_transition(swap_after=99)
        sm.push(_make_scene("Over"), transition=tr)
        assert sm.is_transitioning is True


# ===========================================================================
# 14. Fluxo completo de transição
# ===========================================================================

class TestTransitionFlow:
    def test_load_with_transition_is_transitioning(self, sm):
        sm.load(_make_scene())
        tr = _make_transition(swap_after=99)
        sm.load(_make_scene("New"), transition=tr)
        assert sm.is_transitioning is True

    def test_swap_happens_on_correct_tick(self, sm):
        s1, s2 = _make_scene("A"), _make_scene("B")
        sm.load(s1)
        tr = _make_transition(swap_after=2)
        sm.load(s2, transition=tr)
        sm.update(0.016)  # tick 1 — sem swap
        assert sm.current is not s2
        sm.update(0.016)  # tick 2 — swap
        assert sm.current is s2

    def test_on_transition_end_fires_after_done(self, sm):
        cb = MagicMock()
        sm.on_transition_end = cb
        tr = _make_transition(swap_after=1)
        sm.load(_make_scene(), transition=tr)
        cb.assert_not_called()
        sm.update(0.016)
        cb.assert_called_once()

    def test_scene_start_not_called_before_swap(self, sm):
        sm.load(_make_scene("A"))
        new = _make_scene("B")
        tr = _make_transition(swap_after=5)
        sm.load(new, transition=tr)
        new.start.assert_not_called()

    def test_scene_start_called_after_swap(self, sm):
        sm.load(_make_scene("A"))
        new = _make_scene("B")
        tr = _make_transition(swap_after=1)
        sm.load(new, transition=tr)
        sm.update(0.016)
        new.start.assert_called_once()

    def test_transition_cleared_after_done(self, sm):
        tr = _make_transition(swap_after=1)
        sm.load(_make_scene(), transition=tr)
        sm.update(0.016)
        assert sm._transition is None


# ===========================================================================
# 15. update/draw com top-of-stack
# ===========================================================================

class TestUpdateDrawTopOfStack:
    def test_update_calls_only_top_scene(self, sm):
        base, over = _make_scene("Base"), _make_scene("Over")
        sm.load(base)
        sm.push(over)
        sm.update(0.016)
        over.update.assert_called_once_with(0.016)
        base.update.assert_not_called()

    def test_draw_calls_only_top_scene(self, sm):
        base, over = _make_scene("Base"), _make_scene("Over")
        sm.load(base)
        sm.push(over)
        surf = MagicMock()
        sm.draw(surf)
        over.draw.assert_called_once_with(surf)
        base.draw.assert_not_called()

    def test_handle_event_calls_only_top_scene(self, sm):
        base, over = _make_scene("Base"), _make_scene("Over")
        sm.load(base)
        sm.push(over)
        evt = MagicMock()
        sm.handle_event(evt)
        over.handle_event.assert_called_once_with(evt)
        base.handle_event.assert_not_called()

    def test_after_pop_update_goes_to_base(self, sm):
        base, over = _make_scene("Base"), _make_scene("Over")
        sm.load(base)
        sm.push(over)
        sm.pop()
        base.update.reset_mock()
        sm.update(0.016)
        base.update.assert_called_once()

    def test_after_pop_draw_goes_to_base(self, sm):
        base, over = _make_scene("Base"), _make_scene("Over")
        sm.load(base)
        sm.push(over)
        sm.pop()
        surf = MagicMock()
        sm.draw(surf)
        base.draw.assert_called_once_with(surf)


# ===========================================================================
# 16. _do_swap_load limpa colisores e áudio
# ===========================================================================

class TestDoSwapLoadResources:
    _BOX   = "engine.core.scene_manager.BoxCollider"
    _CIRC  = "engine.core.scene_manager.CircleCollider"
    _AUDIO = "engine.core.scene_manager.AudioManager"

    def test_load_clears_box_registry(self, sm):
        with patch(self._BOX) as mock_box, patch(self._CIRC), patch(self._AUDIO):
            sm.load(_make_scene())
        mock_box._registry.clear.assert_called()

    def test_load_clears_circle_registry(self, sm):
        with patch(self._BOX), patch(self._CIRC) as mock_circ, patch(self._AUDIO):
            sm.load(_make_scene())
        mock_circ._registry.clear.assert_called()

    def test_load_clears_scene_tilemaps(self, sm):
        with patch(self._BOX) as mock_box, patch(self._CIRC), patch(self._AUDIO):
            sm.load(_make_scene())
        mock_box._scene_tilemaps.clear.assert_called()

    def test_load_stops_music(self, sm):
        with patch(self._BOX), patch(self._CIRC), patch(self._AUDIO) as mock_audio:
            sm.load(_make_scene())
        mock_audio.stop_music.assert_called()

    def test_load_unloads_audio_cache(self, sm):
        with patch(self._BOX), patch(self._CIRC), patch(self._AUDIO) as mock_audio:
            sm.load(_make_scene())
        mock_audio.unload_cache.assert_called()


# ===========================================================================
# 17. Shim de compatibilidade (engine/scene_manager.py)
# ===========================================================================

class TestDeprecatedShim:
    def _import_shim(self):
        """Remove o módulo do cache e reimporta para garantir o warning."""
        for key in list(sys.modules):
            if key == "engine.scene_manager":
                del sys.modules[key]
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            import engine.scene_manager as shim  # noqa: F401
            return shim, w

    def test_shim_emits_deprecation_warning(self):
        _, w = self._import_shim()
        cats = [str(x.category) for x in w]
        assert any("DeprecationWarning" in c for c in cats)

    def test_shim_warning_mentions_engine_core(self):
        _, w = self._import_shim()
        messages = [str(x.message) for x in w]
        assert any("engine.core" in m for m in messages)

    def test_shim_exports_scene_manager_class(self):
        from engine.core.scene_manager import SceneManager
        shim, _ = self._import_shim()
        assert shim.SceneManager is SceneManager

    def test_shim_all_contains_scene_manager(self):
        shim, _ = self._import_shim()
        assert "SceneManager" in shim.__all__
