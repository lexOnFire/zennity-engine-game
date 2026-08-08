from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from engine.physics.collider import BoxCollider, CircleCollider
from engine.physics.rigidbody import RigidBody
from engine.physics.spatial_hash import BroadPhaseStats, SpatialHashBroadPhase
from engine.physics.collision_layers import can_collide
from engine.time import Time


@dataclass(frozen=True)
class PhysicsContact:
    a: Any
    b: Any
    is_trigger: bool = False


@dataclass(frozen=True)
class RaycastHit:
    """Result of a raycast query."""
    hit_object: Any  # GameObject that was hit
    hit_point: tuple[float, float]  # (x, y) world position of hit
    hit_distance: float  # Distance from ray origin to hit point
    hit_normal: tuple[float, float]  # Surface normal at hit point
    collider: Any  # Collider component that was hit


class PhysicsWorld:
    """Runtime-only physics registry and collision detection world."""

    def __init__(self, runtime_scene: Any | None = None, broad_phase_cell_size: float = 128.0) -> None:
        self.runtime_scene = runtime_scene
        self.rigidbodies: list[RigidBody] = []
        self.colliders: list[Any] = []
        self.contacts: set[tuple[int, int]] = set()
        self.trigger_contacts: set[tuple[int, int]] = set()
        self.detected_contacts: list[PhysicsContact] = []
        self.broad_phase = SpatialHashBroadPhase(cell_size=broad_phase_cell_size)
        self.broad_phase_stats = BroadPhaseStats()

    def register_rigidbody(self, body: RigidBody) -> None:
        if body not in self.rigidbodies:
            self.rigidbodies.append(body)
            body._runtime_physics_managed = True

    def unregister_rigidbody(self, body: RigidBody) -> None:
        if body in self.rigidbodies:
            self.rigidbodies.remove(body)
        if getattr(body, "_runtime_physics_managed", False):
            body._runtime_physics_managed = False

    def register_collider(self, collider: Any) -> None:
        if self._is_supported_collider(collider) and collider not in self.colliders:
            self.colliders.append(collider)

    def unregister_collider(self, collider: Any) -> None:
        if collider in self.colliders:
            self.colliders.remove(collider)
        self.contacts = {pair for pair in self.contacts if id(collider) not in pair}
        self.trigger_contacts = {pair for pair in self.trigger_contacts if id(collider) not in pair}

    def build_from_scene(self, runtime_scene: Any) -> None:
        self.clear()
        for obj in self._iter_objects(runtime_scene):
            if not bool(getattr(obj, "active", True)):
                continue
            for component in getattr(obj, "components", []):
                if not bool(getattr(component, "enabled", True)):
                    continue
                if isinstance(component, RigidBody):
                    self.register_rigidbody(component)
                elif self._is_supported_collider(component):
                    self.register_collider(component)

    def step(self, delta_time: float | None = None) -> None:
        dt = Time.fixed_delta_time if delta_time is None else float(delta_time)

        for body in list(self.rigidbodies):
            if not self._component_active(body):
                continue

            integrate = getattr(body, "integrate", None)
            if callable(integrate):
                integrate(dt)
                continue

            update = getattr(body, "update", None)
            if callable(update):
                update(dt)

        self.detect_collisions()

    def detect_collisions(self) -> list[PhysicsContact]:
        next_contacts: set[tuple[int, int]] = set()
        next_triggers: set[tuple[int, int]] = set()
        self.detected_contacts = []

        colliders = [c for c in self.colliders if self._component_active(c)]
        candidates = self.broad_phase.candidate_pairs(
            colliders,
            bounds_for=self._collider_bounds,
            scene_for=lambda collider: getattr(getattr(collider, "game_object", None), "scene", None),
        )
        self.broad_phase_stats = self.broad_phase.stats
        for a, b in candidates:
            if not self._same_scene(a, b):
                continue
            # Phase 5B.4: Layer/mask collision filtering
            a_layer = getattr(a, "collision_layer", 1)
            a_mask = getattr(a, "collision_mask", 0xFFFFFFFF)
            b_layer = getattr(b, "collision_layer", 1)
            b_mask = getattr(b, "collision_mask", 0xFFFFFFFF)
            if not can_collide(a_layer, a_mask, b_layer, b_mask):
                continue
            if not self._intersects(a, b):
                continue
            pair = self._pair_key(a, b)
            is_trigger = bool(getattr(a, "is_trigger", False) or getattr(b, "is_trigger", False))
            self.detected_contacts.append(PhysicsContact(a, b, is_trigger))
            if is_trigger:
                next_triggers.add(pair)
                if pair not in self.trigger_contacts:
                    self._emit_trigger_enter(a, b)
            else:
                next_contacts.add(pair)
                if pair not in self.contacts:
                    self._emit_collision_enter(a, b)

        for pair in self.trigger_contacts - next_triggers:
            a, b = self._pair_from_key(pair)
            if a is not None and b is not None:
                self._emit_trigger_exit(a, b)
        for pair in self.contacts - next_contacts:
            a, b = self._pair_from_key(pair)
            if a is not None and b is not None:
                self._emit_collision_exit(a, b)

        self.trigger_contacts = next_triggers
        self.contacts = next_contacts
        return list(self.detected_contacts)

    def raycast(
        self,
        origin: tuple[float, float],
        direction: tuple[float, float],
        max_distance: float = float('inf'),
        ignore_self: str | None = None,
        include_triggers: bool = False,
        layer_mask: int = 0xFFFFFFFF,
    ) -> RaycastHit | None:
        """
        Cast a ray and return the nearest hit.

        Args:
            origin: Ray start position (x, y)
            direction: Ray direction vector (normalized or not)
            max_distance: Maximum distance to test (default: infinity)
            ignore_self: Object name to ignore (usually ray origin object)
            include_triggers: Whether to hit trigger colliders
            layer_mask: Bitmask of layers to accept (Phase 5B.4)

        Returns:
            RaycastHit if hit, None otherwise
        """
        ox, oy = float(origin[0]), float(origin[1])
        dx, dy = float(direction[0]), float(direction[1])

        # Normalize direction or handle zero direction
        dir_len = math.hypot(dx, dy)
        if dir_len < 1e-6:
            return None
        dx, dy = dx / dir_len, dy / dir_len

        closest_hit: RaycastHit | None = None
        closest_distance = float(max_distance)

        for collider in self.colliders:
            if not self._component_active(collider):
                continue
            if not include_triggers and bool(getattr(collider, "is_trigger", False)):
                continue

            # Phase 5B.4: Layer mask filtering for raycast queries
            collider_layer = getattr(collider, "collision_layer", 1)
            if (layer_mask & collider_layer) == 0:
                continue

            obj = getattr(collider, "game_object", None)
            if obj is not None and ignore_self is not None:
                if str(getattr(obj, "name", "")) == ignore_self:
                    continue

            hit = self._ray_collider_intersection(
                ox, oy, dx, dy, closest_distance, collider
            )
            if hit is not None and hit.hit_distance < closest_distance:
                closest_hit = hit
                closest_distance = hit.hit_distance

        return closest_hit

    def _ray_collider_intersection(
        self,
        ox: float, oy: float,
        dx: float, dy: float,
        max_dist: float,
        collider: Any,
    ) -> RaycastHit | None:
        """Test ray vs collider intersection."""
        collider_type = self._collider_type(collider)

        if collider_type == "BoxCollider":
            return self._ray_box_intersection(ox, oy, dx, dy, max_dist, collider)
        elif collider_type == "CircleCollider":
            return self._ray_circle_intersection(ox, oy, dx, dy, max_dist, collider)

        return None

    def _ray_box_intersection(
        self,
        ox: float, oy: float,
        dx: float, dy: float,
        max_dist: float,
        box: Any,
    ) -> RaycastHit | None:
        """Ray vs AABB intersection using slab method."""
        rect = box.rect
        left, top, right, bottom = rect.left, rect.top, rect.right, rect.bottom

        t_min, t_max = 0.0, max_dist

        # X slab
        if abs(dx) > 1e-6:
            t1 = (left - ox) / dx
            t2 = (right - ox) / dx
            if t1 > t2:
                t1, t2 = t2, t1
            t_min = max(t_min, t1)
            t_max = min(t_max, t2)
        else:
            if not (left <= ox <= right):
                return None

        # Y slab
        if abs(dy) > 1e-6:
            t1 = (top - oy) / dy
            t2 = (bottom - oy) / dy
            if t1 > t2:
                t1, t2 = t2, t1
            t_min = max(t_min, t1)
            t_max = min(t_max, t2)
        else:
            if not (top <= oy <= bottom):
                return None

        if t_min < 0 or t_min > t_max or t_min > max_dist:
            return None

        # Hit point and normal
        hit_dist = max(0.0, t_min)
        hit_x = ox + dx * hit_dist
        hit_y = oy + dy * hit_dist

        # Determine normal
        normal = self._box_hit_normal(hit_x, hit_y, left, top, right, bottom)

        obj = getattr(box, "game_object", None)
        return RaycastHit(
            hit_object=obj,
            hit_point=(hit_x, hit_y),
            hit_distance=hit_dist,
            hit_normal=normal,
            collider=box,
        )

    def _ray_circle_intersection(
        self,
        ox: float, oy: float,
        dx: float, dy: float,
        max_dist: float,
        circle: Any,
    ) -> RaycastHit | None:
        """Ray vs circle intersection using quadratic formula."""
        cx, cy = circle.center
        r = float(circle.radius)

        # Ray: P(t) = O + t*D
        # Circle: |P - C|² = r²
        # Substitute: |O + t*D - C|² = r²
        # Expand: t²|D|² + 2t(O-C)·D + |O-C|² - r² = 0

        oc_x = ox - cx
        oc_y = oy - cy

        a = dx * dx + dy * dy
        b = 2 * (oc_x * dx + oc_y * dy)
        c = oc_x * oc_x + oc_y * oc_y - r * r

        discriminant = b * b - 4 * a * c

        if discriminant < 0:
            return None

        sqrt_disc = math.sqrt(discriminant)
        t1 = (-b - sqrt_disc) / (2 * a)
        t2 = (-b + sqrt_disc) / (2 * a)

        t = None
        if t1 >= 0 and t1 <= max_dist:
            t = t1
        elif t2 >= 0 and t2 <= max_dist:
            t = t2

        if t is None:
            return None

        hit_x = ox + dx * t
        hit_y = oy + dy * t

        # Normal at hit point
        norm_x = hit_x - cx
        norm_y = hit_y - cy
        norm_len = math.hypot(norm_x, norm_y)
        if norm_len > 1e-6:
            norm_x /= norm_len
            norm_y /= norm_len

        obj = getattr(circle, "game_object", None)
        return RaycastHit(
            hit_object=obj,
            hit_point=(hit_x, hit_y),
            hit_distance=t,
            hit_normal=(norm_x, norm_y),
            collider=circle,
        )

    @staticmethod
    def _box_hit_normal(
        hit_x: float, hit_y: float,
        left: float, top: float,
        right: float, bottom: float,
    ) -> tuple[float, float]:
        """Determine surface normal at box hit point."""
        # Distance to each edge
        d_left = abs(hit_x - left)
        d_right = abs(hit_x - right)
        d_top = abs(hit_y - top)
        d_bottom = abs(hit_y - bottom)

        min_dist = min(d_left, d_right, d_top, d_bottom)

        if min_dist == d_left:
            return (-1.0, 0.0)
        elif min_dist == d_right:
            return (1.0, 0.0)
        elif min_dist == d_top:
            return (0.0, -1.0)
        else:
            return (0.0, 1.0)

    def clear(self) -> None:
        for body in list(self.rigidbodies):
            if getattr(body, "_runtime_physics_managed", False):
                body._runtime_physics_managed = False
        self.rigidbodies.clear()
        self.colliders.clear()
        self.contacts.clear()
        self.trigger_contacts.clear()
        self.detected_contacts.clear()

    def _iter_objects(self, runtime_scene: Any) -> list[Any]:
        roots = getattr(runtime_scene, "editable_objects", None)
        if roots is None:
            roots = getattr(runtime_scene, "game_objects", [])
        ordered: list[Any] = []

        def visit(obj: Any) -> None:
            ordered.append(obj)
            for child in getattr(obj, "children", []):
                visit(child)

        for obj in list(roots):
            visit(obj)
        return ordered

    def _component_active(self, component: Any) -> bool:
        obj = getattr(component, "game_object", None)
        return (
            obj is not None
            and bool(getattr(obj, "active", True))
            and bool(getattr(component, "enabled", True))
        )

    def _same_scene(self, a: Any, b: Any) -> bool:
        obj_a = getattr(a, "game_object", None)
        obj_b = getattr(b, "game_object", None)
        return obj_a is not None and obj_b is not None and getattr(obj_a, "scene", None) is getattr(obj_b, "scene", None)

    def _intersects(self, a: Any, b: Any) -> bool:
        a_type = self._collider_type(a)
        b_type = self._collider_type(b)
        if a_type == "BoxCollider" and b_type == "BoxCollider":
            return a.rect.colliderect(b.rect)
        if a_type == "CircleCollider" and b_type == "CircleCollider":
            ax, ay = a.center
            bx, by = b.center
            return math.hypot(bx - ax, by - ay) < (a.radius + b.radius)
        if a_type == "BoxCollider" and b_type == "CircleCollider":
            return self._box_circle_intersects(a, b)
        if a_type == "CircleCollider" and b_type == "BoxCollider":
            return self._box_circle_intersects(b, a)
        return False

    def _collider_bounds(self, collider: Any) -> tuple[float, float, float, float]:
        if self._collider_type(collider) == "BoxCollider":
            rect = collider.rect
            return float(rect.left), float(rect.top), float(rect.right), float(rect.bottom)
        center_x, center_y = collider.center
        radius = float(collider.radius)
        return center_x - radius, center_y - radius, center_x + radius, center_y + radius

    def _is_supported_collider(self, collider: Any) -> bool:
        return self._collider_type(collider) in {"BoxCollider", "CircleCollider"}

    def _collider_type(self, collider: Any) -> str:
        return str(getattr(collider, "type_name", getattr(collider, "component_type", type(collider).__name__)))

    def _box_circle_intersects(self, box: BoxCollider, circle: CircleCollider) -> bool:
        rect = box.rect
        cx, cy = circle.center
        closest_x = max(rect.left, min(cx, rect.right))
        closest_y = max(rect.top, min(cy, rect.bottom))
        return math.hypot(cx - closest_x, cy - closest_y) < circle.radius

    def _pair_key(self, a: Any, b: Any) -> tuple[int, int]:
        return tuple(sorted((id(a), id(b))))

    def _pair_from_key(self, pair: tuple[int, int]) -> tuple[Any | None, Any | None]:
        by_id = {id(collider): collider for collider in self.colliders}
        return by_id.get(pair[0]), by_id.get(pair[1])

    def _emit_collision_enter(self, a: Any, b: Any) -> None:
        callback_a = getattr(a, "on_collision_enter", None)
        callback_b = getattr(b, "on_collision_enter", None)
        if callback_a:
            callback_a(b)
        if callback_b:
            callback_b(a)
        self._notify_game_object(a, "on_collision_enter", b)
        self._notify_game_object(b, "on_collision_enter", a)

    def _emit_collision_exit(self, a: Any, b: Any) -> None:
        callback_a = getattr(a, "on_collision_exit", None)
        callback_b = getattr(b, "on_collision_exit", None)
        if callback_a:
            callback_a(b)
        if callback_b:
            callback_b(a)
        self._notify_game_object(a, "on_collision_exit", b)
        self._notify_game_object(b, "on_collision_exit", a)

    def _emit_trigger_enter(self, a: Any, b: Any) -> None:
        callback_a = getattr(a, "on_trigger_enter", None)
        callback_b = getattr(b, "on_trigger_enter", None)
        if callback_a:
            callback_a(b)
        if callback_b:
            callback_b(a)
        self._notify_game_object(a, "on_trigger_enter", b)
        self._notify_game_object(b, "on_trigger_enter", a)

    def _emit_trigger_exit(self, a: Any, b: Any) -> None:
        callback_a = getattr(a, "on_trigger_exit", None)
        callback_b = getattr(b, "on_trigger_exit", None)
        if callback_a:
            callback_a(b)
        if callback_b:
            callback_b(a)
        self._notify_game_object(a, "on_trigger_exit", b)
        self._notify_game_object(b, "on_trigger_exit", a)

    def _notify_game_object(self, collider: Any, method_name: str, other: Any) -> None:
        obj = getattr(collider, "game_object", None)
        if obj is None:
            return
        for component in getattr(obj, "components", []):
            method = getattr(component, method_name, None)
            if callable(method):
                method(other)
        script_runtime = getattr(self.runtime_scene, "script_runtime", None)
        if script_runtime is not None:
            script_runtime.notify_game_object_event(obj, method_name, other)
