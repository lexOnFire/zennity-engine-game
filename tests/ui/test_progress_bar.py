"""
tests/ui/test_progress_bar.py
────────────────────────────────────────────────────────────────────────────
Testes unitários de engine/ui/progress_bar.py (ProgressBar).

Estratégia de isolamento:
  - pygame stubado: Surface, Rect, draw.rect, font.SysFont.
  - pygame.Rect retorna _FakeRect real (mantendo x, y, width, height)
    para que fill_rect seja construído corretamente.
  - draw.rect é MagicMock — chamadas inspecionadas sem SDL.
  - Nenhum init, nenhuma janela.
"""
from __future__ import annotations

import pygame
from unittest.mock import MagicMock
import pytest

class _FakeFont:
    def render(self, text, aa, color): return pygame.Surface((60, 14))
    def size(self, text): return (60, 14)

from engine.ui.progress_bar import ProgressBar  # noqa: E402


# ── helpers ────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def reset_mocks(monkeypatch):
    monkeypatch.setattr(pygame.font, "SysFont", MagicMock(return_value=_FakeFont()), raising=False)
    pygame.draw.rect.reset_mock()
    yield
    pygame.draw.rect.reset_mock()


def _screen():
    from conftest import SurfaceProxy
    return SurfaceProxy((640, 480))


def _bar(**kw):
    kw.setdefault("x", 0); kw.setdefault("y", 0)
    kw.setdefault("width", 200); kw.setdefault("height", 20)
    kw.setdefault("value", 50.0); kw.setdefault("max_value", 100.0)
    return ProgressBar(**kw)


# ── TestInit ────────────────────────────────────────────────────────────────
class TestInit:
    def test_value_stored(self):
        assert _bar(value=75.0).value == pytest.approx(75.0)

    def test_max_value_stored(self):
        assert _bar(max_value=200.0).max_value == pytest.approx(200.0)

    def test_display_value_equals_value_on_init(self):
        b = _bar(value=60.0)
        assert b._display_value == pytest.approx(60.0)

    def test_smooth_default_true(self):
        assert _bar().smooth is True

    def test_smooth_speed_stored(self):
        assert _bar(smooth_speed=50.0).smooth_speed == pytest.approx(50.0)

    def test_show_text_default_false(self):
        assert _bar().show_text is False

    def test_color_fill_stored(self):
        b = ProgressBar(color_fill=(1, 2, 3))
        assert b.color_fill == (1, 2, 3)

    def test_color_bg_stored(self):
        b = ProgressBar(color_bg=(10, 10, 10))
        assert b.color_bg == (10, 10, 10)

    def test_border_radius_stored(self):
        b = ProgressBar(border_radius=8)
        assert b.border_radius == 8

    def test_font_none_on_init(self):
        assert _bar()._font is None


# ── TestRatio ────────────────────────────────────────────────────────────────
class TestRatio:
    def test_ratio_half(self):
        b = _bar(value=50.0, max_value=100.0)
        assert b.ratio == pytest.approx(0.5)

    def test_ratio_full(self):
        b = _bar(value=100.0, max_value=100.0)
        assert b.ratio == pytest.approx(1.0)

    def test_ratio_empty(self):
        b = _bar(value=0.0, max_value=100.0)
        assert b.ratio == pytest.approx(0.0)

    def test_ratio_clamped_above_one(self):
        b = _bar(value=999.0, max_value=100.0)
        assert b.ratio == pytest.approx(1.0)

    def test_ratio_clamped_below_zero(self):
        b = _bar(value=-10.0, max_value=100.0)
        assert b.ratio == pytest.approx(0.0)

    def test_ratio_zero_max_returns_zero(self):
        b = ProgressBar(max_value=0.0)
        assert b.ratio == pytest.approx(0.0)


# ── TestSetValue ─────────────────────────────────────────────────────────────
class TestSetValue:
    def test_set_value_normal(self):
        b = _bar(max_value=100.0)
        b.set_value(75.0)
        assert b.value == pytest.approx(75.0)

    def test_set_value_clamped_above_max(self):
        b = _bar(max_value=100.0)
        b.set_value(200.0)
        assert b.value == pytest.approx(100.0)

    def test_set_value_clamped_below_zero(self):
        b = _bar(max_value=100.0)
        b.set_value(-50.0)
        assert b.value == pytest.approx(0.0)

    def test_set_value_zero(self):
        b = _bar(max_value=100.0)
        b.set_value(0.0)
        assert b.value == pytest.approx(0.0)

    def test_set_value_exact_max(self):
        b = _bar(max_value=100.0)
        b.set_value(100.0)
        assert b.value == pytest.approx(100.0)


