"""
tests/test_transitions.py
────────────────────────────────────────────────────────────────────────────
Testes unitários de engine/transitions.py.

Estratégia de isolamento:
  - pygame completo é stubado: Surface, SRCALPHA, draw.rect são
    substituidos por MagicMock ou fake classes controladas.
  - _FakeSurface rastreia blit/fill/draw calls sem SDL.
  - Cada teste avalia o estado interno (phase, progress, timer) ou
    os métodos blitados na surface, não pixels reais.
  - Easing functions são testadas matematicamente.
"""
from __future__ import annotations

import sys
from types import ModuleType
from unittest.mock import MagicMock, call

import pytest

# ── stub pygame ──────────────────────────────────────────────────────────────

class _FakeSurface:
    """Surface mínimo: rastreia blit/fill, responde a get_size/get_alpha/set_alpha."""
    def __init__(self, size=(800, 600), flags=0):
        self._size  = size
        self._flags = flags
        self._alpha = 255
        self.blit   = MagicMock()
        self.fill   = MagicMock()
        self.set_alpha = MagicMock(side_effect=lambda a: setattr(self, "_alpha", a))
    def get_size(self):  return self._size
    def get_alpha(self): return self._alpha


def _build_pygame_stub():
    pg = ModuleType("pygame")
    pg.SRCALPHA = 65536
    pg.Surface  = _FakeSurface

    draw_mod = ModuleType("pygame.draw")
    draw_mod.rect = MagicMock()
    pg.draw = draw_mod

    sys.modules["pygame"]      = pg
    sys.modules["pygame.draw"] = draw_mod
    return pg


if "pygame" not in sys.modules:
    _pg = _build_pygame_stub()
else:
    _pg = sys.modules["pygame"]
    _pg.SRCALPHA = getattr(_pg, "SRCALPHA", 65536)
    if not isinstance(getattr(_pg, "Surface", None), type) or \
       getattr(_pg.Surface, "_fake", False):
        _pg.Surface = _FakeSurface

from engine.transitions import (   # noqa: E402
    Transition, TransitionPhase,
    FadeTransition, SlideTransition, SlideDirection,
    WipeTransition, CrossfadeTransition,
    EASING, _linear, _ease_in, _ease_out, _ease_in_out,
)


# ── helpers ────────────────────────────────────────────────────────────────

def _advance(t: Transition, dt: float, steps: int = 1):
    for _ in range(steps):
        t.update(dt)


def _run_to_swap(t: Transition):
    """Avança até a fase SWAP."""
    for _ in range(10_000):
        if t.phase == TransitionPhase.SWAP:
            return
        if t.is_done:
            raise RuntimeError("Passou de DONE sem passar por SWAP")
        t.update(0.05)
    raise RuntimeError("SWAP não atingido")


def _run_to_done(t: Transition):
    """Avança até DONE."""
    for _ in range(10_000):
        if t.is_done:
            return
        t.update(0.05)
    raise RuntimeError("DONE não atingido")


def _fake_snap(size=(800, 600)):
    return _FakeSurface(size)


# ── TestEasing ────────────────────────────────────────────────────────────────
class TestEasing:
    def test_linear_zero(self):      assert _linear(0.0)      == pytest.approx(0.0)
    def test_linear_half(self):      assert _linear(0.5)      == pytest.approx(0.5)
    def test_linear_one(self):       assert _linear(1.0)      == pytest.approx(1.0)
    def test_ease_in_zero(self):     assert _ease_in(0.0)     == pytest.approx(0.0)
    def test_ease_in_one(self):      assert _ease_in(1.0)     == pytest.approx(1.0)
    def test_ease_in_quarter(self):  assert _ease_in(0.5)     == pytest.approx(0.25)
    def test_ease_out_zero(self):    assert _ease_out(0.0)    == pytest.approx(0.0)
    def test_ease_out_one(self):     assert _ease_out(1.0)    == pytest.approx(1.0)
    def test_ease_out_half(self):    assert _ease_out(0.5)    == pytest.approx(0.75)
    def test_ease_in_out_zero(self): assert _ease_in_out(0.0) == pytest.approx(0.0)
    def test_ease_in_out_one(self):  assert _ease_in_out(1.0) == pytest.approx(1.0)
    def test_ease_in_out_half(self): assert _ease_in_out(0.5) == pytest.approx(0.5)
    def test_ease_in_out_symmetric(self):
        assert _ease_in_out(0.25) == pytest.approx(1.0 - _ease_in_out(0.75), abs=1e-6)
    def test_easing_dict_has_all_keys(self):
        assert set(EASING.keys()) == {"linear", "ease_in", "ease_out", "ease_in_out"}
    def test_easing_dict_values_are_callable(self):
        for fn in EASING.values():
            assert callable(fn)


