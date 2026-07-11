"""
tests/editor/test_sprite_renderer.py
─────────────────────────────────────────────────────────────────────────────
Testes unitários para editor/viewport/sprite_renderer.py.

Verifica:
  - draw() não faz nada sem surface ou scene
  - draw() ignora objetos sem ImageComponent (fallback legado)
  - draw() ignora objetos com runtime_hidden=True
  - draw() chama blit quando sprite carrega corretamente
  - borda de seleção desenhada apenas para selected_obj correto
  - label de nome desenhado
  - culling (objeto fora da viewport não recebe blit)
  - alpha e rotação aplicados sem crash
  - _find_image_component por get_component e por type_name
  - cache de superfícies (_evict_cache)
"""
from __future__ import annotations

import os
import sys
import types
from unittest.mock import MagicMock, patch

import numpy as np
import pygame
import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

# ---------------------------------------------------------------------------
# Helpers de stubs
# ---------------------------------------------------------------------------

def _make_transform(x=400.0, y=300.0, sx=64.0, sy=64.0, rz=0.0):
    t = MagicMock()
    t.position = np.array([x, y, 0.0], dtype=np.float32)
    t.scale = np.array([sx, sy, 1.0], dtype=np.float32)
    t.rz = rz
    return t


def _make_image_component(sprite_path="player.png", alpha=255):
    comp = MagicMock()
    comp.sprite_path = sprite_path
    comp.alpha = alpha
    comp.component_type = "Image"
    comp.type_name = "Image"
    return comp


def _make_object(
    name="Player",
    image_comp=None,
    runtime_hidden=False,
    x=400.0,
    y=300.0,
    sx=64.0,
    sy=64.0,
    rz=0.0,
):
    obj = MagicMock()
    obj.name = name
    obj.runtime_hidden = runtime_hidden
    obj.transform = _make_transform(x, y, sx, sy, rz)
    obj.components = [image_comp] if image_comp else []
    if image_comp is not None:
        obj.get_component = MagicMock(side_effect=lambda cls: image_comp)
    else:
        obj.get_component = MagicMock(return_value=None)
    return obj


def _make_scene(objects, vp_w=800, vp_h=600):
    scene = MagicMock()
    scene.editable_objects = objects
    scene.font_sm = pygame.font.SysFont("Arial", 11)

    def world_to_vp(pos, lay):
        # Simples: retorna posição 2D diretamente
        return float(pos[0]), float(pos[1])

    scene._world_to_vp = world_to_vp
    scene._layout = MagicMock(return_value={
        "vp_left": 0,
        "vp_right": vp_w,
        "vp_top": 0,
        "vp_bottom": vp_h,
    })
    return scene


def _make_layout(vp_w=800, vp_h=600):
    return {
        "vp_left": 0,
        "vp_right": vp_w,
        "vp_top": 0,
        "vp_bottom": vp_h,
    }


def _fake_surface(w=64, h=64):
    """Cria um pygame.Surface real de tamanho w x h."""
    return pygame.Surface((w, h), pygame.SRCALPHA)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True, scope="module")
def pygame_init():
    pygame.init()
    yield
    pygame.quit()


@pytest.fixture(autouse=True)
def clear_cache():
    """Limpa o cache de superfícies entre testes."""
    from editor.viewport.sprite_renderer import _SURFACE_CACHE
    _SURFACE_CACHE.clear()
    yield
    _SURFACE_CACHE.clear()


# ---------------------------------------------------------------------------
# Importação do módulo sob teste
# ---------------------------------------------------------------------------

from editor.viewport.sprite_renderer import (
    SpriteRenderer,
    _find_image_component,
    _load_surface,
    _evict_cache,
    _SURFACE_CACHE,
    _CACHE_MAX,
)

# ---------------------------------------------------------------------------
# Testes: _find_image_component
# ---------------------------------------------------------------------------

class TestFindImageComponent:
    def test_returns_none_when_no_components(self):
        obj = _make_object()
        assert _find_image_component(obj) is None

    def test_finds_via_get_component(self):
        img = _make_image_component()
        obj = _make_object(image_comp=img)
        # Garante que o get_component retorna o componente
        result = _find_image_component(obj)
        assert result is img

    def test_finds_via_type_name_fallback(self):
        """Sem ImageComponent importável, deve encontrar via type_name='Image'."""
        img = MagicMock()
        img.type_name = "Image"
        img.sprite_path = "hero.png"

        obj = MagicMock()
        obj.components = [img]
        # Simula falha no get_component (engine não disponível)
        obj.get_component = MagicMock(side_effect=Exception("no engine"))

        # Bloqueia o import de engine.ui.runtime_components dentro de _find_image_component
        import sys
        original = sys.modules.get("engine.ui.runtime_components")
        sys.modules["engine.ui.runtime_components"] = None  # type: ignore
        try:
            result = _find_image_component(obj)
        finally:
            if original is None:
                sys.modules.pop("engine.ui.runtime_components", None)
            else:
                sys.modules["engine.ui.runtime_components"] = original

        assert result is img

    def test_ignores_component_with_empty_sprite_path(self):
        img = _make_image_component(sprite_path="")
        obj = _make_object(image_comp=img)
        obj.get_component = MagicMock(return_value=None)  # força fallback por type_name
        img.type_name = "Image"
        result = _find_image_component(obj)
        assert result is None


