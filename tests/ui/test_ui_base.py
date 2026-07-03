"""
tests/ui/test_ui_base.py
────────────────────────────────────────────────────────────────────────────
Testes unitários de engine/ui/base.py  (UIElement, Anchor, Pivot).

Estratégia de isolamento:
  - pygame é stubado via sys.modules antes do import.
  - _FakeRect e _FakeSurface reproduzem o mínimo necessário de
    pygame.Rect / pygame.Surface para get_rect, contains_point e draw.
  - Nenhuma janela, nenhum init, nenhum arquivo externo.
"""
from __future__ import annotations

import sys
from types import ModuleType
from unittest.mock import MagicMock

import pytest

# ── stub pygame ──────────────────────────────────────────────────────────────

class _FakeRect:
    def __init__(self, left=0, top=0, width=0, height=0):
        self.x      = left
        self.y      = top
        self.left   = left
        self.top    = top
        self.width  = width
        self.height = height
    def collidepoint(self, point):
        px, py = point
        return (self.x <= px < self.x + self.width and
                self.y <= py < self.y + self.height)


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
    _pg         = ModuleType("pygame")
    _pg.Surface = _FakeSurface
    _pg.Rect    = _FakeRect
    _event      = ModuleType("pygame.event")
    class _Event:
        def __init__(self, type, **kw):
            self.type = type
            self.__dict__.update(kw)
    _event.Event = _Event
    _pg.event    = _event
    sys.modules["pygame"]       = _pg
    sys.modules["pygame.event"] = _event
else:
    _pg    = sys.modules["pygame"]
    _Event = sys.modules["pygame.event"].Event

from engine.ui.base import Anchor, Pivot, UIElement  # noqa: E402


# ── helpers ──────────────────────────────────────────────────────────────────

def _screen(w=640, h=480):
    return _FakeSurface((w, h))


def _elem(**kw):
    """Cria UIElement com defaults sensatos."""
    kw.setdefault("width",  100)
    kw.setdefault("height",  40)
    return UIElement(**kw)


# ── TestAnchorEnum ────────────────────────────────────────────────────────────

class TestAnchorEnum:
    def test_all_nine_values(self):
        assert len(Anchor) == 9

    def test_top_left_exists(self):
        assert Anchor.TOP_LEFT is not None

    def test_middle_center_exists(self):
        assert Anchor.MIDDLE_CENTER is not None

    def test_bottom_right_exists(self):
        assert Anchor.BOTTOM_RIGHT is not None


class TestPivotEnum:
    def test_all_nine_values(self):
        assert len(Pivot) == 9

    def test_middle_center_exists(self):
        assert Pivot.MIDDLE_CENTER is not None


# ── TestUIElementInit ─────────────────────────────────────────────────────────

class TestUIElementInit:
    def test_defaults_xy_zero(self):
        e = UIElement()
        assert e.x == 0.0 and e.y == 0.0

    def test_defaults_wh_zero(self):
        e = UIElement()
        assert e.width == 0.0 and e.height == 0.0

    def test_defaults_visible_true(self):
        assert UIElement().visible is True

    def test_defaults_no_parent(self):
        assert UIElement().parent is None

    def test_defaults_no_children(self):
        assert UIElement().children == []

    def test_custom_xy(self):
        e = UIElement(x=10.0, y=20.0)
        assert e.x == 10.0 and e.y == 20.0

    def test_custom_wh(self):
        e = UIElement(width=200, height=50)
        assert e.width == 200 and e.height == 50

    def test_custom_anchor(self):
        e = UIElement(anchor=Anchor.MIDDLE_CENTER)
        assert e.anchor is Anchor.MIDDLE_CENTER

    def test_custom_pivot(self):
        e = UIElement(pivot=Pivot.BOTTOM_RIGHT)
        assert e.pivot is Pivot.BOTTOM_RIGHT

    def test_name_stored(self):
        e = UIElement(name="hp_bar")
        assert e.name == "hp_bar"


# ── TestHierarchy ─────────────────────────────────────────────────────────────