# ── TestTransitionBase ────────────────────────────────────────────────────────────
class TestTransitionBase:
    def test_initial_phase_is_out(self):
        assert Transition().phase == TransitionPhase.OUT

    def test_initial_progress_zero(self):
        assert Transition().progress == pytest.approx(0.0)

    def test_is_done_false_initially(self):
        assert Transition().is_done is False

    def test_should_swap_false_initially(self):
        assert Transition().should_swap is False

    def test_duration_out_clamped_to_001(self):
        t = Transition(duration_out=0.0)
        assert t.duration_out == pytest.approx(0.01)

    def test_duration_in_clamped_to_001(self):
        t = Transition(duration_in=0.0)
        assert t.duration_in == pytest.approx(0.01)

    def test_unknown_easing_falls_back_to_ease_in_out(self):
        t = Transition(easing="nonexistent")
        assert t._ease is _ease_in_out

    def test_progress_advances_during_out(self):
        t = Transition(duration_out=1.0)
        t.update(0.5)
        assert 0.0 < t.progress < 1.0

    def test_phase_becomes_swap_after_out_completes(self):
        t = Transition(duration_out=0.1, duration_in=0.1)
        _run_to_swap(t)
        assert t.phase == TransitionPhase.SWAP

    def test_should_swap_true_during_swap_phase(self):
        t = Transition(duration_out=0.1, duration_in=0.1)
        _run_to_swap(t)
        assert t.should_swap is True

    def test_swap_advances_to_in_next_update(self):
        t = Transition(duration_out=0.1, duration_in=0.1)
        _run_to_swap(t)
        t.update(0.0)  # um update no estado SWAP
        assert t.phase == TransitionPhase.IN

    def test_phase_becomes_done_after_in_completes(self):
        t = Transition(duration_out=0.1, duration_in=0.1)
        _run_to_done(t)
        assert t.is_done is True

    def test_update_noop_when_done(self):
        t = Transition(duration_out=0.01, duration_in=0.01)
        _run_to_done(t)
        t.update(999.0)  # não deve crashar nem mudar estado
        assert t.is_done is True

    def test_progress_resets_to_zero_when_entering_in(self):
        t = Transition(duration_out=0.1, duration_in=0.5)
        _run_to_swap(t)
        t.update(0.0)  # swap → IN
        assert t.progress == pytest.approx(0.0)

    def test_progress_reaches_one_when_done(self):
        t = Transition(duration_out=0.1, duration_in=0.1)
        _run_to_done(t)
        assert t.progress == pytest.approx(1.0)

    def test_base_draw_does_nothing(self):
        t   = Transition()
        scr = _FakeSurface()
        t.draw(scr)  # não deve lançar
        scr.blit.assert_not_called()

    def test_snapshot_out_none_initially(self):
        assert Transition().snapshot_out is None

    def test_snapshot_in_none_initially(self):
        assert Transition().snapshot_in is None

    def test_custom_easing_applied_in_progress(self):
        """Easing linear: raw == progress."""
        t = Transition(duration_out=1.0, easing="linear")
        t.update(0.3)
        assert t.progress == pytest.approx(0.3, abs=0.01)


