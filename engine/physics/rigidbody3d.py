"""
RigidBody3D — Componente de física 3D para a Zennity Engine.
Compativel com o pipeline do editor (PhysicsSim) e com cenas 3D independentes.
"""
from __future__ import annotations
import numpy as np
from engine.component import Component


class RigidBody3D(Component):
    """
    Física 3D baseada em impulso.
    Aplica gravidade, drag e colisão com plano Y = floor_y.
    Compativel com o mundo 3D do editor (transformação XYZ).
    """

    GRAVITY: float = 9.8          # m/s²
    FLOOR_Y: float = -0.5         # Y do chão
    RESTITUTION: float = 0.4      # elasticidade colisão chão
    FRICTION: float = 0.88        # fricção lateral

    def __init__(
        self,
        mass: float = 1.0,
        drag: float = 0.02,
        use_gravity: bool = True,
        is_kinematic: bool = False,
    ) -> None:
        super().__init__()
        self.mass: float         = max(mass, 1e-4)
        self.drag: float         = drag
        self.use_gravity: bool   = use_gravity
        self.is_kinematic: bool  = is_kinematic
        self.velocity: np.ndarray = np.zeros(3, dtype=np.float32)

    # ------------------------------------------------------------------
    def add_force(self, fx: float, fy: float, fz: float) -> None:
        if not self.is_kinematic:
            self.velocity += np.array([fx, fy, fz], np.float32) / self.mass

    def add_impulse(self, ix: float, iy: float, iz: float) -> None:
        """Impulso instantâneo (ex: pulo)."""
        if not self.is_kinematic:
            self.velocity += np.array([ix, iy, iz], np.float32)

    def stop(self) -> None:
        self.velocity[:] = 0.0

    # ------------------------------------------------------------------
    def update(self, dt: float) -> None:
        if self.is_kinematic or self.game_object is None:
            return
        dt = min(dt, 0.05)

        if self.use_gravity:
            self.velocity[1] -= self.GRAVITY * dt

        # Drag
        self.velocity *= max(0.0, 1.0 - self.drag * dt)

        # Integra posição
        self.game_object.transform.position += self.velocity * dt

        # Colisão com chão
        half_h = self.game_object.transform.scale[1] * 0.5
        bottom = self.game_object.transform.position[1] - half_h
        if bottom < self.FLOOR_Y:
            self.game_object.transform.position[1] = self.FLOOR_Y + half_h
            self.velocity[1] = -self.velocity[1] * self.RESTITUTION
            self.velocity[0] *= self.FRICTION
            self.velocity[2] *= self.FRICTION
