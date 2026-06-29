from typing import Optional, TYPE_CHECKING
import numpy as np

if TYPE_CHECKING:
    from .game_object import GameObject


class Component:
    """Base class for all components that can be attached to GameObjects."""
    def __init__(self) -> None:
        self.game_object: Optional['GameObject'] = None
        self._started: bool = False

    @property
    def transform(self) -> 'Transform':
        """Quick access to the GameObject's transform."""
        assert self.game_object is not None, "Component not attached to a GameObject"
        return self.game_object.transform

    def start(self) -> None:
        """Called once before the component's first update."""
        pass

    def update(self, dt: float) -> None:
        """Called every frame to update component logic."""
        pass

    def draw(self, screen) -> None:
        """Called every frame to draw component graphics."""
        pass

    def destroy(self) -> None:
        """Called when the component or GameObject is destroyed."""
        pass


class Transform(Component):
    """Component that stores position, rotation, and scale in 2D or 3D space."""
    def __init__(self, 
                 x: float = 0.0, y: float = 0.0, z: float = 0.0,
                 rx: float = 0.0, ry: float = 0.0, rz: float = 0.0,
                 sx: float = 1.0, sy: float = 1.0, sz: float = 1.0) -> None:
        super().__init__()
        
        # Position, rotation (in degrees), and scale as numpy float arrays for fast math
        self._position = np.array([x, y, z], dtype=np.float32)
        self._rotation = np.array([rx, ry, rz], dtype=np.float32)
        self._scale = np.array([sx, sy, sz], dtype=np.float32)

    # Position getters and setters
    @property
    def position(self) -> np.ndarray:
        return self._position

    @position.setter
    def position(self, val: np.ndarray) -> None:
        self._position = np.array(val, dtype=np.float32)

    @property
    def x(self) -> float: return float(self._position[0])
    @x.setter
    def x(self, val: float) -> None: self._position[0] = val

    @property
    def y(self) -> float: return float(self._position[1])
    @y.setter
    def y(self, val: float) -> None: self._position[1] = val

    @property
    def z(self) -> float: return float(self._position[2])
    @z.setter
    def z(self, val: float) -> None: self._position[2] = val

    # Rotation getters and setters (in degrees)
    @property
    def rotation(self) -> np.ndarray:
        return self._rotation

    @rotation.setter
    def rotation(self, val: np.ndarray) -> None:
        self._rotation = np.array(val, dtype=np.float32)

    @property
    def rx(self) -> float: return float(self._rotation[0])
    @rx.setter
    def rx(self, val: float) -> None: self._rotation[0] = val

    @property
    def ry(self) -> float: return float(self._rotation[1])
    @ry.setter
    def ry(self, val: float) -> None: self._rotation[1] = val

    @property
    def rz(self) -> float: return float(self._rotation[2])
    @rz.setter
    def rz(self, val: float) -> None: self._rotation[2] = val

    # Scale getters and setters
    @property
    def scale(self) -> np.ndarray:
        return self._scale

    @scale.setter
    def scale(self, val: np.ndarray) -> None:
        self._scale = np.array(val, dtype=np.float32)

    @property
    def sx(self) -> float: return float(self._scale[0])
    @sx.setter
    def sx(self, val: float) -> None: self._scale[0] = val

    @property
    def sy(self) -> float: return float(self._scale[1])
    @sy.setter
    def sy(self, val: float) -> None: self._scale[1] = val

    @property
    def sz(self) -> float: return float(self._scale[2])
    @sz.setter
    def sz(self, val: float) -> None: self._scale[2] = val

    def translate(self, dx: float, dy: float, dz: float = 0.0) -> None:
        """Moves the transform by the given amounts."""
        self._position += np.array([dx, dy, dz], dtype=np.float32)

    def rotate(self, drx: float, dry: float, drz: float) -> None:
        """Rotates the transform by the given degree amounts."""
        self._rotation += np.array([drx, dry, drz], dtype=np.float32)

    def get_world_position(self) -> np.ndarray:
        """Calculates the absolute position in world space, factoring in parents."""
        if self.game_object and self.game_object.parent:
            parent_pos = self.game_object.parent.transform.get_world_position()
            # Simple translation cascading (note: ignores parent scaling and rotations for simplicity in 2D,
            # but fully sufficient for our hierarchy design)
            return parent_pos + self._position
        return self._position