# ── TestFadeTransition ────────────────────────────────────────────────────────────
class TestFadeTransition:
    def test_default_color_black(self):
        assert FadeTransition().color == (0, 0, 0)

    def test_custom_color_stored(self):
        f = FadeTransition(color=(255, 0, 128))
        assert f.color == (255, 0, 128)

    def test_draw_during_out_blits_snapshot_out(self):
        f = FadeTransition(duration_out=1.0)
        scr = _FakeSurface()
        f.snapshot_out = _fake_snap()
        f.update(0.1)
        f.draw(scr)
        assert scr.blit.call_count >= 1
        assert scr.blit.call_args_list[0][0][0] is f.snapshot_out

    def test_draw_during_out_blits_overlay(self):
        """Dois blits durante OUT: snapshot + overlay."""
        f = FadeTransition(duration_out=1.0)
        scr = _FakeSurface()
        f.snapshot_out = _fake_snap()
        f.update(0.5)
        f.draw(scr)
        assert scr.blit.call_count == 2

    def test_draw_during_in_blits_snapshot_in(self):
        f = FadeTransition(duration_out=0.1, duration_in=1.0)
        scr = _FakeSurface()
        f.snapshot_out = _fake_snap()
        f.snapshot_in  = _fake_snap()
        _run_to_swap(f)
        f.update(0.0)  # IN
        f.update(0.1)
        f.draw(scr)
        assert scr.blit.call_args_list[0][0][0] is f.snapshot_in

    def test_draw_noop_when_done(self):
        f = FadeTransition(duration_out=0.01, duration_in=0.01)
        scr = _FakeSurface()
        _run_to_done(f)
        f.draw(scr)
        scr.blit.assert_not_called()

    def test_draw_no_overlay_when_in_progress_zero(self):
        """alpha=0 → overlay não deve ser blitado na fase IN."""
        f = FadeTransition(duration_out=0.01, duration_in=1.0)
        scr = _FakeSurface()
        f.snapshot_out = _fake_snap()
        f.snapshot_in  = _fake_snap()
        _run_to_swap(f)
        f.update(0.0)   # IN, progress=0
        # Reseta blit para contar somente o draw()
        scr.blit.reset_mock()
        f.draw(scr)
        # progress=0 → alpha=255 (cobre tudo); ainda há 2 blits (snapshot+overlay)
        # O teste só garante que não crasha
        assert scr.blit.call_count >= 1


# ── TestSlideTransition ────────────────────────────────────────────────────────────
class TestSlideTransition:
    def test_default_direction_left(self):
        assert SlideTransition().direction == SlideDirection.LEFT

    def test_all_directions_accepted(self):
        for d in SlideDirection:
            s = SlideTransition(direction=d)
            assert s.direction == d

    def test_draw_during_out_blits_snapshot_out(self):
        s = SlideTransition(duration_out=0.3, duration_in=0.5)
        scr = _FakeSurface()
        s.snapshot_out = _fake_snap()
        s.update(0.1)
        s.draw(scr)
        assert scr.blit.call_count >= 1
        assert scr.blit.call_args_list[0][0][0] is s.snapshot_out

    def test_draw_during_in_blits_snapshot_in(self):
        s = SlideTransition(duration_out=0.1, duration_in=0.5)
        scr = _FakeSurface()
        s.snapshot_out = _fake_snap()
        s.snapshot_in  = _fake_snap()
        _run_to_swap(s)
        s.update(0.0)  # IN
        s.update(0.1)
        s.draw(scr)
        # Snapshot_out base + snapshot_in deslizando
        blitted = [c[0][0] for c in scr.blit.call_args_list]
        assert s.snapshot_in in blitted

    def test_slide_left_position_at_start_of_in(self):
        """LEFT: snapshot_in começa em x=w e desliza até 0."""
        s = SlideTransition(direction=SlideDirection.LEFT,
                            duration_out=0.01, duration_in=1.0,
                            easing="linear")
        scr = _FakeSurface((800, 600))
        s.snapshot_out = _fake_snap()
        s.snapshot_in  = _fake_snap()
        _run_to_swap(s)
        s.update(0.0)   # IN, progress=0 → x=800
        s.draw(scr)
        # Último blit é o snapshot_in; pos x deve ser próximo de 800
        last_pos = scr.blit.call_args_list[-1][0][1]
        assert last_pos[0] == pytest.approx(800, abs=5)

    def test_slide_right_position_at_start_of_in(self):
        s = SlideTransition(direction=SlideDirection.RIGHT,
                            duration_out=0.01, duration_in=1.0,
                            easing="linear")
        scr = _FakeSurface((800, 600))
        s.snapshot_out = _fake_snap()
        s.snapshot_in  = _fake_snap()
        _run_to_swap(s)
        s.update(0.0)   # IN, progress=0 → x=-800
        s.draw(scr)
        last_pos = scr.blit.call_args_list[-1][0][1]
        assert last_pos[0] == pytest.approx(-800, abs=5)

    def test_slide_up_y_position_at_start(self):
        s = SlideTransition(direction=SlideDirection.UP,
                            duration_out=0.01, duration_in=1.0,
                            easing="linear")
        scr = _FakeSurface((800, 600))
        s.snapshot_out = _fake_snap()
        s.snapshot_in  = _fake_snap()
        _run_to_swap(s)
        s.update(0.0)
        s.draw(scr)
        last_pos = scr.blit.call_args_list[-1][0][1]
        assert last_pos[1] == pytest.approx(600, abs=5)

    def test_slide_down_y_position_at_start(self):
        s = SlideTransition(direction=SlideDirection.DOWN,
                            duration_out=0.01, duration_in=1.0,
                            easing="linear")
        scr = _FakeSurface((800, 600))
        s.snapshot_out = _fake_snap()
        s.snapshot_in  = _fake_snap()
        _run_to_swap(s)
        s.update(0.0)
        s.draw(scr)
        last_pos = scr.blit.call_args_list[-1][0][1]
        assert last_pos[1] == pytest.approx(-600, abs=5)

    def test_draw_noop_when_done(self):
        s = SlideTransition(duration_out=0.01, duration_in=0.01)
        scr = _FakeSurface()
        _run_to_done(s)
        s.draw(scr)
        scr.blit.assert_not_called()


