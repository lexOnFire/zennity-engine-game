"""
tests/core/test_scene_manager.py
────────────────────────────────────────────────────────────────
Commit 17: suite completa do SceneManager.

Grupos:
  TestSingleton       (3)  — instance, reset, isolamento de estado
  TestLoad            (7)  — troca imediata, pilha limpa, engine injetado
  TestPush            (6)  — empilhamento, start, preserva base
  TestPop             (6)  — pop, noop em pilha unitária/vazia, pop múltiplo
  TestReplace         (2)  — load() sobre pilha profunda reseta para depth=1
  TestProperties      (3)  — current, stack_depth, is_transitioning
  TestLifecycle       (4)  — start() uma vez, engine atribuído antes
  TestDelegation      (5)  — update/draw/handle_event delegam para cena ativa
  TestBindEngine      (3)  — bind() faz patch de engine.change_scene
  TestCallbacks       (4)  — on_transition_start/end, handle_event bloqueado
  TestEdgeCases       (4)  — push vazio, pop vazio, re-load mesma cena, depth consistente
  TestRepr            (3)  — repr contém os campos esperados

Total esperado: 50 testes.

Todos os testes rodam headless — UIManager, AudioManager e
physics são mockados via pytest fixtures/patch.
"""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch


# ───────────────────────────────────────────────────────────────────
def _make_scene(name="TestScene"):
    """Cena fake com a interface mínima que SceneManager espera."""
    scene = MagicMock()
    scene.__class__.__name__ = name
    scene.engine = None
    return scene


# ───────────────────────────────────────────────────────────────────
@pytest.fixture(autouse=True)
def _patch_deps():
    """Moca dependências pesadas em todos os testes do arquivo."""
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
    """Instância limpa do SceneManager para cada teste."""
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
    def test_instance_is_same_object(self, sm):
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


# ===========================================================================
# 2. load() — substitui toda a pilha
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
        s1 = _make_scene("S1")
        s2 = _make_scene("S2")
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
# 3. push() — empilha sem destruir cena anterior
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
# 4. pop() — remove topo
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
        sm.pop()  # não deve lançar

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
        assert sm.current.engine is sm._engine


# ===========================================================================
# 5. TestReplace — load() sobre pilha profunda
# ===========================================================================

class TestReplace:
    def test_replace_deep_stack_resets_to_depth_one(self, sm):
        sm.load(_make_scene("A"))
        sm.push(_make_scene("B"))
        sm.push(_make_scene("C"))
        assert sm.stack_depth == 3
        fresh = _make_scene("Fresh")
        sm.load(fresh)
        assert sm.stack_depth == 1
        assert sm.current is fresh

    def test_old_scenes_removed_from_stack(self, sm):
        old_a = _make_scene("A")
        old_b = _make_scene("B")
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
        """engine deve estar atribuído quando start() for chamado."""
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
        sm.update(0.016)  # não deve lançar

    def test_draw_does_nothing_when_empty(self, sm):
        sm.draw(MagicMock())  # não deve lançar


# ===========================================================================
# 9. bind() — patch de engine.change_scene
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
# 10. Callbacks on_transition_start / on_transition_end
# ===========================================================================

class TestCallbacks:
    def test_on_transition_start_called(self, sm):
        """Callback deve ser chamado ao iniciar uma transição."""
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
        """handle_event não deve propagar quando is_transitioning=True."""
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
        """Carregar a mesma instância de cena duas vezes não duplica pilha."""
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
