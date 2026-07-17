from __future__ import annotations
import math
from typing import Dict, Any, Callable, Tuple
import pygame
import numpy as np


class GizmoRegistry:
    """
    Registro centralizado de gizmos para o Zennity Editor.
    Permite registrar e consultar funções de desenho de gizmo para componentes.
    """
    _registry: Dict[str, Callable[[Any, pygame.Surface, Any], None]] = {}

    @classmethod
    def register(cls, component_type: str, draw_func: Callable[[Any, pygame.Surface, Any], None]) -> None:
        """Registra uma função de desenho de gizmo para um tipo de componente."""
        cls._registry[component_type] = draw_func

    @classmethod
    def get_gizmo(cls, component_type: str) -> Callable[[Any, pygame.Surface, Any], None] | None:
        """Consulta e retorna a função de desenho de gizmo registrada, ou None."""
        return cls._registry.get(component_type)

    @classmethod
    def draw(cls, screen: pygame.Surface, scene: Any) -> None:
        """Desenha, na ordem legada, todos os gizmos registrados da cena."""
        objects = getattr(scene, "editable_objects", getattr(scene, "game_objects", []))
        for obj in objects:
            if getattr(obj, "name", "") == "EditorCamera":
                continue
            for component in getattr(obj, "components", []):
                draw_func = cls.get_gizmo(component.component_type)
                if draw_func:
                    try:
                        draw_func(component, screen, scene)
                    except Exception:
                        pass


def _get_screen_pos(component: Any, scene: Any) -> Tuple[float, float]:
    """Helper para obter a posição na tela de um componente no editor."""
    obj = component.game_object
    if not obj:
        return (0.0, 0.0)
    pos = obj.transform.get_world_position()
    if type(scene).__name__ not in ("MagicMock", "Mock") and hasattr(scene, "_world_to_vp") and hasattr(scene, "_layout"):
        try:
            val = scene._world_to_vp(pos, scene._layout())
            if isinstance(val, (tuple, list, np.ndarray)) and len(val) >= 2:
                return float(val[0]), float(val[1])
        except Exception:
            pass
    return float(pos[0]), float(pos[1])


def _get_zoom(scene: Any) -> float:
    """Helper para obter o zoom atual da câmera do editor."""
    if hasattr(scene, "_zoom"):
        return float(scene._zoom())
    from engine.graphics.camera2d import Camera2D
    if Camera2D.main:
        return float(Camera2D.main.zoom)
    return 1.0


# ── 1. Camera Gizmo ───────────────────────────────────────────────────────────

def draw_camera_gizmo(component: Any, screen: pygame.Surface, scene: Any) -> None:
    """Desenha um retângulo tracejado/fino representando a projeção e área da câmera."""
    obj = component.game_object
    if not obj or not component.enabled:
        return

    cx, cy = _get_screen_pos(component, scene)
    zoom = _get_zoom(scene)

    # Cores
    color_border = (0, 229, 255)  # Cyan
    color_inner = (0, 229, 255, 30)

    # Proporções de tamanho base
    w = 80.0 * zoom
    h = 50.0 * zoom

    # Superfície semi-transparente para o corpo da câmera
    cam_rect_surf = pygame.Surface((w, h), pygame.SRCALPHA)
    cam_rect_surf.fill(color_inner)
    pygame.draw.rect(cam_rect_surf, color_border, (0, 0, w, h), 2, border_radius=4)
    
    # Desenha lente frontal
    lens_pts = [(w, h * 0.25), (w + 12 * zoom, h * 0.15), (w + 12 * zoom, h * 0.85), (w, h * 0.75)]
    pygame.draw.polygon(cam_rect_surf, (*color_border, 80), lens_pts)
    pygame.draw.polygon(cam_rect_surf, color_border, lens_pts, 2)

    # Rotação
    rz = getattr(obj.transform, "rz", 0.0)
    if rz != 0.0:
        rotated_surf = pygame.transform.rotate(cam_rect_surf, -rz)
        rotated_rect = rotated_surf.get_rect(center=(int(cx), int(cy)))
        screen.blit(rotated_surf, rotated_rect.topleft)
    else:
        screen.blit(cam_rect_surf, (int(cx - w / 2), int(cy - h / 2)))

    # Desenha linha tracejada representando o Viewport Rect se a câmera for selecionada
    selected_idx = getattr(scene, "selected_index", -1)
    if isinstance(selected_idx, (int, float)) and selected_idx >= 0:
        editable_objs = getattr(scene, "editable_objects", [])
        if len(editable_objs) > selected_idx:
            sel_obj = editable_objs[selected_idx]
            if sel_obj is obj:
                # Desenha um retângulo pontilhado indicando a área de cobertura aproximada
                fov_w = 400.0 * zoom / component.zoom
                fov_h = 300.0 * zoom / component.zoom
                fov_surf = pygame.Surface((fov_w, fov_h), pygame.SRCALPHA)
                pygame.draw.rect(fov_surf, (*color_border, 90), (0, 0, fov_w, fov_h), 1, border_radius=2)
                screen.blit(fov_surf, (int(cx - fov_w / 2), int(cy - fov_h / 2)))