class TestHierarchy:
    def test_add_child_appends(self):
        parent = _elem()
        child  = _elem()
        parent.add_child(child)
        assert child in parent.children

    def test_add_child_sets_parent(self):
        parent = _elem()
        child  = _elem()
        parent.add_child(child)
        assert child.parent is parent

    def test_add_child_returns_child(self):
        parent = _elem()
        child  = _elem()
        assert parent.add_child(child) is child

    def test_remove_child(self):
        parent = _elem()
        child  = _elem()
        parent.add_child(child)
        parent.remove_child(child)
        assert child not in parent.children

    def test_remove_child_clears_parent(self):
        parent = _elem()
        child  = _elem()
        parent.add_child(child)
        parent.remove_child(child)
        assert child.parent is None

    def test_remove_nonexistent_child_no_crash(self):
        parent = _elem()
        parent.remove_child(_elem())  # não deve lançar

    def test_multiple_children(self):
        parent = _elem()
        for _ in range(5):
            parent.add_child(_elem())
        assert len(parent.children) == 5


# ── TestGetRect ───────────────────────────────────────────────────────────────

class TestGetRect:
    def test_top_left_anchor_origin(self):
        """TOP_LEFT anchor, offset (0,0): rect deve começar em (0,0)."""
        e = _elem(x=0, y=0, anchor=Anchor.TOP_LEFT, pivot=Pivot.TOP_LEFT)
        r = e.get_rect(_screen(640, 480))
        assert r.x == 0 and r.y == 0

    def test_top_left_anchor_with_offset(self):
        e = _elem(x=50, y=30, anchor=Anchor.TOP_LEFT, pivot=Pivot.TOP_LEFT)
        r = e.get_rect(_screen(640, 480))
        assert r.x == 50 and r.y == 30

    def test_middle_center_anchor_no_offset(self):
        """MIDDLE_CENTER anchor, pivot TOP_LEFT: rect começa no centro da tela."""
        e = _elem(x=0, y=0, width=100, height=40,
                  anchor=Anchor.MIDDLE_CENTER, pivot=Pivot.TOP_LEFT)
        r = e.get_rect(_screen(640, 480))
        assert r.x == 320 and r.y == 240

    def test_middle_center_pivot_centers_element(self):
        """MIDDLE_CENTER anchor + MIDDLE_CENTER pivot: centra o elemento."""
        e = _elem(x=0, y=0, width=100, height=40,
                  anchor=Anchor.MIDDLE_CENTER, pivot=Pivot.MIDDLE_CENTER)
        r = e.get_rect(_screen(640, 480))
        assert r.x == 320 - 50 and r.y == 240 - 20

    def test_bottom_right_anchor(self):
        e = _elem(x=0, y=0, width=100, height=40,
                  anchor=Anchor.BOTTOM_RIGHT, pivot=Pivot.BOTTOM_RIGHT)
        r = e.get_rect(_screen(640, 480))
        assert r.x == 640 - 100 and r.y == 480 - 40

    def test_width_height_in_rect(self):
        e = _elem(width=200, height=80)
        r = e.get_rect(_screen())
        assert r.width == 200 and r.height == 80

    def test_natural_width_used_when_zero(self):
        """width=0 → usa _natural_width (100 por padrão)."""
        e = UIElement(width=0, height=0)
        r = e.get_rect(_screen())
        assert r.width == 100

    def test_natural_height_used_when_zero(self):
        e = UIElement(width=0, height=0)
        r = e.get_rect(_screen())
        assert r.height == 30

    def test_child_anchored_to_parent(self):
        """Filho ancorado em MIDDLE_CENTER usa rect do pai como container."""
        parent = _elem(x=50, y=50, width=200, height=100,
                       anchor=Anchor.TOP_LEFT, pivot=Pivot.TOP_LEFT)
        child  = UIElement(x=0, y=0, width=20, height=10,
                           anchor=Anchor.MIDDLE_CENTER, pivot=Pivot.MIDDLE_CENTER)
        parent.add_child(child)
        screen = _screen()
        pr     = parent.get_rect(screen)
        cr     = child.get_rect(screen)
        # centro do pai
        cx = pr.x + pr.width  // 2
        cy = pr.y + pr.height // 2
        assert cr.x == cx - 10 and cr.y == cy - 5