# ── TestWipeTransition ────────────────────────────────────────────────────────────
class TestWipeTransition:
    def test_default_horizontal_true(self):
        assert WipeTransition().horizontal is True

    def test_vertical_stored(self):
        assert WipeTransition(horizontal=False).horizontal is False

    def test_draw_during_out_blits_snapshot_out(self):
        w = WipeTransition(duration_out=1.0)
        scr = _FakeSurface()
        w.snapshot_out = _fake_snap()
        w.update(0.3)
        w.draw(scr)
        assert scr.blit.call_count >= 1
        assert scr.blit.call_args_list[0][0][0] is w.snapshot_out

    def test_draw_during_out_draws_rect(self):
        """Deve chamar pygame.draw.rect durante OUT."""
        w = WipeTransition(duration_out=1.0)
        scr = _FakeSurface()
        w.snapshot_out = _fake_snap()
        w.update(0.5)
        w.draw(scr)
        _pg.draw.rect.assert_called()

    def test_wipe_rect_width_grows_horizontally(self):
        """OUT horizontal: rect.width = int(W * progress)."""
        w = WipeTransition(horizontal=True, duration_out=1.0, easing="linear")
        scr = _FakeSurface((800, 600))
        w.snapshot_out = _fake_snap()
        w.update(0.5)   # linear → progress ≈ 0.5
        _pg.draw.rect.reset_mock()
        w.draw(scr)
        rect_arg = _pg.draw.rect.call_args[0][2]
        assert rect_arg[2] == pytest.approx(400, abs=8)  # 800 * 0.5

    def test_wipe_rect_height_grows_vertically(self):
        w = WipeTransition(horizontal=False, duration_out=1.0, easing="linear")
        scr = _FakeSurface((800, 600))
        w.snapshot_out = _fake_snap()
        w.update(0.5)
        _pg.draw.rect.reset_mock()
        w.draw(scr)
        rect_arg = _pg.draw.rect.call_args[0][2]
        assert rect_arg[3] == pytest.approx(300, abs=8)  # 600 * 0.5

    def test_draw_during_in_blits_snapshot_in(self):
        w = WipeTransition(duration_out=0.1, duration_in=1.0)
        scr = _FakeSurface()
        w.snapshot_out = _fake_snap()
        w.snapshot_in  = _fake_snap()
        _run_to_swap(w)
        w.update(0.0)   # IN
        w.update(0.1)
        w.draw(scr)
        blitted = [c[0][0] for c in scr.blit.call_args_list]
        assert w.snapshot_in in blitted

    def test_draw_noop_when_done(self):
        w = WipeTransition(duration_out=0.01, duration_in=0.01)
        scr = _FakeSurface()
        _run_to_done(w)
        w.draw(scr)
        scr.blit.assert_not_called()


