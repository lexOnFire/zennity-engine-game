"""
tests/core/test_scene_manager.py
────────────────────────────────────────────────────────────────
Commit 3: valida o contrato público do SceneManager (pilha de cenas).

Estratégia:
  - Usar SceneManager.reset() para isolamento entre testes.
  - Mockar Scene com MagicMock (não precisamos de Pygame para testar a pilha).
  - Mockar UIManager.reset e módulos de physics/audio para evitar
    dependências de runtime.
"""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_scene(name="TestScene"):
    """Cena fake com a interface mínima que SceneManager espera."""
    scene = MagicMock()
    scene.__class__.__name__ = name
    scene.engine = None
    return scene


# ---------------------------------------------------------------------------
# Patches permanentes: evita import de pygame / physics / audio
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _patch_deps():
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


# ---------------------------------------------------------------------------
# Fixture: instância limpa por teste
# ---------------------------------------------------------------------------

@pytest.fixture
def sm():
    from engine.core.scene_manager import SceneManager
    SceneManager.reset()
    manager = SceneManager.instance()
    manager._engine = MagicMock()  # engine fake
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

    def test_multiple_pushes(self, sm):
        sm.load(_make_scene("A"))
        sm.push(_make_scene("B"))
        sm.push(_make_scene("C"))
        assert sm.stack_depth == 3


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
        sm.pop()  # não deve lançar, não deve alterar pilha
        assert sm.stack_depth == 1
        assert sm.current is scene

    def test_pop_empty_stack_is_safe(self, sm):
        sm.pop()  # sem cenas — não deve lançar

    def test_push_then_pop_returns_to_base(self, sm):
        base = _make_scene("Base")
        sm.load(base)
        for i in range(3):
            sm.push(_make_scene(f"Layer{i}"))
        for _ in range(3):
            sm.pop()
        assert sm.current is base
        assert sm.stack_depth == 1


# ===========================================================================
# 5. Propriedades
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
# 6. update / draw / handle_event
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
# 7. __repr__
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
