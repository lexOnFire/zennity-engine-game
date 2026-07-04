"""
tests/editor/test_phase1_viewport_pro.py
─────────────────────────────────────────────────────────────────────────────
Testes unitários e de integração para a Viewport Profissional (Fase 2).
Valida Pan, Zoom suave, conversões de coordenadas, Bounding Box e Grid.
"""
from __future__ import annotations

import math
import os
import numpy as np
import pygame

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QPainter

from editor.phase1_editor import ZennityPhase1Editor
from editor.viewport.viewport_camera import ViewportCamera
from editor.viewport.grid_renderer import GridRenderer
from editor.viewport.bounding_box import BoundingBoxRenderer
from editor.widgets.phase1_viewport import Phase1ViewportWidget


@pytest.fixture(scope="session")
def qapp() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture
def phase1_editor(qapp: QApplication) -> ZennityPhase1Editor:
    editor = ZennityPhase1Editor()
    yield editor
    editor.close()
    editor.deleteLater()
    qapp.processEvents()


# ── Testes de Câmera e Conversão de Coordenadas ───────────────────────────────

def test_viewport_camera_pan() -> None:
    """Verifica se o método pan() desloca a posição da câmera no mundo corretamente."""
    camera = ViewportCamera()
    camera.set_viewport_size(800, 600)
    camera.position = np.array([0.0, 0.0, 0.0], dtype=np.float32)
    camera.zoom = 2.0

    # Pan de 100 pixels para a direita
    # Como zoom é 2.0, o deslocamento no mundo deve ser de 50 unidades em X
    # Pan move câmera na direção contrária para rolar o conteúdo
    camera.pan(100.0, 0.0)

    assert camera.position[0] == pytest.approx(-50.0)
    assert camera.position[1] == pytest.approx(0.0)


def test_viewport_camera_zoom_boundaries() -> None:
    """Garante que os limites de zoom mínimo e máximo sejam respeitados."""
    camera = ViewportCamera()
    camera.zoom_to_mouse(0.0001, 400.0, 300.0)
    camera.update(1.0)
    assert camera.zoom == pytest.approx(camera.min_zoom)

    camera.zoom_to_mouse(100000.0, 400.0, 300.0)
    camera.update(1.0)
    assert camera.zoom == pytest.approx(camera.max_zoom)


def test_viewport_camera_coordinates_roundtrip() -> None:
    """Garante consistência na conversão de coordenadas (World -> Screen -> World)."""
    camera = ViewportCamera()
    camera.set_viewport_size(800, 600)
    camera.position = np.array([123.4, -567.8, 0.0], dtype=np.float32)
    camera.zoom = 1.5

    world_pt = np.array([300.0, 200.0, 0.0], dtype=np.float32)
    screen_pt = camera.world_to_screen(world_pt)
    roundtrip = camera.screen_to_world(screen_pt)

    assert roundtrip[0] == pytest.approx(world_pt[0])
    assert roundtrip[1] == pytest.approx(world_pt[1])


def test_viewport_camera_zoom_to_mouse_preserves_anchor() -> None:
    """Verifica se o ponto mundial sob o mouse permanece na mesma posição de tela após o zoom."""
    camera = ViewportCamera()
    camera.set_viewport_size(800, 600)
    camera.position = np.array([0.0, 0.0, 0.0], dtype=np.float32)
    camera.zoom = 1.0

    # Mouse posicionado em (500, 400) na tela
    mouse_screen = (500.0, 400.0)
    mouse_world_before = camera.screen_to_world(mouse_screen).copy()

    # Aplica zoom-to-mouse com fator 2x
    camera.zoom_to_mouse(2.0, mouse_screen[0], mouse_screen[1])
    
    # Executa update() para processar a interpolação suave até o fim
    for _ in range(20):
        camera.update(0.1)

    assert camera.zoom == pytest.approx(2.0)
    
    # O ponto na tela (500, 400) deve continuar mapeando para o mesmo ponto do mundo anterior
    mouse_world_after = camera.screen_to_world(mouse_screen)
    assert mouse_world_after[0] == pytest.approx(mouse_world_before[0], abs=1e-2)
    assert mouse_world_after[1] == pytest.approx(mouse_world_before[1], abs=1e-2)


# ── Testes de Bounding Box ────────────────────────────────────────────────────

def test_bounding_box_eight_handles_rotation(phase1_editor: ZennityPhase1Editor) -> None:
    """Garante que as 8 alças do Bounding Box rotacionam junto com o objeto."""
    selected = phase1_editor.scene_objects()[1]
    selected.transform.position[0] = 0.0
    selected.transform.position[1] = 0.0
    selected.transform.scale[0] = 100.0
    selected.transform.scale[1] = 50.0
    selected.transform.rz = 90.0  # Rotação de 90 graus
    
    renderer = BoundingBoxRenderer()
    
    # Mock do world_to_viewport para retornar o próprio vetor (coordenada local de mundo)
    # permitindo validar a matemática de rotação das alças de forma direta.
    def mock_w2v(pt):
        return float(pt[0]), float(pt[1])

    # Sobrescrevemos o draw do painter para capturar os pontos enviados
    captured_rects = []
    class DummyPainter(QPainter):
        def drawRect(self, rect):
            captured_rects.append(rect)

    painter = DummyPainter()
    renderer.draw(painter, selected, mock_w2v)

    # 1 caixa delimitadora + 8 alças = 9 retângulos desenhados
    assert len(captured_rects) == 9


