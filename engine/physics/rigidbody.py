import numpy as np
from typing import Optional
from engine.component import Component


class RigidBody(Component):
    """
    Componente de física que aplica gravidade, velocidade e movimento
    ao Transform do GameObject a cada frame.
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
        self.mass: float = max(mass, 0.0001)  # evita divisão por zero
        self.gravity_scale: float = gravity_scale
        self.drag: float = drag          # amortecimento linear (0 = sem atrito)
        self.use_gravity: bool = use_gravity
        self.is_kinematic: bool = is_kinematic  # se True, não sofre forças externas

        # Vetores de estado
        self.velocity: np.ndarray = np.zeros(2, dtype=np.float32)   # px/s
        self.acceleration: np.ndarray = np.zeros(2, dtype=np.float32)

        # Constante de gravidade (px/s²) — pode ser sobrescrita por cena
        self.GRAVITY: float = 980.0

    # ------------------------------------------------------------------
    # Força e impulso
    # ------------------------------------------------------------------

    def add_force(self, fx: float, fy: float) -> None:
        """Aplica uma força contínua (F = m*a, portanto a += F/m)."""
        if self.is_kinematic:
            return
        self.acceleration += np.array([fx, fy], dtype=np.float32) / self.mass

    def add_impulse(self, ix: float, iy: float) -> None:
        """Aplica um impulso instantâneo diretamente na velocidade."""
        if self.is_kinematic:
            return
        self.velocity += np.array([ix, iy], dtype=np.float32) / self.mass

    def set_velocity(self, vx: float, vy: float) -> None:
        """Define a velocidade diretamente (útil para movimento controlado)."""
        self.velocity = np.array([vx, vy], dtype=np.float32)

    def stop(self) -> None:
        """Zera a velocidade e aceleração."""
        self.velocity[:] = 0.0
        self.acceleration[:] = 0.0

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update(self, dt: float) -> None:
        if self.is_kinematic or self.game_object is None:
            return

        # Gravidade
        if self.use_gravity:
            self.acceleration[1] += self.GRAVITY * self.gravity_scale

        # Integração de Euler semi-implícita
        self.velocity += self.acceleration * dt

        # Drag (amortecimento)
        if self.drag > 0.0:
            factor = max(0.0, 1.0 - self.drag * dt)
            self.velocity *= factor

        # Aplica movimento ao Transform
        transform = self.game_object.transform
        transform.x += self.velocity[0] * dt
        transform.y += self.velocity[1] * dt

        # Reseta aceleração (forças devem ser aplicadas todo frame)
        self.acceleration[:] = 0.0
