"""
tests/test_input.py
────────────────────────────────────────────────────────────────────────────
Testes unitários de engine/input.py (Input).

Estratégia de isolamento:
  - pygame completo é stubado: key.get_pressed, mouse.get_pressed,
    mouse.get_pos, mouse.get_rel e todas as constantes K_* e KMOD_*
    são definidas como MagicMock ou inteiros fixos.
  - _FakeKeys simula a ScancodeWrapper: indexação por inteiro,
    retorna True/False controlado pelo teste, e bool() retorna True
    quando há ao menos uma tecla pressionada.
  - Cada teste injeta _keys_current/_keys_previous diretamente
    nos atributos de classe e chama os métodos sem passar por
    pygame.key.get_pressed(), garantindo isolamento total.
"""
from __future__ import annotations

import sys
from types import ModuleType
from unittest.mock import MagicMock

import pytest

# ── stub completo do pygame ───────────────────────────────────────────────────────

class _FakeKeys:
    """Simula pygame.key.ScancodeWrapper indexada por código de tecla."""
    def __init__(self, pressed: set | None = None):
        self._pressed = pressed or set()
    def __getitem__(self, key): return key in self._pressed
    def __bool__(self):         return bool(self._pressed)


def _build_pygame_stub():
    pg = ModuleType("pygame")

    # key
    key_mod = ModuleType("pygame.key")
    key_mod.ScancodeWrapper = _FakeKeys
    key_mod.get_pressed     = MagicMock(return_value=_FakeKeys())
    pg.key = key_mod

    # mouse
    mouse_mod = ModuleType("pygame.mouse")
    mouse_mod.get_pressed = MagicMock(return_value=(False, False, False))
    mouse_mod.get_pos     = MagicMock(return_value=(0, 0))
    mouse_mod.get_rel     = MagicMock(return_value=(0, 0))
    pg.mouse = mouse_mod

    # Constantes de teclado usadas internamente
    for name, val in [
        ("K_LEFT", 276), ("K_RIGHT", 275), ("K_UP", 273), ("K_DOWN", 274),
        ("K_a", 97),  ("K_d", 100), ("K_w", 119), ("K_s", 115),
    ]:
        setattr(pg, name, val)

    sys.modules["pygame"]       = pg
    sys.modules["pygame.key"]   = key_mod
    sys.modules["pygame.mouse"] = mouse_mod
    return pg


if "pygame" not in sys.modules:
    _pg = _build_pygame_stub()
else:
    _pg = sys.modules["pygame"]

from engine.input import Input  # noqa: E402

# Constantes locais (usamos os mesmos valores do stub)
K_LEFT  = _pg.K_LEFT;  K_RIGHT = _pg.K_RIGHT
K_UP    = _pg.K_UP;    K_DOWN  = _pg.K_DOWN
K_a     = _pg.K_a;     K_d     = _pg.K_d
K_w     = _pg.K_w;     K_s     = _pg.K_s


# ── fixture de isolamento ────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def reset_input():
    """Garante estado limpo (nenhuma tecla pressionada) antes de cada teste."""
    Input._keys_current  = _FakeKeys()
    Input._keys_previous = _FakeKeys()
    Input._mouse_current  = (False, False, False)
    Input._mouse_previous = (False, False, False)
    Input._mouse_position = (0, 0)
    Input._mouse_rel      = (0, 0)
    yield
    Input._keys_current  = _FakeKeys()
    Input._keys_previous = _FakeKeys()
    Input._mouse_current  = (False, False, False)
    Input._mouse_previous = (False, False, False)


# ── helpers ────────────────────────────────────────────────────────────────

def _press(*keys):   return _FakeKeys(set(keys))
def _release():      return _FakeKeys()


# ── TestGetKey ────────────────────────────────────────────────────────────────
class TestGetKey:
    def test_key_held_returns_true(self):
        Input._keys_current = _press(K_LEFT)
        assert Input.get_key(K_LEFT) is True

    def test_key_not_pressed_returns_false(self):
        assert Input.get_key(K_LEFT) is False

    def test_different_key_not_affected(self):
        Input._keys_current = _press(K_LEFT)
        assert Input.get_key(K_RIGHT) is False

    def test_empty_state_returns_false(self):
        Input._keys_current = _FakeKeys()
        assert Input.get_key(K_UP) is False

    def test_invalid_key_index_returns_false(self):
        """Chave fora do range não deve lançar."""
        # _FakeKeys.__getitem__ retorna False para chaves ausentes
        assert Input.get_key(99999) is False

    def test_multiple_keys_pressed(self):
        Input._keys_current = _press(K_LEFT, K_RIGHT)
        assert Input.get_key(K_LEFT) is True
        assert Input.get_key(K_RIGHT) is True


