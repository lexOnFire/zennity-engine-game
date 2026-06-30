import numpy as np
from typing import Optional
from engine.component import Component


class RigidBody(Component):
    """
    Componente de física 2D: gravidade, velocidade e movimento
    ao Transform do GameObject a cada frame.
    FIX: gravidade aplicada diretamente na velocidade (não via acceleration)
    para evitar vazamento quando forças externas e gravidade dividiam o mesmo array.
    """

    def __init__(
        self,
        mass: float = 1.0,
        gravity_scale: float = 1.0,
        drag: float = 0.0,
        use_gravity: bool = True,
        is_kinematic: bool = False,
    ) -> None:
        super().__init__()
        self.mass:          float = max(mass, 0.0001)
        self.gravity_scale: float = gravity_scale
        self.drag:          float = drag
        self.use_gravity:   bool  = use_gravity
        self.is_kinematic:  bool  = is_kinematic

        self.velocity:     np.ndarray = np.zeros(2, dtype=np.float32)
        # acceleration stores only EXTERNAL forces (not gravity)
        self.acceleration: np.ndarray = np.zeros(2, dtype=np.float32)

        self.GRAVITY: float = 980.0

    # ------------------------------------------------------------------

    def add_force(self, fx: float, fy: float) -> None:
        if self.is_kinematic:
            return
        self.acceleration += np.array([fx, fy], dtype=np.float32) / self.mass

    def add_impulse(self, ix: float, iy: float) -> None:
        if self.is_kinematic:
            return
        self.velocity += np.array([ix, iy], dtype=np.float32) / self.mass

    def set_velocity(self, vx: float, vy: float) -> None:
        self.velocity = np.array([vx, vy], dtype=np.float32)

    def stop(self) -> None:
        self.velocity[:]     = 0.0
        self.acceleration[:] = 0.0

    # ------------------------------------------------------------------

    def update(self, dt: float) -> None:
        if self.is_kinematic or self.game_object is None:
            return

        # FIX: apply gravity directly to velocity, separate from external forces
        if self.use_gravity:
            self.velocity[1] += self.GRAVITY * self.gravity_scale * dt

        # Integrate external forces
        self.velocity += self.acceleration * dt

        if self.drag > 0.0:
            self.velocity *= max(0.0, 1.0 - self.drag * dt)

        transform = self.game_object.transform
        transform.x += self.velocity[0] * dt
        transform.y += self.velocity[1] * dt

        # Reset external forces (gravity is NOT here — it's in velocity directly)
        self.acceleration[:] = 0.0
