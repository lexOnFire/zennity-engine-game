import numpy as np
from typing import Optional
from engine.core import Component


class RigidBody(Component):
    """
    Componente de física 2D: gravidade, velocidade e movimento
    ao Transform do GameObject a cada frame.
    FIX: gravidade aplicada diretamente na velocidade (não via acceleration)
    para evitar vazamento quando forças externas e gravidade dividiam o mesmo array.

    Adicionado: atributo `grounded` para integração com TilemapCollider.

    FIX (jul/2026): GRAVITY movida para constante de classe — era atributo de
    instância mutável em __init__, o que tornava impossível alterar o valor
    globalmente sem criar um novo RigidBody.
    Para sobrescrever pontualmente: rb.GRAVITY = 500.0 (continua funcionando
    por herança de atributo de instância sobre o de classe).
    Para alterar globalmente: RigidBody.GRAVITY = 500.0
    """

    # Constante de classe — valor padrão da gravidade em pixels/s²
    GRAVITY: float = 980.0
    UNIQUE = True
    BODY_TYPES: tuple[str, ...] = ("dynamic", "kinematic", "static")

    def __init__(
        self,
        mass: float = 1.0,
        gravity_scale: float = 1.0,
        drag: float = 0.0,
        use_gravity: bool = True,
        is_kinematic: bool = False,
        body_type: str = "dynamic",
    ) -> None:
        super().__init__()
        self.mass:          float = max(mass, 0.0001)
        self.gravity_scale: float = gravity_scale
        self.drag:          float = drag
        self.use_gravity:   bool  = use_gravity
        self.is_kinematic:  bool  = is_kinematic

        if body_type != "dynamic" or is_kinematic:
            self.body_type = body_type if body_type != "dynamic" else ("kinematic" if is_kinematic else "dynamic")
        else:
            self._body_type = "dynamic"

        self.velocity:     np.ndarray = np.zeros(2, dtype=np.float32)
        # acceleration stores only EXTERNAL forces (not gravity)
        self.acceleration: np.ndarray = np.zeros(2, dtype=np.float32)

        # Flag definida pelo TilemapCollider a cada frame
        self.grounded: bool = False

    @property
    def body_type(self) -> str:
        if getattr(self, "_body_type", None) in self.BODY_TYPES:
            return self._body_type
        return "kinematic" if self.is_kinematic else "dynamic"

    @body_type.setter
    def body_type(self, val: str) -> None:
        val_str = str(val).lower().strip()
        if val_str not in self.BODY_TYPES:
            val_str = "dynamic"
        self._body_type = val_str
        if val_str == "kinematic":
            self.is_kinematic = True
        elif val_str == "static":
            self.is_kinematic = True
            self.use_gravity = False
        else:
            self.is_kinematic = False

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

        # Reset external forces (gravity is NOT here — it's in velocity directly)
        self.acceleration[:] = 0.0

    def serialize_properties(self) -> dict:
        return {
            "body_type": str(self.body_type),
            "mass": float(self.mass),
            "gravity_scale": float(self.gravity_scale),
            "drag": float(self.drag),
            "use_gravity": bool(self.use_gravity),
            "is_kinematic": bool(self.is_kinematic),
            "velocity": self.velocity.tolist(),
            "acceleration": self.acceleration.tolist(),
        }

    def deserialize_properties(self, data: dict) -> None:
        self.mass = float(data.get("mass", self.mass))
        self.gravity_scale = float(data.get("gravity_scale", self.gravity_scale))
        self.drag = float(data.get("drag", self.drag))
        self.use_gravity = bool(data.get("use_gravity", self.use_gravity))
        self.is_kinematic = bool(data.get("is_kinematic", self.is_kinematic))
        if "body_type" in data:
            self.body_type = str(data["body_type"])
        if "velocity" in data:
            self.velocity = np.array(data["velocity"], dtype=np.float32)
        if "acceleration" in data:
            self.acceleration = np.array(data["acceleration"], dtype=np.float32)