# ── TestGetKeyDown ─────────────────────────────────────────────────────────────
class TestGetKeyDown:
    def test_key_down_true_when_pressed_this_frame(self):
        Input._keys_previous = _release()
        Input._keys_current  = _press(K_LEFT)
        assert Input.get_key_down(K_LEFT) is True

    def test_key_down_false_when_held(self):
        """Segurado desde o frame anterior não é key_down."""
        Input._keys_previous = _press(K_LEFT)
        Input._keys_current  = _press(K_LEFT)
        assert Input.get_key_down(K_LEFT) is False

    def test_key_down_false_when_not_pressed(self):
        assert Input.get_key_down(K_LEFT) is False

    def test_key_down_false_when_released_this_frame(self):
        Input._keys_previous = _press(K_LEFT)
        Input._keys_current  = _release()
        assert Input.get_key_down(K_LEFT) is False

    def test_key_down_empty_states_no_crash(self):
        Input._keys_current  = _FakeKeys()
        Input._keys_previous = _FakeKeys()
        assert Input.get_key_down(K_UP) is False

    def test_key_down_only_for_correct_key(self):
        Input._keys_previous = _release()
        Input._keys_current  = _press(K_LEFT)
        assert Input.get_key_down(K_RIGHT) is False


# ── TestGetKeyUp ────────────────────────────────────────────────────────────────
class TestGetKeyUp:
    def test_key_up_true_when_released_this_frame(self):
        Input._keys_previous = _press(K_LEFT)
        Input._keys_current  = _release()
        assert Input.get_key_up(K_LEFT) is True

    def test_key_up_false_when_still_held(self):
        Input._keys_previous = _press(K_LEFT)
        Input._keys_current  = _press(K_LEFT)
        assert Input.get_key_up(K_LEFT) is False

    def test_key_up_false_when_never_pressed(self):
        assert Input.get_key_up(K_LEFT) is False

    def test_key_up_false_when_just_pressed(self):
        Input._keys_previous = _release()
        Input._keys_current  = _press(K_LEFT)
        assert Input.get_key_up(K_LEFT) is False

    def test_key_up_empty_states_no_crash(self):
        assert Input.get_key_up(K_DOWN) is False

    def test_key_up_only_for_correct_key(self):
        Input._keys_previous = _press(K_LEFT)
        Input._keys_current  = _release()
        assert Input.get_key_up(K_RIGHT) is False


# ── TestMouse ──────────────────────────────────────────────────────────────────
class TestMouse:
    def test_mouse_position_default(self):
        assert Input.get_mouse_position() == (0, 0)

    def test_mouse_position_stored(self):
        Input._mouse_position = (320, 240)
        assert Input.get_mouse_position() == (320, 240)

    def test_mouse_rel_default(self):
        assert Input.get_mouse_rel() == (0, 0)

    def test_mouse_rel_stored(self):
        Input._mouse_rel = (5, -3)
        assert Input.get_mouse_rel() == (5, -3)

    def test_mouse_button_held(self):
        Input._mouse_current = (True, False, False)
        assert Input.get_mouse_button(0) is True

    def test_mouse_button_not_held(self):
        assert Input.get_mouse_button(0) is False

    def test_mouse_button_right(self):
        Input._mouse_current = (False, False, True)
        assert Input.get_mouse_button(2) is True

    def test_mouse_button_invalid_index_returns_false(self):
        assert Input.get_mouse_button(99) is False

    def test_mouse_button_down_true(self):
        Input._mouse_previous = (False, False, False)
        Input._mouse_current  = (True, False, False)
        assert Input.get_mouse_button_down(0) is True

    def test_mouse_button_down_false_when_held(self):
        Input._mouse_previous = (True, False, False)
        Input._mouse_current  = (True, False, False)
        assert Input.get_mouse_button_down(0) is False

    def test_mouse_button_down_false_when_not_pressed(self):
        assert Input.get_mouse_button_down(0) is False

    def test_mouse_button_up_true(self):
        Input._mouse_previous = (True, False, False)
        Input._mouse_current  = (False, False, False)
        assert Input.get_mouse_button_up(0) is True

    def test_mouse_button_up_false_when_still_held(self):
        Input._mouse_previous = (True, False, False)
        Input._mouse_current  = (True, False, False)
        assert Input.get_mouse_button_up(0) is False

    def test_mouse_button_up_false_when_never_pressed(self):
        assert Input.get_mouse_button_up(0) is False

    def test_mouse_button_invalid_up_returns_false(self):
        assert Input.get_mouse_button_up(99) is False


