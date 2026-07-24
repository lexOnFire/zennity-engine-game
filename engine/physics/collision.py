from engine.physics.collider import BoxCollider
from ..component import Component
from typing import Tuple, List, Optional
import numpy as np


class BoxCollider2D(BoxCollider):
    """2D Axis-Aligned Bounding Box (AABB) Collider (Subclasse de BoxCollider para compatibilidade)."""
    all_colliders: List['BoxCollider2D'] = []

    def __init__(self, width: float = 32.0, height: float = 32.0,
                 offset_x: float = 0.0, offset_y: float = 0.0,
                 is_trigger: bool = False) -> None:
        super().__init__(width, height, offset_x, offset_y, is_trigger)

    def start(self) -> None:
        super().start()
        if self not in BoxCollider2D.all_colliders:
            BoxCollider2D.all_colliders.append(self)

    def destroy(self) -> None:
        super().destroy()
        if self in BoxCollider2D.all_colliders:
            BoxCollider2D.all_colliders.remove(self)

    def get_bounds(self) -> Tuple[float, float, float, float]:
        """Returns bounds as (left, right, top, bottom) in world coordinates."""
        world_pos = self.transform.get_world_position()
        cx = world_pos[0] + self.offset_x
        cy = world_pos[1] + self.offset_y

        half_w = (self.width * abs(self.transform.sx)) / 2.0
        half_h = (self.height * abs(self.transform.sy)) / 2.0

        return (cx - half_w, cx + half_w, cy - half_h, cy + half_h)

    def check_collision(self, other: 'BoxCollider2D') -> bool:
        """Returns True if this collider intersects with another."""
        l1, r1, t1, b1 = self.get_bounds()
        l2, r2, t2, b2 = other.get_bounds()

        return not (r1 <= l2 or l1 >= r2 or b1 <= t2 or t1 >= b2)

    def get_overlap(self, other: 'BoxCollider2D') -> Tuple[float, float]:
        """Calculates the overlap vector on X and Y axes if colliding."""
        l1, r1, t1, b1 = self.get_bounds()
        l2, r2, t2, b2 = other.get_bounds()

        overlap_x = 0.0
        overlap_y = 0.0

        if r1 > l2 and l1 < r2:
            overlap_x = min(r1 - l2, r2 - l1)
            if (r1 - l2) < (r2 - l1):
                overlap_x = -overlap_x

        if b1 > t2 and t1 < b2:
            overlap_y = min(b1 - t2, b2 - t1)
            if (b1 - t2) < (b2 - t1):
                overlap_y = -overlap_y

        return overlap_x, overlap_y


def check_collision(a: BoxCollider2D, b: BoxCollider2D) -> bool:
    """Module-level helper: returns True if colliders a and b intersect."""
    return a.check_collision(b)