# ── TestContainsPoint ─────────────────────────────────────────────────────────

class TestContainsPoint:
    def test_inside_returns_true(self):
        e = _elem(x=0, y=0, width=100, height=50)
        assert e.contains_point((50, 25), _screen()) is True

    def test_outside_returns_false(self):
        e = _elem(x=0, y=0, width=100, height=50)
        assert e.contains_point((200, 200), _screen()) is False

    def test_edge_top_left_inside(self):
        e = _elem(x=0, y=0, width=100, height=50)
        assert e.contains_point((0, 0), _screen()) is True

    def test_edge_bottom_right_outside(self):
        """collidepoint usa [left, right) × [top, bottom)."""
        e = _elem(x=0, y=0, width=100, height=50)
        assert e.contains_point((100, 50), _screen()) is False


# ── TestVisibility ────────────────────────────────────────────────────────────

class TestVisibility:
    def test_draw_invisible_skips_children(self):
        parent = _elem()
        parent.visible = False
        child_draw = MagicMock()
        child = _elem()
        child.draw = child_draw
        parent.add_child(child)
        parent.draw(_screen())
        child_draw.assert_not_called()

    def test_update_invisible_skips_children(self):
        parent = _elem()
        parent.visible = False
        child_update = MagicMock()
        child = _elem()
        child.update = child_update
        parent.add_child(child)
        parent.update(0.016)
        child_update.assert_not_called()

    def test_handle_event_invisible_returns_false(self):
        e = _elem()
        e.visible = False
        ev = MagicMock()
        assert e.handle_event(ev, _screen()) is False

    def test_draw_visible_calls_draw_self(self):
        e = _elem()
        e._draw_self = MagicMock()
        e.draw(_screen())
        e._draw_self.assert_called_once()


# ── TestHandleEvent ───────────────────────────────────────────────────────────

class TestHandleEvent:
    def test_returns_false_by_default(self):
        e = _elem()
        ev = MagicMock()
        assert e.handle_event(ev, _screen()) is False

    def test_child_consuming_event_stops_propagation(self):
        parent = _elem()
        child  = _elem()
        child.handle_event = MagicMock(return_value=True)
        parent.add_child(child)
        result = parent.handle_event(MagicMock(), _screen())
        assert result is True

    def test_children_iterated_in_reverse(self):
        """Último filho adicionado tem prioridade."""
        parent = _elem()
        order  = []
        for i in range(3):
            c = _elem(name=str(i))
            c.handle_event = MagicMock(
                side_effect=lambda ev, s, idx=i: order.append(idx) or False
            )
            parent.add_child(c)
        parent.handle_event(MagicMock(), _screen())
        assert order == [2, 1, 0]


# ── TestUpdate ────────────────────────────────────────────────────────────────

class TestUpdate:
    def test_update_propagates_to_children(self):
        parent = _elem()
        child  = _elem()
        child.update = MagicMock()
        parent.add_child(child)
        parent.update(0.016)
        child.update.assert_called_once_with(0.016)

    def test_update_calls_all_children(self):
        parent = _elem()
        updates = []
        for i in range(4):
            c = _elem()
            c.update = MagicMock(side_effect=lambda dt, idx=i: updates.append(idx))
            parent.add_child(c)
        parent.update(0.016)
        assert len(updates) == 4


# ── TestRepr ──────────────────────────────────────────────────────────────────

class TestRepr:
    def test_repr_contains_class(self):
        assert "UIElement" in repr(UIElement())

    def test_repr_contains_name(self):
        e = UIElement(name="test_elem")
        assert "test_elem" in repr(e)

    def test_repr_contains_dimensions(self):
        e = UIElement(width=200, height=50)
        r = repr(e)
        assert "200" in r and "50" in r
