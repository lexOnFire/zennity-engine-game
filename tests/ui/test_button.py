"""
tests/ui/test_button.py
────────────────────────────────────────────────────────────────────────────
Testes unitários de engine/ui/button.py (Button).

Estratégia de isolamento:
  - pygame stubado via sys.modules (Surface, Rect, font, draw, eventos).
  - _FakeFont.size() retorna um tamanho fixo (80, 20) para calcular
    natural_width/height de forma determinística.
  - Eventos são objetos simples com .type, .button, .pos.
  - pygame.draw.rect é MagicMock — chamadas rastreadas sem SDL.
"""
from __future__ import annotations

import sys
from types import ModuleType
from unittest.mock import MagicMock, call

import pytest

# ── stub pygame ──────────────────────────────────────────────────────────────

MOUSEMOTION     = 1024
MOUSEBUTTONDOWN = 1025
MOUSEBUTTONUP   = 1026


class _FakeRect:
    def __init__(self, x=0, y=0, w=0, h=0):
        self.x = x; self.y = y; self.width = w; self.height = h
        self.left = x; self.top = y
    def collidepoint(self, pos):
        px, py = pos
        return self.x <= px < self.x + self.width and self.y <= py < self.y + self.height
    def inflate(self, dw, dh):
        return _FakeRect(self.x - dw//2, self.y - dh//2,
                         self.width + dw, self.height + dh)


class _FakeTextSurf:
    def get_width(self):  return 80
    def get_height(self): return 20


class _FakeFont:
    def size(self, text): return (80, 20)
    def render(self, text, aa, color): return _FakeTextSurf()


class _FakeSurface:
    SRCALPHA = 0x00010000
    def __init__(self, size=(640, 480)):
        self._w, self._h = size
        self.blit = MagicMock()
        self.fill = MagicMock()
    def get_rect(self):
        return _FakeRect(0, 0, self._w, self._h)
    def get_width(self):  return self._w
    def get_height(self): return self._h


if "pygame" not in sys.modules:
    _pg              = ModuleType("pygame")
    _pg.Surface      = _FakeSurface
    _pg.Rect         = _FakeRect
    _pg.MOUSEMOTION      = MOUSEMOTION
    _pg.MOUSEBUTTONDOWN  = MOUSEBUTTONDOWN
    _pg.MOUSEBUTTONUP    = MOUSEBUTTONUP
    _font_mod = ModuleType("pygame.font")
    _font_mod.SysFont = MagicMock(return_value=_FakeFont())
    _pg.font      = _font_mod
    _draw         = ModuleType("pygame.draw")
    _draw.rect    = MagicMock()
    _pg.draw      = _draw
    _event_mod    = ModuleType("pygame.event")
    _pg.event     = _event_mod
    sys.modules["pygame"]       = _pg
    sys.modules["pygame.font"]  = _font_mod
    sys.modules["pygame.draw"]  = _draw
    sys.modules["pygame.event"] = _event_mod
else:
    _pg       = sys.modules["pygame"]
    _font_mod = sys.modules.get("pygame.font", _pg.font)
    _draw     = sys.modules.get("pygame.draw", _pg.draw)

from engine.ui.button import Button  # noqa: E402


# ── helpers ────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def reset_draw(monkeypatch):
    global _draw
    if not hasattr(_pg, "draw"):
        _pg.draw = ModuleType("pygame.draw")
    _draw = _pg.draw
    if not hasattr(getattr(_draw, "rect", None), "reset_mock"):
        monkeypatch.setattr(_draw, "rect", MagicMock(), raising=False)
    if not hasattr(getattr(_font_mod, "SysFont", None), "reset_mock"):
        monkeypatch.setattr(_font_mod, "SysFont", MagicMock(), raising=False)
    _draw.rect.reset_mock()
    _font_mod.SysFont.reset_mock()
    _font_mod.SysFont.return_value = _FakeFont()
    yield
    _draw.rect.reset_mock()


def _screen(w=640, h=480):
    return _FakeSurface((w, h))


def _btn(**kw):
    kw.setdefault("x", 0)
    kw.setdefault("y", 0)
    kw.setdefault("width", 120)
    kw.setdefault("height", 40)
    kw.setdefault("text", "OK")
    return Button(**kw)


def _event(type_, pos=(0, 0), button=1):
    e = MagicMock()
    e.type   = type_
    e.pos    = pos
    e.button = button
    return e