# ---------------------------------------------------------------------------
# Testes: SpriteRenderer.draw — casos gerais
# ---------------------------------------------------------------------------

class TestSpriteRendererDraw:
    def setup_method(self):
        self.renderer = SpriteRenderer()
        self.surface = pygame.Surface((800, 600), pygame.SRCALPHA)
        self.layout = _make_layout()

    def test_draw_none_surface_no_crash(self):
        scene = _make_scene([])
        self.renderer.draw(None, scene, None, self.layout, 1.0)  # sem crash

    def test_draw_none_scene_no_crash(self):
        self.renderer.draw(self.surface, None, None, self.layout, 1.0)  # sem crash

    def test_draw_empty_scene_no_crash(self):
        scene = _make_scene([])
        self.renderer.draw(self.surface, scene, None, self.layout, 1.0)

    def test_skips_object_without_image_component(self):
        obj = _make_object()  # sem ImageComponent
        scene = _make_scene([obj])
        # Surface deve permanecer intacta (sem blit de sprite)
        before = pygame.image.tostring(self.surface, "RGBA")
        with patch("editor.viewport.sprite_renderer._load_surface", return_value=None):
            self.renderer.draw(self.surface, scene, None, self.layout, 1.0)
        after = pygame.image.tostring(self.surface, "RGBA")
        assert before == after

    def test_skips_runtime_hidden_object(self):
        img = _make_image_component()
        obj = _make_object(image_comp=img, runtime_hidden=True)
        scene = _make_scene([obj])
        before = pygame.image.tostring(self.surface, "RGBA")
        fake_surf = _fake_surface()
        with patch("editor.viewport.sprite_renderer._load_surface", return_value=fake_surf):
            self.renderer.draw(self.surface, scene, None, self.layout, 1.0)
        after = pygame.image.tostring(self.surface, "RGBA")
        assert before == after  # hidden: nada desenhado

    def test_skips_object_when_surface_not_loaded(self):
        img = _make_image_component(sprite_path="missing.png")
        obj = _make_object(image_comp=img)
        scene = _make_scene([obj])
        before = pygame.image.tostring(self.surface, "RGBA")
        with patch("editor.viewport.sprite_renderer._load_surface", return_value=None):
            self.renderer.draw(self.surface, scene, None, self.layout, 1.0)
        after = pygame.image.tostring(self.surface, "RGBA")
        assert before == after  # sem blit

    def test_draws_sprite_when_surface_loaded(self):
        img = _make_image_component()
        obj = _make_object(image_comp=img, x=400.0, y=300.0)
        scene = _make_scene([obj])
        before = pygame.image.tostring(self.surface, "RGBA")
        fake_surf = _fake_surface(64, 64)
        fake_surf.fill((255, 0, 0, 255))  # vermelho — distinguível
        with patch("editor.viewport.sprite_renderer._load_surface", return_value=fake_surf):
            self.renderer.draw(self.surface, scene, None, self.layout, 1.0)
        after = pygame.image.tostring(self.surface, "RGBA")
        assert before != after  # algo foi desenhado

    def test_draws_selection_border_for_selected_obj(self):
        img = _make_image_component()
        obj = _make_object(image_comp=img, x=400.0, y=300.0, sx=100.0, sy=100.0)
        scene = _make_scene([obj])
        fake_surf = _fake_surface(100, 100)

        with patch("editor.viewport.sprite_renderer._load_surface", return_value=fake_surf), \
             patch("pygame.draw.rect") as mock_rect:
            self.renderer.draw(self.surface, scene, obj, self.layout, 1.0)
            assert mock_rect.called, "Borda de seleção deve ser desenhada para o selected_obj"

    def test_no_selection_border_for_other_obj(self):
        img = _make_image_component()
        obj = _make_object(image_comp=img, x=400.0, y=300.0)
        other = _make_object(name="Other")
        scene = _make_scene([obj])
        fake_surf = _fake_surface()

        with patch("editor.viewport.sprite_renderer._load_surface", return_value=fake_surf), \
             patch("pygame.draw.rect") as mock_rect:
            self.renderer.draw(self.surface, scene, other, self.layout, 1.0)
            assert not mock_rect.called, "Borda não deve ser desenhada para outro objeto"

    def test_no_selection_border_when_selected_is_none(self):
        img = _make_image_component()
        obj = _make_object(image_comp=img, x=400.0, y=300.0)
        scene = _make_scene([obj])
        fake_surf = _fake_surface()

        with patch("editor.viewport.sprite_renderer._load_surface", return_value=fake_surf), \
             patch("pygame.draw.rect") as mock_rect:
            self.renderer.draw(self.surface, scene, None, self.layout, 1.0)
            assert not mock_rect.called


