from __future__ import annotations

import os
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pygame

from engine.assets.asset_database import AssetDatabase
from engine.assets.asset_importer import AssetImporter
from engine.assets.asset_metadata import AssetInfo, AssetMeta
from engine.assets.asset_path import AssetPathResolver
from engine.assets.asset_types import AssetType, detect_asset_type


class Mesh:
    """Represents a 3D polygonal mesh loaded from an OBJ file or created procedurally."""

    def __init__(self, vertices: np.ndarray, faces: List[List[int]], normals: Optional[np.ndarray] = None) -> None:
        self.vertices = np.array(vertices, dtype=np.float32)
        self.faces = faces
        self.vertex_normals = np.array(normals, dtype=np.float32) if normals is not None else None
        self.face_normals = []
        self._calculate_face_normals()

    def _calculate_face_normals(self) -> None:
        self.face_normals = []
        for face in self.faces:
            if len(face) < 3:
                self.face_normals.append(np.array([0, 0, 1], dtype=np.float32))
                continue
            v0 = self.vertices[face[0]]
            v1 = self.vertices[face[1]]
            v2 = self.vertices[face[2]]
            normal = np.cross(v1 - v0, v2 - v0)
            norm = np.linalg.norm(normal)
            if norm > 0:
                normal = normal / norm
            else:
                normal = np.array([0.0, 0.0, 1.0], dtype=np.float32)
            self.face_normals.append(normal)
        self.face_normals = np.array(self.face_normals, dtype=np.float32)


class Assets:
    """Legacy runtime asset cache kept compatible with earlier engine code."""

    _images: Dict[str, pygame.Surface] = {}
    _sounds: Dict[str, pygame.mixer.Sound] = {}
    _fonts: Dict[Tuple[str, int], pygame.font.Font] = {}
    _meshes: Dict[str, Mesh] = {}

    @classmethod
    def get_image(cls, path: str, alpha: bool = True) -> pygame.Surface:
        if path not in cls._images:
            if not os.path.exists(path):
                fallback = pygame.Surface((32, 32))
                fallback.fill((255, 0, 255))
                cls._images[path] = fallback
            else:
                img = pygame.image.load(path)
                cls._images[path] = img.convert_alpha() if alpha else img.convert()
        return cls._images[path]

    @classmethod
    def load_sprite_sheet(cls, path: str, frame_width: int, frame_height: int) -> List[pygame.Surface]:
        sheet = cls.get_image(path)
        sheet_width, sheet_height = sheet.get_size()
        frames = []
        for y in range(0, sheet_height, frame_height):
            for x in range(0, sheet_width, frame_width):
                if x + frame_width <= sheet_width and y + frame_height <= sheet_height:
                    frame = pygame.Surface((frame_width, frame_height), pygame.SRCALPHA)
                    frame.blit(sheet, (0, 0), (x, y, frame_width, frame_height))
                    frames.append(frame)
        return frames

    @classmethod
    def get_sound(cls, path: str) -> pygame.mixer.Sound:
        if path not in cls._sounds:
            if not os.path.exists(path):
                class NullSound:
                    def play(self, *args, **kwargs): pass
                    def stop(self): pass
                    def set_volume(self, *args): pass
                cls._sounds[path] = NullSound()
            else:
                cls._sounds[path] = pygame.mixer.Sound(path)
        return cls._sounds[path]

    @classmethod
    def play_music(cls, path: str, loops: int = -1, volume: float = 0.5) -> None:
        if os.path.exists(path):
            pygame.mixer.music.load(path)
            pygame.mixer.music.set_volume(volume)
            pygame.mixer.music.play(loops)

    @classmethod
    def get_font(cls, name: Optional[str], size: int) -> pygame.font.Font:
        key = (name or "sys_default", size)
        if key not in cls._fonts:
            if name is None or not os.path.exists(name):
                cls._fonts[key] = pygame.font.SysFont("Arial", size)
            else:
                cls._fonts[key] = pygame.font.Font(name, size)
        return cls._fonts[key]

    @classmethod
    def get_mesh(cls, path: str) -> Mesh:
        if path not in cls._meshes:
            cls._meshes[path] = cls.create_cube_mesh() if not os.path.exists(path) else cls._load_obj(path)
        return cls._meshes[path]

    @classmethod
    def _load_obj(cls, path: str) -> Mesh:
        vertices = []
        faces = []
        normals = []
        with open(path, "r") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                parts = line.split()
                if parts[0] == "v":
                    vertices.append([float(parts[1]), float(parts[2]), float(parts[3])])
                elif parts[0] == "vn":
                    normals.append([float(parts[1]), float(parts[2]), float(parts[3])])
                elif parts[0] == "f":
                    face = []
                    for vert_token in parts[1:]:
                        v_idx = int(vert_token.split("/")[0])
                        face.append(v_idx - 1 if v_idx > 0 else len(vertices) + v_idx)
                    faces.append(face)
        norms_arr = np.array(normals, dtype=np.float32) if normals else None
        return Mesh(np.array(vertices, dtype=np.float32), faces, norms_arr)

    @classmethod
    def create_cube_mesh(cls, size: float = 1.0) -> Mesh:
        s = size / 2.0
        vertices = np.array([
            [-s, -s, -s],
            [s, -s, -s],
            [s, s, -s],
            [-s, s, -s],
            [-s, -s, s],
            [s, -s, s],
            [s, s, s],
            [-s, s, s],
        ], dtype=np.float32)
        faces = [
            [0, 3, 2, 1],
            [1, 2, 6, 5],
            [5, 6, 7, 4],
            [4, 7, 3, 0],
            [3, 7, 6, 2],
            [0, 1, 5, 4],
        ]
        return Mesh(vertices, faces)


__all__ = [
    "Any",
    "AssetDatabase",
    "AssetImporter",
    "AssetInfo",
    "AssetMeta",
    "AssetPathResolver",
    "AssetType",
    "Assets",
    "Mesh",
    "detect_asset_type",
]
