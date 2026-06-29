from ..component import Component
from typing import Tuple
import numpy as np

class Camera2D(Component):
    """Camera component for 2D scenes. Handles panning, zoom, and coordinate conversion."""
    main: 'Camera2D' = None

    def __init__(self, zoom: float = 1.0) -> None:
        super().__init__()
        self.zoom = zoom
        # Set this as the main camera if none exists
        if Camera2D.main is None:
            Camera2D.main = self

    def start(self) -> None:
        if Camera2D.main is None:
            Camera2D.main = self

    def make_main(self) -> None:
        """Sets this camera as the primary camera for the 2D scene."""
        Camera2D.main = self

    def world_to_screen(self, world_pos: np.ndarray, screen_width: int, screen_height: int) -> Tuple[float, float]:
        """Converts a world position [x, y] to screen space pixels [px, py]."""
        cam_pos = self.transform.position
        # Center of screen is (screen_width / 2, screen_height / 2)
        screen_x = (world_pos[0] - cam_pos[0]) * self.zoom + (screen_width / 2.0)
        # Flip Y coordinate in 2D so that up in world space is up on screen (optional,
        # but let's keep it simple: Y goes down in standard Pygame, which is fine, 
        # or we can follow standard screen space where Y goes down. Let's follow 
        # standard screen space where Y goes down, so we don't flip unless the user wants).
        # Let's stick to standard Pygame coordinate mapping (Y down) to keep things intuitive.
        screen_y = (world_pos[1] - cam_pos[1]) * self.zoom + (screen_height / 2.0)
        return screen_x, screen_y

    def screen_to_world(self, screen_pos: Tuple[float, float], screen_width: int, screen_height: int) -> Tuple[float, float]:
        """Converts screen pixel coordinates back into world coordinates."""
        cam_pos = self.transform.position
        world_x = (screen_pos[0] - (screen_width / 2.0)) / self.zoom + cam_pos[0]
        world_y = (screen_pos[1] - (screen_height / 2.0)) / self.zoom + cam_pos[1]
        return world_x, world_y
