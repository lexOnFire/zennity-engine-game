"""Fixed-step gravity integration for isolated Play Mode."""
from __future__ import annotations

from typing import Any


class ViewportPhysicsStepper:
    def __init__(self, gravity: float = 980.0) -> None:
        self.gravity = float(gravity)

    def step(
        self, objects: dict[str, dict[str, Any]], velocities_y: dict[str, float],
        grounded: dict[str, bool], motion_axes: dict[str, set[str]],
        steps: int, fixed_dt: float,
    ) -> None:
        for _ in range(max(0, int(steps))):
            static = [obj for obj in objects.values() if obj.get("active", True) and obj.get("collider")
                      and not obj["collider"].get("is_trigger", False)
                      and (obj.get("rigidbody") or {}).get("is_kinematic", True)]
            for name, obj in list(objects.items()):
                rigidbody = obj.get("rigidbody") or {}
                if not obj.get("active", True) or rigidbody.get("is_kinematic", False) or not rigidbody.get("use_gravity", False):
                    continue
                if "y" in motion_axes.get(name, set()):
                    velocities_y[name] = 0.0
                    continue
                grounded[name] = False
                velocity = velocities_y.get(name, 0.0) + self.gravity * float(rigidbody.get("gravity_scale", 1.0)) * fixed_dt
                previous_bottom = obj["y"] + obj["h"] / 2
                obj["y"] += velocity * fixed_dt
                for floor in static:
                    if floor is obj:
                        continue
                    overlaps_x = abs(obj["x"] - floor["x"]) * 2 < obj["w"] + floor["w"]
                    floor_top = floor["y"] - floor["h"] / 2
                    bottom = obj["y"] + obj["h"] / 2
                    if overlaps_x and previous_bottom <= floor_top and bottom >= floor_top:
                        obj["y"] = floor_top - obj["h"] / 2
                        velocity = 0.0
                        grounded[name] = True
                        break
                velocities_y[name] = velocity
                obj["_grounded"] = bool(grounded.get(name, False))
