from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from engine.physics.collider import BoxCollider, CircleCollider
from engine.physics.rigidbody import RigidBody
from engine.time import Time


@dataclass(frozen=True)
class PhysicsContact:
    a: Any
    b: Any
    is_trigger: bool = False


class PhysicsWorld:
    """Runtime-only physics registry and collision detection world."""

    def __init__(self, runtime_scene: Any | None = None) -> None:
        self.runtime_scene = runtime_scene
        self.rigidbodies: list[RigidBody] = []
        self.colliders: list[Any] = []
        self.contacts: set[tuple[int, int]] = set()
        self.trigger_contacts: set[tuple[int, int]] = set()
        self.detected_contacts: list[PhysicsContact] = []

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
            if self._component_active(body):
                body.integrate(dt)
        self.detect_collisions()

    def detect_collisions(self) -> list[PhysicsContact]:
        next_contacts: set[tuple[int, int]] = set()
        next_triggers: set[tuple[int, int]] = set()
        self.detected_contacts = []

        colliders = [c for c in self.colliders if self._component_active(c)]
        for index, a in enumerate(colliders):
            for b in colliders[index + 1 :]:
                if not self._same_scene(a, b):
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
                    self._resolve_collision(a, b)
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

    def _resolve_collision(self, a: Any, b: Any) -> None:
        a_type = self._collider_type(a)
        b_type = self._collider_type(b)
        if a_type == "BoxCollider" and b_type == "BoxCollider":
            rect_a = a.rect
            rect_b = b.rect
            overlap_x = min(rect_a.right, rect_b.right) - max(rect_a.left, rect_b.left)
            overlap_y = min(rect_a.bottom, rect_b.bottom) - max(rect_a.top, rect_b.top)
            if overlap_x > 0 and overlap_y > 0:
                BoxCollider._resolve(a, b, overlap_x, overlap_y)
            return

        if a_type == "CircleCollider" and b_type == "CircleCollider":
            ax, ay = a.center
            bx, by = b.center
            dist = math.hypot(bx - ax, by - ay)
            min_dist = a.radius + b.radius
            if dist < min_dist:
                CircleCollider._resolve(a, b, ax, ay, bx, by, dist, min_dist)

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