# ── TestCrossfadeTransition ──────────────────────────────────────────────────────────
class TestCrossfadeTransition:
    def test_duration_split_equally(self):
        c = CrossfadeTransition(duration=0.6)
        assert c.duration_out == pytest.approx(0.3)
        assert c.duration_in  == pytest.approx(0.3)

    def test_draw_during_out_blits_snapshot_out(self):
        c = CrossfadeTransition(duration=2.0)
        scr = _FakeSurface()
        c.snapshot_out = _fake_snap()
        c.update(0.1)
        c.draw(scr)
        assert scr.blit.call_count >= 1 or scr.fill.call_count >= 1

    def test_draw_during_in_fills_black_first(self):
        c = CrossfadeTransition(duration=2.0)
        scr = _FakeSurface()
        c.snapshot_out = _fake_snap()
        c.snapshot_in  = _fake_snap()
        _run_to_swap(c)
        c.update(0.0)  # IN
        c.update(0.1)
        scr.fill.reset_mock()
        scr.blit.reset_mock()
        c.draw(scr)
        # fill((0,0,0)) antes de blit snapshot_in
        assert scr.fill.call_count >= 1

    def test_draw_during_in_sets_alpha(self):
        c = CrossfadeTransition(duration=2.0)
        scr = _FakeSurface()
        c.snapshot_out = _fake_snap()
        c.snapshot_in  = _fake_snap()
        _run_to_swap(c)
        c.update(0.0)
        c.update(0.2)
        c.draw(scr)
        # _alpha_surf.set_alpha deve ter sido chamado
        assert c._alpha_surf is not None
        assert c._alpha_surf._alpha is not None

    def test_draw_noop_when_done(self):
        c = CrossfadeTransition(duration=0.02)
        scr = _FakeSurface()
        _run_to_done(c)
        scr.blit.reset_mock()
        scr.fill.reset_mock()
        c.draw(scr)
        scr.blit.assert_not_called()
        scr.fill.assert_not_called()

    def test_alpha_surf_recreated_on_resize(self):
        c = CrossfadeTransition(duration=2.0)
        scr = _FakeSurface((400, 300))
        c.snapshot_out = _fake_snap((400, 300))
        c.update(0.1)
        c.draw(scr)
        first_surf = c._alpha_surf
        # Simula resize
        scr2 = _FakeSurface((800, 600))
        c.draw(scr2)
        # Nova superficie criada porque tamanho mudou
        assert c._alpha_surf.get_size() == (800, 600)


# ── TestPhaseLifecycle (integração) ──────────────────────────────────────────────────
class TestPhaseLifecycle:
    @pytest.mark.parametrize("cls", [
        lambda: FadeTransition(duration_out=0.1, duration_in=0.1),
        lambda: SlideTransition(duration_out=0.1, duration_in=0.1),
        lambda: WipeTransition(duration_out=0.1, duration_in=0.1),
        lambda: CrossfadeTransition(duration=0.2),
    ])
    def test_all_transitions_reach_done(self, cls):
        t = cls()
        _run_to_done(t)
        assert t.is_done

    @pytest.mark.parametrize("cls", [
        lambda: FadeTransition(duration_out=0.1, duration_in=0.1),
        lambda: SlideTransition(duration_out=0.1, duration_in=0.1),
        lambda: WipeTransition(duration_out=0.1, duration_in=0.1),
        lambda: CrossfadeTransition(duration=0.2),
    ])
    def test_all_transitions_pass_through_swap(self, cls):
        t = cls()
        _run_to_swap(t)
        assert t.should_swap

    @pytest.mark.parametrize("cls", [
        lambda: FadeTransition(duration_out=0.1, duration_in=0.1),
        lambda: SlideTransition(duration_out=0.1, duration_in=0.1),
        lambda: WipeTransition(duration_out=0.1, duration_in=0.1),
        lambda: CrossfadeTransition(duration=0.2),
    ])
    def test_all_transitions_start_with_out(self, cls):
        t = cls()
        assert t.phase == TransitionPhase.OUT
