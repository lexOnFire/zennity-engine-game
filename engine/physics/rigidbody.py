from ..component import Component
from .collision import BoxCollider2D
import numpy as np

class Rigidbody2D(Component):
    """Component that simulates simple gravity, velocity, and AABB collision resolution in 2D."""
    def __init__(self, gravity: float = 980.0, use_gravity: bool = True) -> None:
        super().__init__()
        self.velocity = np.array([0.0, 0.0], dtype=np.float32)  # [vx, vy]
        self.gravity = gravity
        self.use_gravity = use_gravity
        self.is_grounded = False
        
        self._collider = None

    def start(self) -> None:
        self._collider = self.game_object.get_component(BoxCollider2D)

    def update(self, dt: float) -> None:
        # Apply gravity
        if self.use_gravity and not self.is_grounded:
            self.velocity[1] += self.gravity * dt

        # Move X axis first and check collisions
        self.transform.x += self.velocity[0] * dt
        self._resolve_collisions_axis(axis=0)

        # Move Y axis and check collisions
        self.is_grounded = False
        self.transform.y += self.velocity[1] * dt
        self._resolve_collisions_axis(axis=1)

    def _resolve_collisions_axis(self, axis: int) -> None:
        """Resolves collisions on the specified axis (0 for X, 1 for Y)."""
        if not self._collider:
            self._collider = self.game_object.get_component(BoxCollider2D)
            if not self._collider:
                return

        for other in BoxCollider2D.all_colliders:
            # Skip self and triggers
            if other == self._collider or other.is_trigger:
                continue
                
            if self._collider.check_collision(other):
                overlap_x, overlap_y = self._collider.get_overlap(other)
                
                if axis == 0:  # X axis resolution
                    if abs(overlap_x) > 0:
                        self.transform.x += overlap_x
                        self.velocity[0] = 0.0
                else:  # Y axis resolution
                    if abs(overlap_y) > 0:
                        self.transform.y += overlap_y
                        
                        # In Pygame screen space, Y increases downwards.
                        # If overlap_y is negative, we were pushed up (hitting the ground).
                        # If overlap_y is positive, we were pushed down (hitting the ceiling).
                        if overlap_y < 0.0:
                            self.is_grounded = True
                            if self.velocity[1] > 0.0:
                                self.velocity[1] = 0.0
                        elif overlap_y > 0.0:
                            if self.velocity[1] < 0.0:
                                self.velocity[1] = 0.0
