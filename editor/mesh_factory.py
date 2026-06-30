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


def create_plane_mesh(size: float = 2.0, subdivisions: int = 1) -> Mesh:
    """Plano horizontal (XZ) centrado na origem, com subdivisoes opcionais."""
    s = size / 2.0
    step = size / max(subdivisions, 1)
    vertices = []
    for iz in range(subdivisions + 1):
        for ix in range(subdivisions + 1):
            x = -s + ix * step
            z = -s + iz * step
            vertices.append([x, 0.0, z])
    faces = []
    n = subdivisions + 1
    for iz in range(subdivisions):
        for ix in range(subdivisions):
            p0 = iz * n + ix
            p1 = iz * n + ix + 1
            p2 = (iz + 1) * n + ix + 1
            p3 = (iz + 1) * n + ix
            faces.append([p0, p1, p2, p3])
    return Mesh(np.array(vertices, dtype=np.float32), faces)


def create_capsule_mesh(radius: float = 0.4, height: float = 1.0,
                        rings: int = 8, sectors: int = 12) -> Mesh:
    """Capsula (cilindro com semiesferas nas extremidades)."""
    vertices = []
    faces = []

    half_h = height / 2.0

    # --- semiesfera superior ---
    for r in range(rings // 2 + 1):
        theta = r * np.pi / rings  # 0 -> pi/2
        sin_t, cos_t = np.sin(theta), np.cos(theta)
        for s in range(sectors):
            phi = s * 2 * np.pi / sectors
            vertices.append([
                radius * np.cos(phi) * sin_t,
                half_h + radius * cos_t,
                radius * np.sin(phi) * sin_t,
            ])

    top_rings = rings // 2 + 1

    # --- semiesfera inferior ---
    for r in range(rings // 2, rings + 1):
        theta = r * np.pi / rings  # pi/2 -> pi
        sin_t, cos_t = np.sin(theta), np.cos(theta)
        for s in range(sectors):
            phi = s * 2 * np.pi / sectors
            vertices.append([
                radius * np.cos(phi) * sin_t,
                -half_h + radius * cos_t,
                radius * np.sin(phi) * sin_t,
            ])

    total_rings = rings + 1  # top_rings + bot_rings - 1 (anel equatorial compartilhado)

    for r in range(total_rings - 1):
        for s in range(sectors):
            p0 = r * sectors + s
            p1 = r * sectors + (s + 1) % sectors
            p2 = (r + 1) * sectors + (s + 1) % sectors
            p3 = (r + 1) * sectors + s
            faces.append([p0, p1, p2, p3])

    return Mesh(np.array(vertices, dtype=np.float32), faces)
