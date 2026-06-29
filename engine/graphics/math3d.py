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
    
    # Rotation about X axis
    rot_x = np.array([
        [1, 0, 0, 0],
        [0, np.cos(rx), -np.sin(rx), 0],
        [0, np.sin(rx),  np.cos(rx), 0],
        [0, 0, 0, 1]
    ], dtype=np.float32)
    
    # Rotation about Y axis
    rot_y = np.array([
        [np.cos(ry), 0, np.sin(ry), 0],
        [0, 1, 0, 0],
        [-np.sin(ry), 0, np.cos(ry), 0],
        [0, 0, 0, 1]
    ], dtype=np.float32)
    
    # Rotation about Z axis
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
    """Calculates the view matrix from the camera position and rotation (Euler angles in degrees)."""
    # View matrix is the inverse of the camera's translation and rotation.
    # Inverse translation
    t_inv = translation_matrix(-cam_pos[0], -cam_pos[1], -cam_pos[2])
    
    # Inverse rotation: transpose of rotation matrix (since it's orthogonal)
    # We rotate by negative angles in reverse order.
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
    
    # Combined inverse rotation: Rz * Rx * Ry
    r_inv = rot_z @ rot_x @ rot_y
    
    return r_inv @ t_inv

def project_vertices(vertices: np.ndarray, model_matrix: np.ndarray, view_matrix: np.ndarray, proj_matrix: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """Transforms 3D vertices using Model-View-Projection matrices.
    Returns:
      - projected: np.ndarray shape (N, 2) in screen pixel coordinates.
      - camera_z: np.ndarray shape (N,) containing camera-space Z-depths (useful for clipping and depth sorting).
    """
    # Convert vertices to homogeneous coordinates (add w=1 column)
    N = vertices.shape[0]
    homogeneous_vertices = np.hstack((vertices, np.ones((N, 1), dtype=np.float32)))
    
    # 1. Transform to world space
    world_verts = (model_matrix @ homogeneous_vertices.T).T
    
    # 2. Transform to camera space
    cam_verts = (view_matrix @ world_verts.T).T
    
    # Camera space coordinates
    cx, cy, cz = cam_verts[:, 0], cam_verts[:, 1], cam_verts[:, 2]
    
    # 3. Transform to clip space using projection matrix
    clip_verts = (proj_matrix @ cam_verts.T).T
    
    # 4. Perspective division (divide x, y, z by w)
    w = clip_verts[:, 3]
    # Avoid divide-by-zero
    w = np.where(np.abs(w) < 1e-5, 1e-5 * np.sign(w), w)
    
    ndc_x = clip_verts[:, 0] / w
    ndc_y = clip_verts[:, 1] / w
    
    # Return camera Z (depth) for clipping. In camera space, Z is positive in front of camera.
    depth = cz
    
    return np.column_stack((ndc_x, ndc_y)), depth
