import pytest
from unittest.mock import MagicMock
import pygame
import numpy as np

from engine.core import GameObject, Component, Transform
from engine.graphics.camera import Camera
from engine.physics.collider import BoxCollider, CircleCollider
from engine.audio import AudioSource, AudioListener
from editor.gizmos.gizmo_registry import GizmoRegistry, _get_screen_pos, _get_zoom
from editor.widgets.viewport_widget import ViewportWidget





def test_gizmo_registry_and_resolution():
    """Valida o registro e a consulta de gizmos por tipo de componente."""
    dummy_func = MagicMock()
    GizmoRegistry.register("DummyComponent", dummy_func)
    
    resolved = GizmoRegistry.get_gizmo("DummyComponent")
    assert resolved is dummy_func
    
    # Gizmo inexistente retorna None e não quebra
    assert GizmoRegistry.get_gizmo("NonExistent") is None


def test_camera_gizmo_rendering():
    """Garante que o gizmo de Câmera renderiza na superfície sem crashar ou modificar o componente."""
    go = GameObject("CamGO")
    cam = go.add_component(Camera(zoom=2.0))
    go.transform.position = np.array([10.0, 20.0, 0.0], dtype=np.float32)

    surface = pygame.Surface((200, 200), pygame.SRCALPHA)
    scene_mock = MagicMock()
    scene_mock._zoom.return_value = 1.0
    scene_mock._layout.return_value = {"vp_left": 0, "vp_top": 0, "vp_w": 200, "vp_h": 200}
    scene_mock._world_to_vp.return_value = (100.0, 100.0)

    draw_func = GizmoRegistry.get_gizmo("Camera")
    assert draw_func is not None

    # Executa o gizmo
    draw_func(cam, surface, scene_mock)

    # Verifica que valores não foram modificados
    assert cam.zoom == 2.0
    assert go.transform.position[0] == 10.0


def test_box_collider_gizmo_rendering():
    """Garante que o gizmo do BoxCollider desenha corretamente respeitando rotação do Transform."""
    go = GameObject("BoxGO")
    col = go.add_component(BoxCollider(width=40, height=20))
    go.transform.position = np.array([50.0, 50.0, 0.0], dtype=np.float32)
    go.transform.rz = 45.0

    surface = pygame.Surface((200, 200), pygame.SRCALPHA)
    scene_mock = MagicMock()
    scene_mock._zoom.return_value = 1.0
    scene_mock._layout.return_value = {"vp_left": 0, "vp_top": 0, "vp_w": 200, "vp_h": 200}
    scene_mock._world_to_vp.return_value = (50.0, 50.0)

    draw_func = GizmoRegistry.get_gizmo("BoxCollider")
    assert draw_func is not None

    draw_func(col, surface, scene_mock)
    
    assert col.width == 40
    assert col.height == 20
    assert go.transform.rz == 45.0


def test_circle_collider_gizmo_rendering():
    """Garante que o gizmo do CircleCollider desenha corretamente."""
    go = GameObject("CircleGO")
    col = go.add_component(CircleCollider(radius=15))

    surface = pygame.Surface((200, 200), pygame.SRCALPHA)
    scene_mock = MagicMock()
    scene_mock._zoom.return_value = 1.2
    scene_mock._layout.return_value = {"vp_left": 0, "vp_top": 0, "vp_w": 200, "vp_h": 200}
    scene_mock._world_to_vp.return_value = (10.0, 20.0)

    draw_func = GizmoRegistry.get_gizmo("CircleCollider")
    assert draw_func is not None

    draw_func(col, surface, scene_mock)
    assert col.radius == 15


def test_audio_gizmos_rendering():
    """Garante que os gizmos do AudioSource e AudioListener desenham sem erros."""
    go = GameObject("AudioGO")
    source = go.add_component(AudioSource(audio_clip="ambient.wav"))
    listener = go.add_component(AudioListener())

    surface = pygame.Surface((200, 200), pygame.SRCALPHA)
    scene_mock = MagicMock()
    scene_mock._zoom.return_value = 1.0
    scene_mock._layout.return_value = {"vp_left": 0, "vp_top": 0, "vp_w": 200, "vp_h": 200}
    scene_mock._world_to_vp.return_value = (100.0, 100.0)

    draw_source = GizmoRegistry.get_gizmo("AudioSource")
    draw_listener = GizmoRegistry.get_gizmo("AudioListener")

    assert draw_source is not None
    assert draw_listener is not None

    draw_source(source, surface, scene_mock)
    draw_listener(listener, surface, scene_mock)

    assert source.audio_clip == "ambient.wav"
    assert listener.enabled is True
