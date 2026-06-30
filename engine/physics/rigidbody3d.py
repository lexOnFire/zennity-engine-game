"""
RigidBody3D — Componente de física 3D para a Zennity Engine.
"""
from __future__ import annotations
import numpy as np
from engine.component import Component


class RigidBody3D(Component):
    """
    Física 3D baseada em impulso.
    Aplica gravidade, drag e colisão com plano Y = floor_y.
    """

    GRAVITY:     float = 9.8
    FLOOR_Y:     float = -0.5
    RESTITUTION: float = 0.4
    FRICTION:    float = 0.88
    # Velocidade mínima após ricochete: abaixo disso o objeto “dorme” no chão
    SLEEP_VEL:   float = 0.5

    def __init__(
        self,
        mass: float = 1.0,
        drag: float = 0.02,
        use_gravity: bool = True,
        is_kinematic: bool = False,
    ) -> None:
        super().__init__()
        self.mass:         float      = max(mass, 1e-4)
        self.drag:         float      = drag
        self.use_gravity:  bool       = use_gravity
        self.is_kinematic: bool       = is_kinematic
        self.velocity:     np.ndarray = np.zeros(3, dtype=np.float32)
        self._sleeping:    bool       = False

    def add_force(self, fx: float, fy: float, fz: float) -> None:
        if not self.is_kinematic:
            self._sleeping = False
            self.velocity += np.array([fx, fy, fz], np.float32) / self.mass

    def add_impulse(self, ix: float, iy: float, iz: float) -> None:
        if not self.is_kinematic:
            self._sleeping = False
            self.velocity += np.array([ix, iy, iz], np.float32)

    def stop(self) -> None:
        self.velocity[:] = 0.0
        self._sleeping   = True

    def update(self, dt: float) -> None:
        if self.is_kinematic or self.game_object is None:
            return
        # Objeto "dormindo" (pousado no chão) — não simular até receber impulso/força
        if self._sleeping:
            return

        dt = min(dt, 0.05)

        if self.use_gravity:
            self.velocity[1] -= self.GRAVITY * dt

        self.velocity *= max(0.0, 1.0 - self.drag * dt)

        self.game_object.transform.position += self.velocity * dt

        # FIX: guard against scale[1] == 0 (flat objects stuck on floor forever)
        scale_y = self.game_object.transform.scale[1]
        if abs(scale_y) < 1e-4:
            return
        half_h = scale_y * 0.5
        bottom = self.game_object.transform.position[1] - half_h
        if bottom < self.FLOOR_Y:
            self.game_object.transform.position[1] = self.FLOOR_Y + half_h
            bounce_vy = -self.velocity[1] * self.RESTITUTION
            # FIX: se a velocidade pós-ricochete for menor que o threshold,
            # zerar e "dormir" o objeto — isso elimina o flutuar infinito
            if abs(bounce_vy) < self.SLEEP_VEL:
                self.velocity[1] = 0.0
                self.velocity[0] = 0.0
                self.velocity[2] = 0.0
                self._sleeping   = True
            else:
                self.velocity[1]  = bounce_vy
                self.velocity[0] *= self.FRICTION
                self.velocity[2] *= self.FRICTION