# ── TestUpdate ────────────────────────────────────────────────────────────────
class TestUpdate:
    def test_smooth_display_moves_toward_value(self):
        b = _bar(value=100.0, smooth=True, smooth_speed=80.0)
        b._display_value = 0.0
        b.update(0.1)
        assert b._display_value > 0.0

    def test_smooth_display_snaps_when_close(self):
        """Quando diff ≤ step, display_value deve igualar value."""
        b = _bar(value=50.0, smooth=True, smooth_speed=1000.0)
        b._display_value = 49.99
        b.update(0.1)   # step=100 >> diff=0.01
        assert b._display_value == pytest.approx(50.0)

    def test_smooth_false_display_equals_value_instantly(self):
        b = _bar(value=80.0, smooth=False)
        b._display_value = 0.0
        b.update(0.016)
        assert b._display_value == pytest.approx(80.0)

    def test_smooth_display_decreases_when_value_lower(self):
        b = _bar(value=20.0, smooth=True, smooth_speed=80.0)
        b._display_value = 100.0
        b.update(0.1)
        assert b._display_value < 100.0

    def test_update_dt_zero_no_movement(self):
        b = _bar(value=100.0, smooth=True, smooth_speed=80.0)
        b._display_value = 0.0
        b.update(0.0)
        assert b._display_value == pytest.approx(0.0)

    def test_display_value_never_overshoots(self):
        b = _bar(value=50.0, smooth=True, smooth_speed=10000.0)
        b._display_value = 0.0
        b.update(10.0)
        assert b._display_value == pytest.approx(50.0)


# ── TestDrawSelf ────────────────────────────────────────────────────────────
class TestDrawSelf:
    def test_draw_calls_draw_rect_bg(self):
        b = _bar()
        b._draw_self(_screen())
        assert pygame.draw.rect.called

    def test_draw_bg_color_correct(self):
        b = _bar(color_bg=(10, 20, 30))
        b._draw_self(_screen())
        first_color = pygame.draw.rect.call_args_list[0][0][1]
        assert first_color == (10, 20, 30)

    def test_draw_fill_color_correct(self):
        b = _bar(color_fill=(80, 200, 100), value=50.0, max_value=100.0)
        b._display_value = 50.0
        b._draw_self(_screen())
        # 2ª chamada é o fill
        second_color = pygame.draw.rect.call_args_list[1][0][1]
        assert second_color == (80, 200, 100)

    def test_draw_no_fill_when_empty(self):
        b = _bar(value=0.0, max_value=100.0)
        b._display_value = 0.0
        b._draw_self(_screen())
        # sem fill_rect: apenas bg + borda = 2 chamadas
        assert pygame.draw.rect.call_count == 2

    def test_draw_with_border_three_calls(self):
        b = _bar(color_border=(0, 0, 0))
        b._display_value = 50.0
        b._draw_self(_screen())
        # bg + fill + borda = 3
        assert pygame.draw.rect.call_count == 3

    def test_draw_no_border_two_calls_when_full(self):
        b = _bar(color_border=None)
        b._display_value = 50.0
        b._draw_self(_screen())
        # bg + fill (sem borda)
        assert pygame.draw.rect.call_count == 2

    def test_show_text_calls_blit(self):
        scr = _screen()
        b = _bar(show_text=True)
        b._display_value = 50.0
        b._draw_self(scr)
        scr.blit_mock.assert_called_once()

    def test_show_text_false_no_blit(self):
        scr = _screen()
        b = _bar(show_text=False)
        b._display_value = 50.0
        b._draw_self(scr)
        scr.blit_mock.assert_not_called()

    def test_fill_width_proportional(self):
        """display_value=50, max=100, bar_width=200 → fill_w=100."""
        b = _bar(width=200, value=50.0, max_value=100.0)
        b._display_value = 50.0
        b._draw_self(_screen())
        fill_rect_arg = pygame.draw.rect.call_args_list[1][0][2]
        assert fill_rect_arg.width == 100

    def test_fill_width_zero_when_empty(self):
        b = _bar(width=200, value=0.0, max_value=100.0)
        b._display_value = 0.0
        b._draw_self(_screen())
        # fill não é desenhado — apenas 2 chamadas (bg + borda)
        assert pygame.draw.rect.call_count == 2

    def test_invisible_no_draw(self):
        scr = _screen()
        b = _bar()
        b.visible = False
        b.draw(scr)
        pygame.draw.rect.assert_not_called()
