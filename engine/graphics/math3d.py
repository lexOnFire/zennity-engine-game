import numpy as np
from typing import Tuple

def translation_matrix(x: float, y: float, z: float) -> np.ndarray:
    """Returns a 4x4 translation matrix."""
    return np.array([
        [1, 0, 0, x],
        [0, 1, 0, y],
        [0, 0, 1, z],
        [0, 0, 0, 1]
    ], dtype=np.float32)

def scale_matrix(sx: float, sy: float, sz: float) -> np.ndarray:
    """Returns a 4x4 scale matrix."""
    return np.array([
        [sx,  0,  0, 0],
        [ 0, sy,  0, 0],
        [ 0,  0, sz, 0],
        [ 0,  0,  0, 1]
    ], dtype=np.float32)

def rotation_matrix(rx_deg: float, ry_deg: float, rz_deg: float) -> np.ndarray:
    """Returns a 4x4 rotation matrix combining X, Y, and Z rotations (in degrees)."""
    rx = np.radians(rx_deg)
    ry = np.radians(ry_deg)
    rz = np.radians(rz_deg)

    rot_x = np.array([
        [1, 0, 0, 0],
        [0, np.cos(rx), -np.sin(rx), 0],
        [0, np.sin(rx),  np.cos(rx), 0],
        [0, 0, 0, 1]
    ], dtype=np.float32)

    rot_y = np.array([
        [np.cos(ry), 0, np.sin(ry), 0],
        [0, 1, 0, 0],
        [-np.sin(ry), 0, np.cos(ry), 0],
        [0, 0, 0, 1]
    ], dtype=np.float32)

    rot_z = np.array([
        [np.cos(rz), -np.sin(rz), 0, 0],
        [np.sin(rz),  np.cos(rz), 0, 0],
        [0, 0, 1, 0],
        [0, 0, 0, 1]
    ], dtype=np.float32)

    # Combined rotation: Ry * Rx * Rz
    return rot_y @ rot_x @ rot_z

def projection_matrix(fov_deg: float, aspect_ratio: float, near: float, far: float) -> np.ndarray:
    """Returns a standard 4x4 perspective projection matrix."""
    fov_rad = np.radians(fov_deg)
    f = 1.0 / np.tan(fov_rad / 2.0)

    proj = np.zeros((4, 4), dtype=np.float32)
    proj[0, 0] = f / aspect_ratio
    proj[1, 1] = f
    proj[2, 2] = (far + near) / (far - near)
    proj[2, 3] = (-2.0 * far * near) / (far - near)
    proj[3, 2] = 1.0
    return proj

def view_matrix(cam_pos: np.ndarray, cam_rot: np.ndarray) -> np.ndarray:
    """Calculates the view matrix from the camera position and rotation (Euler angles in degrees).
    Correct order: inverse_rotation @ inverse_translation = Rz(-z) @ Rx(-x) @ Ry(-y) @ T(-pos)
    This is the transpose/inverse of the camera's world transform.
    """
    t_inv = translation_matrix(-cam_pos[0], -cam_pos[1], -cam_pos[2])

    rx = np.radians(-cam_rot[0])
    ry = np.radians(-cam_rot[1])
    rz = np.radians(-cam_rot[2])

    rot_x = np.array([
        [1, 0, 0, 0],
        [0, np.cos(rx), -np.sin(rx), 0],
        [0, np.sin(rx),  np.cos(rx), 0],
        [0, 0, 0, 1]
    ], dtype=np.float32)

    rot_y = np.array([
        [np.cos(ry), 0, np.sin(ry), 0],
        [0, 1, 0, 0],
        [-np.sin(ry), 0, np.cos(ry), 0],
        [0, 0, 0, 1]
    ], dtype=np.float32)

    rot_z = np.array([
        [np.cos(rz), -np.sin(rz), 0, 0],
        [np.sin(rz),  np.cos(rz), 0, 0],
        [0, 0, 1, 0],
        [0, 0, 0, 1]
    ], dtype=np.float32)

    # Correct inverse rotation order: Ry(-y) @ Rx(-x) @ Rz(-z)
    # (inverse of Rz @ Rx @ Ry from rotation_matrix)
    r_inv = rot_y @ rot_x @ rot_z

    return r_inv @ t_inv

def project_vertices(
    vertices: np.ndarray,
    model_matrix: np.ndarray,
    view_matrix: np.ndarray,
    proj_matrix: np.ndarray
) -> Tuple[np.ndarray, np.ndarray]:
    """Transforms 3D vertices using Model-View-Projection matrices.
    Returns:
      - projected: np.ndarray shape (N, 2) in NDC coordinates.
      - depth:     np.ndarray shape (N,) camera-space Z depths.
    """
    N = vertices.shape[0]
    homogeneous_vertices = np.hstack((vertices, np.ones((N, 1), dtype=np.float32)))

    world_verts = (model_matrix @ homogeneous_vertices.T).T
    cam_verts   = (view_matrix  @ world_verts.T).T
    clip_verts  = (proj_matrix  @ cam_verts.T).T

    w = clip_verts[:, 3]
    # FIX: safe divide — avoids w==0 case where sign(0)==0 still gives 0
    w = np.where(w >= 0, np.maximum(w,  1e-5),
                         np.minimum(w, -1e-5))

    ndc_x = clip_verts[:, 0] / w
    ndc_y = clip_verts[:, 1] / w

    depth = cam_verts[:, 2]

    return np.column_stack((ndc_x, ndc_y)), depth