# ────────────────────────────────────────────────────────────────────────────
class TestButtonInit:
    def test_text_stored(self):
        assert _btn(text="Play").text == "Play"

    def test_enabled_default_true(self):
        assert _btn().enabled is True

    def test_hovered_default_false(self):
        assert _btn()._hovered is False

    def test_pressed_default_false(self):
        assert _btn()._pressed is False

    def test_hover_t_default_zero(self):
        assert _btn()._hover_t == pytest.approx(0.0)

    def test_on_click_default_none(self):
        assert _btn().on_click is None

    def test_custom_colors_stored(self):
        b = Button(color_normal=(1, 2, 3))
        assert b.color_normal == (1, 2, 3)

    def test_border_radius_stored(self):
        b = Button(border_radius=10)
        assert b.border_radius == 10

    def test_padding_stored(self):
        b = Button(padding_x=20.0, padding_y=8.0)
        assert b.padding_x == 20.0 and b.padding_y == 8.0


class TestNaturalSize:
    def test_natural_width_text_plus_padding(self):
        """text_width(80) + 2*padding_x(18) = 116."""
        b = Button(padding_x=18.0)
        assert b._natural_width(_screen()) == pytest.approx(116.0)

    def test_natural_height_text_plus_padding(self):
        """text_height(20) + 2*padding_y(10) = 40."""
        b = Button(padding_y=10.0)
        assert b._natural_height(_screen()) == pytest.approx(40.0)

    def test_custom_padding_changes_natural_size(self):
        b = Button(padding_x=30.0)
        assert b._natural_width(_screen()) == pytest.approx(140.0)


class TestHandleEventMouseMotion:
    def test_hover_true_when_over_rect(self):
        b = _btn(x=0, y=0, width=120, height=40)
        b.handle_event(_event(MOUSEMOTION, pos=(60, 20)), _screen())
        assert b._hovered is True

    def test_hover_false_when_outside(self):
        b = _btn(x=0, y=0, width=120, height=40)
        b._hovered = True
        b.handle_event(_event(MOUSEMOTION, pos=(200, 200)), _screen())
        assert b._hovered is False

    def test_hover_invisible_ignored(self):
        b = _btn()
        b.visible = False
        b.handle_event(_event(MOUSEMOTION, pos=(60, 20)), _screen())
        assert b._hovered is False

    def test_hover_disabled_ignored(self):
        b = _btn(enabled=False)
        b.handle_event(_event(MOUSEMOTION, pos=(60, 20)), _screen())
        assert b._hovered is False


class TestHandleEventMouseDown:
    def test_pressed_true_on_mousedown(self):
        b = _btn(x=0, y=0, width=120, height=40)
        b.handle_event(_event(MOUSEBUTTONDOWN, pos=(60, 20)), _screen())
        assert b._pressed is True

    def test_pressed_false_when_outside(self):
        b = _btn(x=0, y=0, width=120, height=40)
        b.handle_event(_event(MOUSEBUTTONDOWN, pos=(300, 300)), _screen())
        assert b._pressed is False

    def test_mousedown_returns_true_when_hit(self):
        b = _btn(x=0, y=0, width=120, height=40)
        result = b.handle_event(_event(MOUSEBUTTONDOWN, pos=(60, 20)), _screen())
        assert result is True

    def test_mousedown_returns_false_when_miss(self):
        b = _btn(x=0, y=0, width=120, height=40)
        result = b.handle_event(_event(MOUSEBUTTONDOWN, pos=(300, 300)), _screen())
        assert result is False

    def test_right_click_ignored(self):
        b = _btn(x=0, y=0, width=120, height=40)
        b.handle_event(_event(MOUSEBUTTONDOWN, pos=(60, 20), button=3), _screen())
        assert b._pressed is False

    def test_disabled_button_ignores_mousedown(self):
        b = _btn(x=0, y=0, width=120, height=40, enabled=False)
        b.handle_event(_event(MOUSEBUTTONDOWN, pos=(60, 20)), _screen())
        assert b._pressed is False


class TestHandleEventMouseUp:
    def test_on_click_called_on_valid_release(self):
        cb = MagicMock()
        b = _btn(x=0, y=0, width=120, height=40, on_click=cb)
        b._pressed = True
        b.handle_event(_event(MOUSEBUTTONUP, pos=(60, 20)), _screen())
        cb.assert_called_once()

    def test_on_click_not_called_when_released_outside(self):
        cb = MagicMock()
        b = _btn(x=0, y=0, width=120, height=40, on_click=cb)
        b._pressed = True
        b.handle_event(_event(MOUSEBUTTONUP, pos=(300, 300)), _screen())
        cb.assert_not_called()

    def test_on_click_not_called_if_not_pressed(self):
        cb = MagicMock()
        b = _btn(x=0, y=0, width=120, height=40, on_click=cb)
        b._pressed = False
        b.handle_event(_event(MOUSEBUTTONUP, pos=(60, 20)), _screen())
        cb.assert_not_called()

    def test_pressed_cleared_on_mouse_up_inside(self):
        b = _btn(x=0, y=0, width=120, height=40)
        b._pressed = True
        b.handle_event(_event(MOUSEBUTTONUP, pos=(60, 20)), _screen())
        assert b._pressed is False

    def test_pressed_cleared_on_mouse_up_outside(self):
        b = _btn(x=0, y=0, width=120, height=40)
        b._pressed = True
        b.handle_event(_event(MOUSEBUTTONUP, pos=(300, 300)), _screen())
        assert b._pressed is False

    def test_mouse_up_returns_true_on_valid_click(self):
        b = _btn(x=0, y=0, width=120, height=40)
        b._pressed = True
        result = b.handle_event(_event(MOUSEBUTTONUP, pos=(60, 20)), _screen())
        assert result is True

    def test_no_on_click_no_error(self):
        b = _btn(x=0, y=0, width=120, height=40, on_click=None)
        b._pressed = True
        b.handle_event(_event(MOUSEBUTTONUP, pos=(60, 20)), _screen())  # sem crash


