"""
tests/ui/test_label.py
────────────────────────────────────────────────────────────────────────────
Testes unitários de engine/ui/label.py (Label).

Estratégia de isolamento:
  - pygame stubado via sys.modules antes do import.
  - _FakeFont.render() retorna _FakeSurf(90, 24) fixo — dimensionação
    de texto determinística.
  - screen.blit é MagicMock para rastrear chamadas.
  - Nenhuma janela / init pygame real.
"""
from __future__ import annotations

import sys
from types import ModuleType
from unittest.mock import MagicMock, call

import pytest

# ── stub pygame ──────────────────────────────────────────────────────────────

TEXT_W, TEXT_H = 90, 24


class _FakeSurf:
    def __init__(self, w=TEXT_W, h=TEXT_H):
        self._w, self._h = w, h
    def get_width(self):  return self._w
    def get_height(self): return self._h
    @property
    def topleft(self): return (0, 0)


class _FakeFont:
    def render(self, text, aa, color):
        return _FakeSurf()
    def size(self, text):
        return (TEXT_W, TEXT_H)


class _FakeScreen:
    def __init__(self, w=640, h=480):
        self._w, self._h = w, h
        self.blit = MagicMock()
    def get_rect(self):
        class R:
            x = 0; y = 0; width = 640; height = 480
        return R()
    def get_width(self):  return self._w
    def get_height(self): return self._h


if "pygame" not in sys.modules:
    _pg          = ModuleType("pygame")
    _font_mod    = ModuleType("pygame.font")
    _font_mod.SysFont = MagicMock(return_value=_FakeFont())
    _pg.font     = _font_mod
    _pg.Surface  = _FakeScreen
    class _FakeRect:
        def __init__(self, x=0, y=0, w=0, h=0):
            self.x=x; self.y=y; self.width=w; self.height=h
            self.left=x; self.top=y
            self.topleft=(x,y)
        def collidepoint(self, p): return False
    _pg.Rect     = _FakeRect
    sys.modules["pygame"]      = _pg
    sys.modules["pygame.font"] = _font_mod
else:
    _pg       = sys.modules["pygame"]
    _font_mod = sys.modules.get("pygame.font", _pg.font)

from engine.ui.label import Label  # noqa: E402


# ── helpers ────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def reset_font_mock():
    _font_mod.SysFont.reset_mock()
    _font_mod.SysFont.return_value = _FakeFont()
    yield


def _screen():
    return _FakeScreen()


def _lbl(**kw):
    kw.setdefault("text", "Hello")
    return Label(**kw)


# ── TestLabelInit ───────────────────────────────────────────────────────────
class TestLabelInit:
    def test_text_stored(self):
        assert _lbl(text="Score: 0").text == "Score: 0"

    def test_default_text_empty(self):
        assert Label().text == ""

    def test_font_size_stored(self):
        assert _lbl(font_size=32).font_size == 32

    def test_color_stored(self):
        assert _lbl(color=(255, 0, 0)).color == (255, 0, 0)

    def test_bold_stored(self):
        assert _lbl(bold=True).bold is True

    def test_italic_stored(self):
        assert _lbl(italic=True).italic is True

    def test_shadow_default_false(self):
        assert _lbl().shadow is False

    def test_dirty_on_init(self):
        assert _lbl()._dirty is True

    def test_surface_none_on_init(self):
        assert _lbl()._surface is None

    def test_font_none_on_init(self):
        assert _lbl()._font is None


# ── TestSetText ───────────────────────────────────────────────────────────────
class TestSetText:
    def test_set_text_updates_text(self):
        l = _lbl(text="old")
        l.set_text("new")
        assert l.text == "new"

    def test_set_text_marks_dirty(self):
        l = _lbl()
        l._dirty = False
        l.set_text("changed")
        assert l._dirty is True

    def test_set_same_text_no_dirty(self):
        l = _lbl(text="same")
        l._dirty = False
        l.set_text("same")
        assert l._dirty is False

    def test_set_color_marks_dirty(self):
        l = _lbl()
        l._dirty = False
        l.set_color((0, 0, 0))
        assert l._dirty is True

    def test_set_color_updates_color(self):
        l = _lbl()
        l.set_color((128, 64, 32))
        assert l.color == (128, 64, 32)


# ── TestRebuild ───────────────────────────────────────────────────────────────
class TestRebuild:
    def test_rebuild_clears_dirty(self):
        l = _lbl()
        l._rebuild()
        assert l._dirty is False

    def test_rebuild_sets_surface(self):
        l = _lbl()
        l._rebuild()
        assert l._surface is not None

    def test_rebuild_creates_font(self):
        l = _lbl()
        l._rebuild()
        assert l._font is not None

    def test_double_draw_no_double_rebuild(self):
        """Segunda chamada a _draw_self não deve recriar o surface."""
        l = _lbl()
        scr = _screen()
        l._draw_self(scr)
        surf_after_first = l._surface
        l._draw_self(scr)
        assert l._surface is surf_after_first

    def test_set_text_triggers_rebuild_on_next_draw(self):
        l = _lbl(text="A")
        scr = _screen()
        l._draw_self(scr)       # constrói pela 1ª vez
        l.set_text("B")         # marca dirty
        l._draw_self(scr)       # deve reconstruir
        assert l.text == "B" and l._dirty is False


# ── TestNaturalSize ───────────────────────────────────────────────────────────
class TestNaturalSize:
    def test_natural_width_from_surface(self):
        l = _lbl()
        assert l._natural_width(_screen()) == TEXT_W

    def test_natural_height_from_surface(self):
        l = _lbl()
        assert l._natural_height(_screen()) == TEXT_H

    def test_natural_width_triggers_rebuild_if_dirty(self):
        l = _lbl()
        assert l._dirty is True
        l._natural_width(_screen())
        assert l._dirty is False

    def test_natural_height_triggers_rebuild_if_dirty(self):
        l = _lbl()
        l._natural_height(_screen())
        assert l._dirty is False


# ── TestDrawSelf ────────────────────────────────────────────────────────────
class TestDrawSelf:
    def test_draw_calls_blit(self):
        scr = _screen()
        l = _lbl()
        l._draw_self(scr)
        scr.blit.assert_called()

    def test_draw_rebuilds_when_dirty(self):
        l = _lbl()
        scr = _screen()
        assert l._surface is None
        l._draw_self(scr)
        assert l._surface is not None

    def test_draw_without_shadow_one_blit(self):
        scr = _screen()
        l = _lbl(shadow=False)
        l._draw_self(scr)
        assert scr.blit.call_count == 1

    def test_draw_with_shadow_two_blits(self):
        scr = _screen()
        l = _lbl(shadow=True)
        l._draw_self(scr)
        assert scr.blit.call_count == 2

    def test_shadow_blit_offset_by_one(self):
        """A sombra é deslocada (rect.x+1, rect.y+1)."""
        scr = _screen()
        l = _lbl(shadow=True)
        l._draw_self(scr)
        shadow_pos = scr.blit.call_args_list[0][0][1]
        text_pos   = scr.blit.call_args_list[1][0][1]
        # text_pos pode ser uma tupla ou topleft; shadow deve ser +1
        assert shadow_pos[0] == text_pos[0] + 1 or shadow_pos[1] == text_pos[1] + 1

    def test_draw_invisible_no_blit(self):
        scr = _screen()
        l = _lbl()
        l.visible = False
        l.draw(scr)
        scr.blit.assert_not_called()

    def test_draw_empty_text_no_crash(self):
        scr = _screen()
        l = Label(text="")
        l._draw_self(scr)   # não deve lançar
