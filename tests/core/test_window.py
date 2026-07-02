"""
tests/core/test_window.py
────────────────────────────────────────────────────────────────
Commit 10: valida o contrato público de Window.
Todos os testes mockam pygame.display para rodar headless.
"""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch, PropertyMock
import pygame


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_surface(w: int, h: int) -> MagicMock:
    """Surface fake que responde a get_width/height/size."""
    surf = MagicMock(spec=pygame.Surface)
    surf.get_width.return_value  = w
    surf.get_height.return_value = h
    surf.get_size.return_value   = (w, h)
    return surf


def _make_display_info(w: int = 1920, h: int = 1080) -> MagicMock:
    info = MagicMock()
    info.current_w = w
    info.current_h = h
    return info


# ---------------------------------------------------------------------------
# Fixture base: cria Window com display totalmente mockado
# ---------------------------------------------------------------------------

@pytest.fixture
def make_window():
    """
    Retorna uma factory que constrói Window com pygame.display mockado.
    Uso: win = make_window(800, 600)
    """
    def _factory(width=800, height=600, title="Test", resizable=True):
        surf = _make_surface(width, height)
        with patch("engine.window.pygame.display.Info",      return_value=_make_display_info()), \
             patch("engine.window.pygame.display.set_mode",  return_value=surf), \
             patch("engine.window.pygame.display.set_caption"):
            from engine.window import Window
            win = Window(width=width, height=height, title=title, resizable=resizable)
        return win, surf
    return _factory


# ===========================================================================
# 1. Defaults
# ===========================================================================

class TestDefaults:
    def test_width(self, make_window):
        win, _ = make_window(800, 600)
        assert win.width == 800

    def test_height(self, make_window):
        win, _ = make_window(800, 600)
        assert win.height == 600

    def test_size(self, make_window):
        win, _ = make_window(800, 600)
        assert win.size == (800, 600)

    def test_title_stored(self, make_window):
        win, _ = make_window(title="Meu Jogo")
        assert win._title == "Meu Jogo"

    def test_not_fullscreen_by_default(self, make_window):
        win, _ = make_window()
        assert win.is_fullscreen is False

    def test_screen_is_surface(self, make_window):
        win, surf = make_window()
        assert win.screen is surf

    def test_resizable_stored(self, make_window):
        win, _ = make_window(resizable=False)
        assert win._resizable is False


# ===========================================================================
# 2. set_title
# ===========================================================================

class TestSetTitle:
    def test_set_title_updates_internal(self, make_window):
        win, _ = make_window(title="Inicial")
        with patch("engine.window.pygame.display.set_caption") as mock_cap:
            win.set_title("Novo Título")
        assert win._title == "Novo Título"

    def test_set_title_calls_set_caption(self, make_window):
        win, _ = make_window()
        with patch("engine.window.pygame.display.set_caption") as mock_cap:
            win.set_title("Zennity")
            mock_cap.assert_called_once_with("Zennity")


# ===========================================================================
# 3. on_resize
# ===========================================================================

class TestOnResize:
    def test_on_resize_updates_screen(self, make_window):
        win, _ = make_window(800, 600, resizable=True)
        new_surf = _make_surface(1024, 768)
        with patch("engine.window.pygame.display.set_mode", return_value=new_surf) as mock_mode:
            win.on_resize(1024, 768)
        assert win.screen is new_surf

    def test_on_resize_updates_dimensions(self, make_window):
        win, _ = make_window(800, 600)
        new_surf = _make_surface(1024, 768)
        with patch("engine.window.pygame.display.set_mode", return_value=new_surf):
            win.on_resize(1024, 768)
        assert win.width  == 1024
        assert win.height == 768

    def test_on_resize_ignored_in_fullscreen(self, make_window):
        win, original_surf = make_window(800, 600)
        win._fullscreen = True  # simula fullscreen ativo
        with patch("engine.window.pygame.display.set_mode") as mock_mode:
            win.on_resize(1920, 1080)
            mock_mode.assert_not_called()
        assert win.screen is original_surf  # não mudou


# ===========================================================================
# 4. toggle_fullscreen
# ===========================================================================

class TestToggleFullscreen:
    def test_toggle_enters_fullscreen(self, make_window):
        win, _ = make_window(800, 600)
        fs_surf = _make_surface(1920, 1080)
        with patch("engine.window.pygame.display.Info",     return_value=_make_display_info(1920, 1080)), \
             patch("engine.window.pygame.display.set_mode", return_value=fs_surf):
            win.toggle_fullscreen()
        assert win.is_fullscreen is True

    def test_toggle_saves_dimensions_before_fullscreen(self, make_window):
        win, _ = make_window(800, 600)
        fs_surf = _make_surface(1920, 1080)
        with patch("engine.window.pygame.display.Info",     return_value=_make_display_info(1920, 1080)), \
             patch("engine.window.pygame.display.set_mode", return_value=fs_surf):
            win.toggle_fullscreen()
        assert win._saved_w == 800
        assert win._saved_h == 600

    def test_toggle_exits_fullscreen(self, make_window):
        win, _ = make_window(800, 600)
        fs_surf   = _make_surface(1920, 1080)
        back_surf = _make_surface(800, 600)

        # entra no fullscreen
        with patch("engine.window.pygame.display.Info",     return_value=_make_display_info()), \
             patch("engine.window.pygame.display.set_mode", return_value=fs_surf):
            win.toggle_fullscreen()

        # sai do fullscreen
        with patch("engine.window.pygame.display.set_mode", return_value=back_surf):
            win.toggle_fullscreen()

        assert win.is_fullscreen is False

    def test_toggle_restores_dimensions(self, make_window):
        win, _ = make_window(800, 600)
        fs_surf   = _make_surface(1920, 1080)
        back_surf = _make_surface(800, 600)

        with patch("engine.window.pygame.display.Info",     return_value=_make_display_info()), \
             patch("engine.window.pygame.display.set_mode", return_value=fs_surf):
            win.toggle_fullscreen()

        with patch("engine.window.pygame.display.set_mode", return_value=back_surf):
            win.toggle_fullscreen()

        assert win.width  == 800
        assert win.height == 600


# ===========================================================================
# 5. flip
# ===========================================================================

class TestFlip:
    def test_flip_calls_display_flip(self, make_window):
        win, _ = make_window()
        with patch("engine.window.pygame.display.flip") as mock_flip:
            win.flip()
            mock_flip.assert_called_once()


# ===========================================================================
# 6. Clamping de resolução (janela maior que desktop é reduzida)
# ===========================================================================

class TestResolutionClamping:
    def test_oversized_window_is_clamped(self):
        """Se w/h >= desktop, a janela é reduzida para 90%x85% do desktop."""
        surf = _make_surface(int(1920 * 0.9), int(1080 * 0.85))
        with patch("engine.window.pygame.display.Info",      return_value=_make_display_info(1920, 1080)), \
             patch("engine.window.pygame.display.set_mode",  return_value=surf) as mock_mode, \
             patch("engine.window.pygame.display.set_caption"):
            from engine.window import Window
            win = Window(width=1920, height=1080)  # igual ao desktop -> clampado
        called_w, called_h = mock_mode.call_args[0][0]
        assert called_w == int(1920 * 0.9)
        assert called_h == int(1080 * 0.85)