# ---------------------------------------------------------------------------
# Testes: culling
# ---------------------------------------------------------------------------

class TestSpriteRendererCulling:
    def setup_method(self):
        self.renderer = SpriteRenderer()
        self.surface = pygame.Surface((800, 600), pygame.SRCALPHA)
        self.layout = _make_layout(800, 600)

    def test_object_outside_right_is_culled(self):
        img = _make_image_component()
        obj = _make_object(image_comp=img, x=1000.0, y=300.0, sx=32.0, sy=32.0)
        scene = _make_scene([obj])
        before = pygame.image.tostring(self.surface, "RGBA")
        fake_surf = _fake_surface(32, 32)
        fake_surf.fill((0, 255, 0, 255))
        with patch("editor.viewport.sprite_renderer._load_surface", return_value=fake_surf):
            self.renderer.draw(self.surface, scene, None, self.layout, 1.0)
        after = pygame.image.tostring(self.surface, "RGBA")
        assert before == after

    def test_object_inside_viewport_is_drawn(self):
        img = _make_image_component()
        obj = _make_object(image_comp=img, x=400.0, y=300.0, sx=32.0, sy=32.0)
        scene = _make_scene([obj])
        before = pygame.image.tostring(self.surface, "RGBA")
        fake_surf = _fake_surface(32, 32)
        fake_surf.fill((0, 0, 255, 255))
        with patch("editor.viewport.sprite_renderer._load_surface", return_value=fake_surf):
            self.renderer.draw(self.surface, scene, None, self.layout, 1.0)
        after = pygame.image.tostring(self.surface, "RGBA")
        assert before != after


# ---------------------------------------------------------------------------
# Testes: alpha e rotação
# ---------------------------------------------------------------------------

class TestSpriteRendererAlphaRotation:
    def setup_method(self):
        self.renderer = SpriteRenderer()
        self.surface = pygame.Surface((800, 600), pygame.SRCALPHA)
        self.layout = _make_layout()

    def test_alpha_applied_without_crash(self):
        img = _make_image_component(alpha=128)
        obj = _make_object(image_comp=img, x=400.0, y=300.0)
        scene = _make_scene([obj])
        fake_surf = _fake_surface()
        with patch("editor.viewport.sprite_renderer._load_surface", return_value=fake_surf):
            self.renderer.draw(self.surface, scene, None, self.layout, 1.0)

    def test_rotation_applied_without_crash(self):
        img = _make_image_component()
        obj = _make_object(image_comp=img, x=400.0, y=300.0, rz=45.0)
        scene = _make_scene([obj])
        fake_surf = _fake_surface()
        with patch("editor.viewport.sprite_renderer._load_surface", return_value=fake_surf):
            self.renderer.draw(self.surface, scene, None, self.layout, 1.0)

    def test_zero_rotation_skips_transform_rotate(self):
        img = _make_image_component()
        obj = _make_object(image_comp=img, rz=0.0)
        scene = _make_scene([obj])
        fake_surf = _fake_surface()
        with patch("editor.viewport.sprite_renderer._load_surface", return_value=fake_surf), \
             patch("pygame.transform.rotate") as mock_rot:
            self.renderer.draw(self.surface, scene, None, self.layout, 1.0)
            assert not mock_rot.called, "rotate nao deve ser chamado para rz=0"


# ---------------------------------------------------------------------------
# Testes: cache de superfícies
# ---------------------------------------------------------------------------

class TestSurfaceCache:
    def test_evict_cache_halves_entries(self):
        from editor.viewport import sprite_renderer as sr
        sr._SURFACE_CACHE.clear()
        for i in range(10):
            sr._SURFACE_CACHE[(str(i), 64, 64, 0.0)] = _fake_surface()
        _evict_cache()
        assert len(sr._SURFACE_CACHE) <= 5

    def test_same_params_reuses_cached_surface(self):
        img = _make_image_component(sprite_path="hero.png")
        obj = _make_object(image_comp=img, x=400.0, y=300.0, sx=64.0, sy=64.0)
        scene = _make_scene([obj])
        layout = _make_layout()
        surface = pygame.Surface((800, 600), pygame.SRCALPHA)
        renderer = SpriteRenderer()

        base_surf = _fake_surface(64, 64)

        with patch("editor.viewport.sprite_renderer._load_surface", return_value=base_surf), \
             patch("pygame.transform.scale", wraps=pygame.transform.scale) as mock_scale:
            renderer.draw(surface, scene, None, layout, 1.0)
            calls_first = mock_scale.call_count
            renderer.draw(surface, scene, None, layout, 1.0)
            calls_second = mock_scale.call_count

        # Na segunda passagem, scale não deve ser chamado novamente (cache hit)
        assert calls_second == calls_first