# ── TestAxes ───────────────────────────────────────────────────────────────────
class TestAxes:
    # --- Horizontal ---
    def test_axis_h_zero_by_default(self):
        assert Input.get_axis_horizontal() == pytest.approx(0.0)

    def test_axis_h_left_arrow(self):
        Input._keys_current = _press(K_LEFT)
        assert Input.get_axis_horizontal() == pytest.approx(-1.0)

    def test_axis_h_right_arrow(self):
        Input._keys_current = _press(K_RIGHT)
        assert Input.get_axis_horizontal() == pytest.approx(1.0)

    def test_axis_h_a_key(self):
        Input._keys_current = _press(K_a)
        assert Input.get_axis_horizontal() == pytest.approx(-1.0)

    def test_axis_h_d_key(self):
        Input._keys_current = _press(K_d)
        assert Input.get_axis_horizontal() == pytest.approx(1.0)

    def test_axis_h_both_left_right_cancels(self):
        Input._keys_current = _press(K_LEFT, K_RIGHT)
        assert Input.get_axis_horizontal() == pytest.approx(0.0)

    def test_axis_h_both_ad_cancels(self):
        Input._keys_current = _press(K_a, K_d)
        assert Input.get_axis_horizontal() == pytest.approx(0.0)

    def test_axis_h_arrow_and_wasd_combined(self):
        """LEFT + d = -1 + 1 = 0."""
        Input._keys_current = _press(K_LEFT, K_d)
        assert Input.get_axis_horizontal() == pytest.approx(0.0)

    # --- Vertical ---
    def test_axis_v_zero_by_default(self):
        assert Input.get_axis_vertical() == pytest.approx(0.0)

    def test_axis_v_up_arrow(self):
        Input._keys_current = _press(K_UP)
        assert Input.get_axis_vertical() == pytest.approx(-1.0)

    def test_axis_v_down_arrow(self):
        Input._keys_current = _press(K_DOWN)
        assert Input.get_axis_vertical() == pytest.approx(1.0)

    def test_axis_v_w_key(self):
        Input._keys_current = _press(K_w)
        assert Input.get_axis_vertical() == pytest.approx(-1.0)

    def test_axis_v_s_key(self):
        Input._keys_current = _press(K_s)
        assert Input.get_axis_vertical() == pytest.approx(1.0)

    def test_axis_v_both_up_down_cancels(self):
        Input._keys_current = _press(K_UP, K_DOWN)
        assert Input.get_axis_vertical() == pytest.approx(0.0)

    def test_axis_v_both_ws_cancels(self):
        Input._keys_current = _press(K_w, K_s)
        assert Input.get_axis_vertical() == pytest.approx(0.0)

    def test_axis_v_arrow_and_wasd_combined(self):
        """UP + s = -1 + 1 = 0."""
        Input._keys_current = _press(K_UP, K_s)
        assert Input.get_axis_vertical() == pytest.approx(0.0)


# ── TestUpdate ──────────────────────────────────────────────────────────────────
class TestUpdate:
    def test_update_shifts_keys_current_to_previous(self):
        cur = _press(K_LEFT)
        Input._keys_current = cur
        Input.update()
        assert Input._keys_previous is cur

    def test_update_fetches_new_keys_current(self):
        new_keys = _press(K_RIGHT)
        _pg.key.get_pressed.return_value = new_keys
        Input.update()
        assert Input._keys_current is new_keys
        _pg.key.get_pressed.return_value = _FakeKeys()  # reset

    def test_update_shifts_mouse_current_to_previous(self):
        Input._mouse_current = (True, False, False)
        _pg.mouse.get_pressed.return_value = (False, False, False)
        _pg.mouse.get_pos.return_value     = (0, 0)
        _pg.mouse.get_rel.return_value     = (0, 0)
        Input.update()
        assert Input._mouse_previous == (True, False, False)

    def test_update_fetches_mouse_position(self):
        _pg.mouse.get_pressed.return_value = (False, False, False)
        _pg.mouse.get_pos.return_value     = (100, 200)
        _pg.mouse.get_rel.return_value     = (0, 0)
        Input.update()
        assert Input._mouse_position == (100, 200)
        _pg.mouse.get_pos.return_value = (0, 0)  # reset

    def test_update_fetches_mouse_rel(self):
        _pg.mouse.get_pressed.return_value = (False, False, False)
        _pg.mouse.get_pos.return_value     = (0, 0)
        _pg.mouse.get_rel.return_value     = (3, -7)
        Input.update()
        assert Input._mouse_rel == (3, -7)
        _pg.mouse.get_rel.return_value = (0, 0)  # reset