class TestUpdate:
    def test_hover_t_increases_toward_one_when_hovered(self):
        b = _btn()
        b._hovered = True
        b._hover_t = 0.0
        b.update(0.1)
        assert b._hover_t > 0.0

    def test_hover_t_decreases_toward_zero_when_not_hovered(self):
        b = _btn()
        b._hovered = False
        b._hover_t = 1.0
        b.update(0.1)
        assert b._hover_t < 1.0

    def test_hover_t_capped_near_one(self):
        b = _btn()
        b._hovered = True
        b._hover_t = 0.0
        for _ in range(200):
            b.update(1.0)
        assert b._hover_t <= 1.0 + 1e-6

    def test_update_dt_zero_no_change(self):
        b = _btn()
        b._hovered = True
        b._hover_t = 0.5
        b.update(0.0)
        assert b._hover_t == pytest.approx(0.5)


class TestLerpColor:
    def test_lerp_at_zero_returns_a(self):
        b = _btn()
        assert b._lerp_color((10, 20, 30), (100, 200, 300), 0.0) == (10, 20, 30)

    def test_lerp_at_one_returns_b(self):
        b = _btn()
        assert b._lerp_color((10, 20, 30), (110, 120, 130), 1.0) == (110, 120, 130)

    def test_lerp_midpoint(self):
        b = _btn()
        result = b._lerp_color((0, 0, 0), (100, 100, 100), 0.5)
        assert result == (50, 50, 50)


class TestDrawSelf:
    def test_draw_calls_pygame_draw_rect(self):
        b = _btn(x=0, y=0, width=120, height=40)
        b._draw_self(_screen())
        assert _draw.rect.called

    def test_disabled_uses_color_disabled(self):
        b = _btn(x=0, y=0, width=120, height=40,
                 color_disabled=(99, 99, 99), enabled=False)
        b._draw_self(_screen())
        first_call_color = _draw.rect.call_args_list[0][0][1]
        assert first_call_color == (99, 99, 99)

    def test_pressed_uses_color_pressed(self):
        b = _btn(x=0, y=0, width=120, height=40, color_pressed=(1, 2, 3))
        b._pressed = True
        b._draw_self(_screen())
        first_call_color = _draw.rect.call_args_list[0][0][1]
        assert first_call_color == (1, 2, 3)

    def test_normal_state_bg_color_is_lerp(self):
        """hover_t=0 → fundo deve ser color_normal."""
        b = _btn(x=0, y=0, width=120, height=40,
                 color_normal=(60, 80, 120))
        b._hover_t = 0.0
        b._draw_self(_screen())
        first_call_color = _draw.rect.call_args_list[0][0][1]
        assert first_call_color == (60, 80, 120)

    def test_pressed_extra_draw_rect_called(self):
        """Estado pressed deve chamar draw.rect extra (sombra interna)."""
        b = _btn(x=0, y=0, width=120, height=40)
        b._pressed = True
        b._draw_self(_screen())
        # fundo + borda + sombra interna = pelo menos 3 chamadas
        assert _draw.rect.call_count >= 3

    def test_screen_blit_called_for_text(self):
        screen = _screen()
        b = _btn(x=0, y=0, width=120, height=40)
        b._draw_self(screen)
        screen.blit.assert_called_once()

    def test_pressed_text_offset_y(self):
        """Quando pressionado, o texto deve ser deslocado 1px para baixo."""
        screen = _screen()
        b = _btn(x=0, y=0, width=120, height=40)
        # sem press
        b._draw_self(screen)
        ty_normal = screen.blit.call_args[0][1][1]
        screen.blit.reset_mock()
        # com press
        b._pressed = True
        b._draw_self(screen)
        ty_pressed = screen.blit.call_args[0][1][1]
        assert ty_pressed == ty_normal + 1
