import numpy as np
from typing import Any, Optional
from engine.core.component import Component


class RigidBody(Component):
    """
    Componente de física 2D: gravidade, velocidade e movimento
    ao Transform do GameObject a cada frame.
    FIX: gravidade aplicada diretamente na velocidade (não via acceleration)
    para evitar vazamento quando forças externas e gravidade dividiam o mesmo array.

    Adicionado: atributo `grounded` para integração com TilemapCollider.
    """
    component_type = "RigidBody"
    unique = True

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

        # Flag definida pelo TilemapCollider a cada frame
        self.grounded: bool = False

        self.GRAVITY: float = 980.0

    def serialize_properties(self) -> dict[str, Any]:
        return {
            "mass": float(self.mass),
            "gravity_scale": float(self.gravity_scale),
            "drag": float(self.drag),
            "use_gravity": bool(self.use_gravity),
            "is_kinematic": bool(self.is_kinematic),
            "velocity": [float(v) for v in self.velocity],
            "acceleration": [float(v) for v in self.acceleration],
        }

    def deserialize_properties(self, data: dict[str, Any]) -> None:
        self.mass = max(float(data.get("mass", 1.0)), 0.0001)
        self.gravity_scale = float(data.get("gravity_scale", 1.0))
        self.drag = float(data.get("drag", 0.0))
        self.use_gravity = bool(data.get("use_gravity", True))
        self.is_kinematic = bool(data.get("is_kinematic", False))
        self.velocity = np.array(data.get("velocity", [0.0, 0.0]), dtype=np.float32)
        self.acceleration = np.array(data.get("acceleration", [0.0, 0.0]), dtype=np.float32)

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

        # Reseta grounded a cada frame (TilemapCollider seta de volta se estiver no chão)
        self.grounded = False

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

        # Reset external forces (gravity is NOT here — it’s in velocity directly)
        self.acceleration[:] = 0.0


from engine.core.component_registry import register_component

register_component(RigidBody)
register_component(RigidBody, "Rigidbody")