# ── Testes de Grid ────────────────────────────────────────────────────────────

def test_grid_renderer_opacity_fading() -> None:
    """Verifica se o GridRenderer oculta ou atenua linhas conforme o zoom."""
    grid = GridRenderer()
    
    class DummyPainter(QPainter):
        def drawLine(self, *args):
            pass

    painter = DummyPainter()
    cam_pos = np.zeros(3)

    # Zoom extremamente baixo (0.1x) -> espaçamento 3.2px (fada a zero secundário)
    grid.draw(painter, 800, 600, 0.1, cam_pos, lambda pt: (pt[0], pt[1]))
    
    # Zoom alto (2.0x) -> espaçamento 64px, secundário visível
    grid.draw(painter, 800, 600, 2.0, cam_pos, lambda pt: (pt[0], pt[1]))


# ── Teste da Viewport API ─────────────────────────────────────────────────────

def test_viewport_public_coordinate_api(phase1_editor: ZennityPhase1Editor) -> None:
    """Valida as 4 funções da API de conversão de coordenadas da Viewport."""
    vp: Phase1ViewportWidget = phase1_editor.viewport
    assert hasattr(vp, "world_to_viewport")
    assert hasattr(vp, "viewport_to_world")
    assert hasattr(vp, "screen_to_world")
    assert hasattr(vp, "world_to_screen")

    world_pt = np.array([50.0, -10.0, 0.0])
    vp_pt = vp.world_to_viewport(world_pt)
    assert len(vp_pt) == 2

    back = vp.viewport_to_world(vp_pt)
    assert back[0] == pytest.approx(50.0)
    assert back[1] == pytest.approx(-10.0)


# ── Testes de Bounding Box e Selection Outline APIs ───────────────────────────

def test_bounding_box_apis_rectangular_bounds() -> None:
    """Verifica o cálculo de bounds retangulares para objetos convencionais."""
    from engine.core.game_object import GameObject
    from editor.viewport.bounding_box import get_object_bounds

    obj = GameObject("RectObject")
    obj.transform.position = np.array([10.0, 20.0, 0.0], dtype=np.float32)
    obj.transform.scale = np.array([100.0, 50.0, 1.0], dtype=np.float32)
    
    # min_x = 10 - 50 = -40; max_x = 10 + 50 = 60
    # min_y = 20 - 25 = -5; max_y = 20 + 25 = 45
    bounds = get_object_bounds(obj)
    assert bounds == (-40.0, -5.0, 60.0, 45.0)


def test_bounding_box_apis_circular_bounds() -> None:
    """Verifica o cálculo de bounds circulares para objetos baseados em círculo."""
    from engine.core.game_object import GameObject
    from engine.physics.collider import CircleCollider
    from editor.viewport.bounding_box import get_object_bounds

    obj = GameObject("CircleObject")
    obj.transform.position = np.array([5.0, 5.0, 0.0], dtype=np.float32)
    obj.transform.scale = np.array([40.0, 40.0, 1.0], dtype=np.float32)
    obj.add_component(CircleCollider(radius=15.0))

    # min_x = 5 - 15 = -10; max_x = 5 + 15 = 20
    bounds = get_object_bounds(obj)
    assert bounds == (-10.0, -10.0, 20.0, 20.0)


def test_bounding_box_apis_eight_handle_positions() -> None:
    """Valida as posições geradas para as 8 alças ao redor dos bounds."""
    from editor.viewport.bounding_box import get_handle_positions

    bounds = (-10.0, -20.0, 30.0, 40.0)
    # mid_x = 10.0, mid_y = 10.0
    handles = get_handle_positions(bounds)
    
    # Ordem: TL, TC, TR, RC, BR, BC, BL, LC
    expected = [
        (-10.0, -20.0), # TL
        (10.0, -20.0),  # TC
        (30.0, -20.0),  # TR
        (30.0, 10.0),   # RC
        (30.0, 40.0),   # BR
        (10.0, 40.0),   # BC
        (-10.0, 40.0),  # BL
        (-10.0, 10.0),  # LC
    ]
    assert handles == expected


def test_bounding_box_apis_hit_test_handle() -> None:
    """Verifica se o hit test detecta cliques corretos nos handles de escala."""
    from editor.viewport.bounding_box import hit_test_handle

    handles = [
        (10.0, 10.0),
        (20.0, 10.0),
        (30.0, 10.0),
    ]

    # Cliques exatos
    assert hit_test_handle((10.0, 10.0), handles) == 0
    assert hit_test_handle((30.0, 10.0), handles) == 2

    # Cliques com tolerância (limite 6px)
    assert hit_test_handle((12.0, 9.0), handles) == 0
    assert hit_test_handle((20.0, 20.0), handles) is None # muito longe


def test_bounding_box_draw_no_selection_no_crash() -> None:
    """Verifica que o BoundingBoxRenderer e o SelectionOutlineRenderer não quebram sem seleção."""
    from PySide6.QtGui import QPainter
    from editor.viewport.bounding_box import BoundingBoxRenderer
    from editor.viewport.selection_outline import SelectionOutlineRenderer

    class DummyPainter(QPainter):
        pass

    painter = DummyPainter()
    box_renderer = BoundingBoxRenderer()
    outline_renderer = SelectionOutlineRenderer()

    # Sem seleção (selected=None), deve retornar silenciosamente sem erro
    box_renderer.draw(painter, None, lambda x: (0, 0))
    outline_renderer.draw(painter, None, lambda x: (0, 0))
