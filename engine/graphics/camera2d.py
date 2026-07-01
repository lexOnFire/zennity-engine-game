from ..component import Component
from typing import Tuple, Optional, Any
import numpy as np

class Camera2D(Component):
    """Camera component for 2D scenes. Handles panning, zoom, target follow, bounds, and coordinate conversion."""
    main: 'Camera2D' = None

    def __init__(
        self,
        zoom: float = 1.0,
        target: Optional[Any] = None,
        smoothness: float = 0.1,  # Menor = mais rápido/reativo, 0.0 = instantâneo
        bounds: Optional[Tuple[float, float, float, float]] = None,  # (min_x, min_y, max_x, max_y)
        offset: Tuple[float, float] = (0.0, 0.0)
    ) -> None:
        super().__init__()
        self.zoom = zoom
        self.target = target
        self.smoothness = smoothness
        self.bounds = bounds
        self.offset = offset

        # Define como câmera principal se nenhuma existir
        if Camera2D.main is None:
            Camera2D.main = self

    def start(self) -> None:
        if Camera2D.main is None:
            Camera2D.main = self

    def make_main(self) -> None:
        """Define esta câmera como a principal da cena 2D."""
        Camera2D.main = self

    def update(self, dt: float) -> None:
        if self.target is not None and self.game_object:
            target_pos = self.target.transform.position
            tx = target_pos[0] + self.offset[0]
            ty = target_pos[1] + self.offset[1]

            curr_pos = self.transform.position
            if self.smoothness <= 0.0:
                curr_pos[0] = tx
                curr_pos[1] = ty
            else:
                # Interpolação de movimento linear independente de taxa de quadros
                curr_pos[0] += (tx - curr_pos[0]) * min(1.0, (1.0 / self.smoothness) * dt)
                curr_pos[1] += (ty - curr_pos[1]) * min(1.0, (1.0 / self.smoothness) * dt)

            # Aplica os limites físicos de movimentação
            if self.bounds is not None:
                min_x, min_y, max_x, max_y = self.bounds
                curr_pos[0] = max(min_x, min(curr_pos[0], max_x))
                curr_pos[1] = max(min_y, min(curr_pos[1], max_y))

    def world_to_screen(self, world_pos: np.ndarray, screen_width: int, screen_height: int) -> Tuple[float, float]:
        """Converte uma coordenada do espaço de mundo [x, y] para pixels na tela [px, py]."""
        cam_pos = self.transform.position
        screen_x = (world_pos[0] - cam_pos[0]) * self.zoom + (screen_width / 2.0)
        screen_y = (world_pos[1] - cam_pos[1]) * self.zoom + (screen_height / 2.0)
        return screen_x, screen_y

    def screen_to_world(self, screen_pos: Tuple[float, float], screen_width: int, screen_height: int) -> Tuple[float, float]:
        """Converte coordenadas de pixels de tela de volta para o espaço de mundo."""
        cam_pos = self.transform.position
        world_x = (screen_pos[0] - (screen_width / 2.0)) / self.zoom + cam_pos[0]
        world_y = (screen_pos[1] - (screen_height / 2.0)) / self.zoom + cam_pos[1]
        return world_x, world_y
