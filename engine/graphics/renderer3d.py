import pygame
import numpy as np
from typing import Tuple, List, Optional
from ..component import Component
from ..assets import Mesh
from .math3d import (
    translation_matrix, rotation_matrix, scale_matrix,
    projection_matrix, view_matrix, project_vertices
)


class Camera3D(Component):
    """3D Camera component. Computes View and Projection matrices."""
    main: 'Camera3D' = None

    def __init__(self, fov: float = 60.0, near: float = 0.1, far: float = 100.0,
                 viewport_x: float = 0.0, viewport_y: float = 0.0,
                 viewport_width: Optional[float] = None,
                 viewport_height: Optional[float] = None) -> None:
        super().__init__()
        self.fov = fov
        self.near = near
        self.far = far
        self.viewport_x = viewport_x
        self.viewport_y = viewport_y
        self.viewport_width  = viewport_width
        self.viewport_height = viewport_height

        self.view_matrix       = np.eye(4, dtype=np.float32)
        self.projection_matrix = np.eye(4, dtype=np.float32)

        if Camera3D.main is None:
            Camera3D.main = self

    def start(self) -> None:
        # FIX: always claim main on start so new cameras after scene reload work
        Camera3D.main = self

    def destroy(self) -> None:
        # FIX: release main reference when this camera is destroyed
        if Camera3D.main is self:
            Camera3D.main = None

    def update(self, dt: float) -> None:
        if self.game_object:
            pos = self.transform.position
            rot = self.transform.rotation
            self.view_matrix = view_matrix(pos, rot)

            screen = pygame.display.get_surface()
            if screen:
                width, height = screen.get_size()
                v_w = self.viewport_width  if self.viewport_width  is not None else width
                v_h = self.viewport_height if self.viewport_height is not None else height
                aspect = v_w / max(1.0, v_h)
                self.projection_matrix = projection_matrix(self.fov, aspect, self.near, self.far)


class MeshRenderer3D(Component):
    """Projects and renders a 3D Mesh using a Camera3D."""
    def __init__(self, mesh: Mesh, color: Tuple[int, int, int] = (200, 200, 200),
                 wireframe: bool = False, draw_backfaces: bool = False) -> None:
        super().__init__()
        self.mesh = mesh
        self.color = color
        self.wireframe = wireframe
        self.draw_backfaces = draw_backfaces
        self.last_screen_coords = None
        self.line_width = 1

        self.light_dir = np.array([0.5, 1.0, 0.5], dtype=np.float32)
        self.light_dir = self.light_dir / np.linalg.norm(self.light_dir)

    def draw(self, screen: pygame.Surface) -> None:
        if not self.mesh or not Camera3D.main:
            return
        # FIX: guard against stale Camera3D.main (destroyed camera)
        if Camera3D.main.game_object is None:
            return

        pos   = self.transform.position
        rot   = self.transform.rotation
        scale = self.transform.scale

        m_matrix = (
            translation_matrix(pos[0], pos[1], pos[2])
            @ rotation_matrix(rot[0], rot[1], rot[2])
            @ scale_matrix(scale[0], scale[1], scale[2])
        )

        v_matrix = Camera3D.main.view_matrix
        p_matrix = Camera3D.main.projection_matrix

        ndc_coords, depths = project_vertices(self.mesh.vertices, m_matrix, v_matrix, p_matrix)

        width, height = screen.get_size()
        v_x = Camera3D.main.viewport_x
        v_y = Camera3D.main.viewport_y
        v_w = Camera3D.main.viewport_width  if Camera3D.main.viewport_width  is not None else width
        v_h = Camera3D.main.viewport_height if Camera3D.main.viewport_height is not None else height

        w_half = v_w / 2.0
        h_half = v_h / 2.0

        screen_coords = np.zeros((ndc_coords.shape[0], 2), dtype=np.int32)
        screen_coords[:, 0] = v_x + (ndc_coords[:, 0] + 1.0) * w_half
        screen_coords[:, 1] = v_y + (-ndc_coords[:, 1] + 1.0) * h_half
        self.last_screen_coords = screen_coords

        rot_m = rotation_matrix(rot[0], rot[1], rot[2])[:3, :3]

        faces_to_draw = []
        near_plane = Camera3D.main.near

        for i, face in enumerate(self.mesh.faces):
            face_depths = depths[face]
            if np.any(face_depths < near_plane):
                continue

            face_normal  = self.mesh.face_normals[i]
            world_normal = rot_m @ face_normal

            v0_hom   = np.append(self.mesh.vertices[face[0]], 1.0)
            v0_world = (m_matrix @ v0_hom)[:3]
            cam_to_face = v0_world - Camera3D.main.transform.position
            norm_len = np.linalg.norm(cam_to_face)
            if norm_len > 0:
                cam_to_face = cam_to_face / norm_len

            dot_prod = np.dot(world_normal, cam_to_face)
            # FIX: use > 0 (not >= 0) so tangent faces (dot==0) are still drawn
            if not self.draw_backfaces and dot_prod > 0.0:
                continue

            # Detecção dinâmica de luz pontual (Light GameObject) na cena
            light_pos = None
            if self.game_object and self.game_object.scene:
                for go in self.game_object.scene.game_objects:
                    if (getattr(go, "mesh_type", "") == "Light" or "light" in go.name.lower()) and go.active:
                        light_pos = go.transform.position
                        break
            
            if light_pos is not None:
                l_dir = light_pos - v0_world
                l_len = np.linalg.norm(l_dir)
                if l_len > 0:
                    l_dir = l_dir / l_len
                intensity = np.dot(world_normal, l_dir)
            else:
                intensity = np.dot(world_normal, self.light_dir)

            intensity = 0.15 + 0.85 * max(0.0, intensity)

            shaded_color = (
                max(0, min(255, int(self.color[0] * intensity))),
                max(0, min(255, int(self.color[1] * intensity))),
                max(0, min(255, int(self.color[2] * intensity)))
            )

            avg_depth = np.mean(face_depths)
            points = [tuple(screen_coords[idx]) for idx in face]
            faces_to_draw.append((avg_depth, points, shaded_color))

        faces_to_draw.sort(key=lambda item: item[0], reverse=True)

        for depth, points, color in faces_to_draw:
            if self.wireframe:
                pygame.draw.polygon(screen, color, points, self.line_width)
            else:
                pygame.draw.polygon(screen, color, points, 0)
                pygame.draw.polygon(screen, color, points, 1)
