import pygame
import os
from typing import Dict, List, Tuple, Any, Optional
import numpy as np

class Mesh:
    """Represents a 3D polygonal mesh loaded from an OBJ file or created procedurally."""
    def __init__(self, vertices: np.ndarray, faces: List[List[int]], normals: Optional[np.ndarray] = None) -> None:
        self.vertices = np.array(vertices, dtype=np.float32)  # shape (N, 3)
        self.faces = faces  # List of list of vertex indices (e.g. [[0, 1, 2], [2, 3, 0]])
        self.vertex_normals = np.array(normals, dtype=np.float32) if normals is not None else None
        
        # Calculate face normals for flat lighting
        self.face_normals = []
        self._calculate_face_normals()

    def _calculate_face_normals(self) -> None:
        self.face_normals = []
        for face in self.faces:
            if len(face) < 3:
                self.face_normals.append(np.array([0, 0, 1], dtype=np.float32))
                continue
            # Get 3 vertices of the face
            v0 = self.vertices[face[0]]
            v1 = self.vertices[face[1]]
            v2 = self.vertices[face[2]]
            
            # Vectors along two edges
            edge1 = v1 - v0
            edge2 = v2 - v0
            
            # Cross product gives the normal vector
            normal = np.cross(edge1, edge2)
            norm = np.linalg.norm(normal)
            if norm > 0:
                normal = normal / norm
            else:
                normal = np.array([0.0, 0.0, 1.0], dtype=np.float32)
                
            self.face_normals.append(normal)
        self.face_normals = np.array(self.face_normals, dtype=np.float32)


class Assets:
    """Manages loading and caching of game assets (images, audio, fonts, 3D meshes)."""
    _images: Dict[str, pygame.Surface] = {}
    _sounds: Dict[str, pygame.mixer.Sound] = {}
    _fonts: Dict[Tuple[str, int], pygame.font.Font] = {}
    _meshes: Dict[str, Mesh] = {}

    @classmethod
    def get_image(cls, path: str, alpha: bool = True) -> pygame.Surface:
        """Loads and caches an image. Automatically converts pixel formats."""
        if path not in cls._images:
            if not os.path.exists(path):
                # Return a fallback colored square surface if image is missing
                fallback = pygame.Surface((32, 32))
                fallback.fill((255, 0, 255))  # Magenta magenta placeholder
                cls._images[path] = fallback
            else:
                img = pygame.image.load(path)
                if alpha:
                    cls._images[path] = img.convert_alpha()
                else:
                    cls._images[path] = img.convert()
        return cls._images[path]

    @classmethod
    def load_sprite_sheet(cls, path: str, frame_width: int, frame_height: int) -> List[pygame.Surface]:
        """Slices a sprite sheet into a list of individual frames."""
        sheet = cls.get_image(path)
        sheet_width, sheet_height = sheet.get_size()
        frames = []
        for y in range(0, sheet_height, frame_height):
            for x in range(0, sheet_width, frame_width):
                # Ensure we don't slice out of bounds
                if x + frame_width <= sheet_width and y + frame_height <= sheet_height:
                    frame = pygame.Surface((frame_width, frame_height), pygame.SRCALPHA)
                    frame.blit(sheet, (0, 0), (x, y, frame_width, frame_height))
                    frames.append(frame)
        return frames

    @classmethod
    def get_sound(cls, path: str) -> pygame.mixer.Sound:
        """Loads and caches a sound effect."""
        if path not in cls._sounds:
            if not os.path.exists(path):
                # Null Sound fallback to prevent crash
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
        """Plays background music using the pygame stream channel."""
        if os.path.exists(path):
            pygame.mixer.music.load(path)
            pygame.mixer.music.set_volume(volume)
            pygame.mixer.music.play(loops)

    @classmethod
    def get_font(cls, name: Optional[str], size: int) -> pygame.font.Font:
        """Loads and caches a font. Pass None for the system default font."""
        key = (name or "sys_default", size)
        if key not in cls._fonts:
            if name is None or not os.path.exists(name):
                cls._fonts[key] = pygame.font.SysFont("Arial", size)
            else:
                cls._fonts[key] = pygame.font.Font(name, size)
        return cls._fonts[key]

    @classmethod
    def get_mesh(cls, path: str) -> Mesh:
        """Loads and caches a 3D Mesh from an OBJ file."""
        if path not in cls._meshes:
            if not os.path.exists(path):
                # Return a basic fallback Cube mesh if file doesn't exist
                cls._meshes[path] = cls.create_cube_mesh()
            else:
                cls._meshes[path] = cls._load_obj(path)
        return cls._meshes[path]

    @classmethod
    def _load_obj(cls, path: str) -> Mesh:
        """Parses a simple Wavefront OBJ file."""
        vertices = []
        faces = []
        normals = []
        
        with open(path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                parts = line.split()
                prefix = parts[0]
                
                if prefix == 'v':
                    vertices.append([float(parts[1]), float(parts[2]), float(parts[3])])
                elif prefix == 'vn':
                    normals.append([float(parts[1]), float(parts[2]), float(parts[3])])
                elif prefix == 'f':
                    face = []
                    for vert_token in parts[1:]:
                        # Format can be: v or v/vt or v/vt/vn or v//vn
                        indices = vert_token.split('/')
                        v_idx = int(indices[0])
                        # Handle positive/negative OBJ indices (1-based to 0-based)
                        if v_idx > 0:
                            v_idx -= 1
                        else:
                            # Negative index counts from end of loaded vertices
                            v_idx = len(vertices) + v_idx
                        face.append(v_idx)
                    faces.append(face)
        
        # If there are no normals parsed, set to None
        norms_arr = np.array(normals, dtype=np.float32) if normals else None
        return Mesh(np.array(vertices, dtype=np.float32), faces, norms_arr)

    @classmethod
    def create_cube_mesh(cls, size: float = 1.0) -> Mesh:
        """Procedurally creates a 3D Cube mesh centered at the origin."""
        s = size / 2.0
        vertices = np.array([
            [-s, -s, -s],  # 0
            [ s, -s, -s],  # 1
            [ s,  s, -s],  # 2
            [-s,  s, -s],  # 3
            [-s, -s,  s],  # 4
            [ s, -s,  s],  # 5
            [ s,  s,  s],  # 6
            [-s,  s,  s]   # 7
        ], dtype=np.float32)

        # 6 faces of the cube, vertices defined in counter-clockwise order when looking from outside
        faces = [
            [0, 3, 2, 1],  # Back
            [1, 2, 6, 5],  # Right
            [5, 6, 7, 4],  # Front
            [4, 7, 3, 0],  # Left
            [3, 7, 6, 2],  # Top
            [0, 1, 5, 4]   # Bottom
        ]
        
        return Mesh(vertices, faces)
