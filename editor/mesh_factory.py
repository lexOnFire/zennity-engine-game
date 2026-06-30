"""Geradores procedurais de malhas 3D usadas pelo editor."""
import numpy as np
from engine.assets import Mesh


def create_pyramid_mesh(size: float = 1.0) -> Mesh:
    """Pirâmide de base quadrada centrada na origem."""
    s = size / 2.0
    vertices = np.array([
        [-s, -0.4 * size, -s],
        [ s, -0.4 * size, -s],
        [ s, -0.4 * size,  s],
        [-s, -0.4 * size,  s],
        [0.0, 0.6 * size, 0.0],
    ], dtype=np.float32)
    faces = [
        [0, 1, 4],
        [1, 2, 4],
        [2, 3, 4],
        [3, 0, 4],
        [3, 2, 1, 0],
    ]
    return Mesh(vertices, faces)


def create_sphere_mesh(radius: float = 0.5, rings: int = 12, sectors: int = 12) -> Mesh:
    """Esfera UV paramétrica."""
    vertices = []
    for r in range(rings + 1):
        theta = r * np.pi / rings
        sin_t, cos_t = np.sin(theta), np.cos(theta)
        for s in range(sectors):
            phi = s * 2 * np.pi / sectors
            vertices.append([
                radius * np.cos(phi) * sin_t,
                radius * cos_t,
                radius * np.sin(phi) * sin_t,
            ])
    faces = []
    for r in range(rings):
        for s in range(sectors):
            p0 = r * sectors + s
            p1 = r * sectors + (s + 1) % sectors
            p2 = (r + 1) * sectors + (s + 1) % sectors
            p3 = (r + 1) * sectors + s
            faces.append([p0, p1, p2, p3])
    return Mesh(np.array(vertices, dtype=np.float32), faces)