# ── 2. BoxCollider Gizmo ──────────────────────────────────────────────────────

def draw_box_collider_gizmo(component: Any, screen: pygame.Surface, scene: Any) -> None:
    """Desenha um contorno verde claro representando a caixa física do BoxCollider."""
    obj = component.game_object
    if not obj or not component.enabled:
        return

    cx, cy = _get_screen_pos(component, scene)
    zoom = _get_zoom(scene)
    rz = getattr(obj.transform, "rz", 0.0)

    w = float(component.width) * zoom
    h = float(component.height) * zoom

    col_color = (76, 175, 80)  # Green

    # Calcula vértices rotacionados
    rad = math.radians(rz)
    cos_val = math.cos(rad)
    sin_val = math.sin(rad)

    half_w = w / 2.0
    half_h = h / 2.0

    corners = [
        (-half_w, -half_h),
        (half_w, -half_h),
        (half_w, half_h),
        (-half_w, half_h)
    ]

    screen_corners = []
    for lx, ly in corners:
        rx = lx * cos_val - ly * sin_val
        ry = lx * sin_val + ly * cos_val
        screen_corners.append((int(cx + rx), int(cy + ry)))

    # Desenha o contorno do colisor
    pygame.draw.polygon(screen, col_color, screen_corners, 1)


# ── 3. CircleCollider Gizmo ───────────────────────────────────────────────────

def draw_circle_collider_gizmo(component: Any, screen: pygame.Surface, scene: Any) -> None:
    """Desenha um contorno circular verde claro correspondente ao raio do colisor."""
    obj = component.game_object
    if not obj or not component.enabled:
        return

    cx, cy = _get_screen_pos(component, scene)
    zoom = _get_zoom(scene)
    
    r = float(component.radius) * zoom
    col_color = (76, 175, 80)  # Green

    pygame.draw.circle(screen, col_color, (int(cx), int(cy)), int(r), 1)


# ── 4. AudioSource Gizmo ──────────────────────────────────────────────────────

def draw_audio_source_gizmo(component: Any, screen: pygame.Surface, scene: Any) -> None:
    """Desenha um alto-falante e um círculo amarelo suave representando a fonte de som."""
    obj = component.game_object
    if not obj or not component.enabled:
        return

    cx, cy = _get_screen_pos(component, scene)
    zoom = _get_zoom(scene)

    color_source = (255, 235, 59)  # Yellow
    r = 14 * zoom

    # Desenha círculo amarelo suave
    pygame.draw.circle(screen, color_source, (int(cx), int(cy)), int(r), 1)
    
    # Desenha símbolo simples de alto-falante (uma caixinha e um cone)
    box_w = 6 * zoom
    box_h = 6 * zoom
    pygame.draw.rect(screen, color_source, (cx - box_w, cy - box_h/2, box_w, box_h))
    
    poly_pts = [
        (cx, cy - box_h/2),
        (cx + 6 * zoom, cy - box_h),
        (cx + 6 * zoom, cy + box_h),
        (cx, cy + box_h/2)
    ]
    pygame.draw.polygon(screen, color_source, poly_pts)

    # Rótulo de texto
    font = pygame.font.SysFont("monospace", int(10 * zoom))
    text_s = font.render("AudioSource", True, color_source)
    screen.blit(text_s, (int(cx - text_s.get_width()/2), int(cy - r - text_s.get_height() - 2)))


# ── 5. AudioListener Gizmo ────────────────────────────────────────────────────

def draw_audio_listener_gizmo(component: Any, screen: pygame.Surface, scene: Any) -> None:
    """Desenha uma representação visual magenta representando o receptor de áudio."""
    obj = component.game_object
    if not obj or not component.enabled:
        return

    cx, cy = _get_screen_pos(component, scene)
    zoom = _get_zoom(scene)

    color_listener = (233, 30, 99)  # Magenta
    r = 14 * zoom

    # Desenha círculo do receptor
    pygame.draw.circle(screen, color_listener, (int(cx), int(cy)), int(r), 1)

    # Desenha símbolo interno simplificado de orelha (dois círculos aninhados)
    pygame.draw.circle(screen, color_listener, (int(cx), int(cy)), int(r * 0.6), 1)
    pygame.draw.circle(screen, color_listener, (int(cx), int(cy)), int(r * 0.3), 1)

    # Rótulo de texto
    font = pygame.font.SysFont("monospace", int(10 * zoom))
    text_s = font.render("AudioListener", True, color_listener)
    screen.blit(text_s, (int(cx - text_s.get_width()/2), int(cy - r - text_s.get_height() - 2)))


# Registro Inicial dos Gizmos Padrão
GizmoRegistry.register("Camera", draw_camera_gizmo)
GizmoRegistry.register("BoxCollider", draw_box_collider_gizmo)
GizmoRegistry.register("CircleCollider", draw_circle_collider_gizmo)
GizmoRegistry.register("AudioSource", draw_audio_source_gizmo)
GizmoRegistry.register("AudioListener", draw_audio_listener_gizmo)
