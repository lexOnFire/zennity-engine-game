"""
PhysicsSim — Simulação física 3D para o modo Play do editor.
"""
from __future__ import annotations
from typing import List, TYPE_CHECKING
import numpy as np

if TYPE_CHECKING:
    from engine.game_object import GameObject


def _half_extents(obj: "GameObject") -> np.ndarray:
    """Retorna os semi-eixos (half-extents) AABB do objeto respeitando o scale real."""
    return obj.transform.scale * 0.5


def _aabb_overlap(pos_a, he_a, pos_b, he_b):
    """
    Retorna (overlapping, penetration_vector) para dois AABBs.
    penetration_vector aponta de b para a, com magnitude da menor penetração.
    """
    diff = pos_a - pos_b
    sum_he = he_a + he_b
    pen = sum_he - np.abs(diff)
    if np.any(pen <= 0):
        return False, None
    axis = int(np.argmin(pen))
    normal = np.zeros(3, dtype=np.float32)
    normal[axis] = np.sign(diff[axis]) if diff[axis] != 0 else 1.0
    return True, (normal, pen[axis])


class PhysicsSim:
    GRAVITY:     float = 9.8
    FLOOR_Y:     float = -0.5
    RESTITUTION: float = 0.4
    FRICTION:    float = 0.88
    OBJ_E:       float = 0.5

    @staticmethod
    def attach_rigidbody(obj: "GameObject") -> None:
        from engine.physics.rigidbody3d import RigidBody3D
        # Remove RigidBody3D antigo se existir (evita duplicatas entre Play/Stop/Play)
        old_rb = obj.get_component(RigidBody3D)
        if old_rb is not None:
            try:
                obj.components.remove(old_rb)
            except ValueError:
                pass

        vy = float(getattr(obj, "initial_velocity_y", 0.0))
        rb = obj.add_component(RigidBody3D(
            use_gravity=getattr(obj, "use_physics", True),
            is_kinematic=getattr(obj, "is_static", False),
        ))
        rb.velocity     = np.array([0.0, vy, 0.0], dtype=np.float32)
        rb.use_gravity  = getattr(obj, "use_physics", True)
        rb.is_kinematic = getattr(obj, "is_static", False)
        # _phys_vel: fallback caso RigidBody3D não esteja disponível no step
        obj._phys_vel   = np.array([0.0, vy, 0.0], dtype=np.float32)

    @staticmethod
    def detach_rigidbody(obj: "GameObject") -> None:
        from engine.physics.rigidbody3d import RigidBody3D
        rb = obj.get_component(RigidBody3D)
        if rb is not None:
            try:
                obj.components.remove(rb)
            except ValueError:
                pass
        # Remove o atributo de vel fallback para não sujar o estado do editor
        if hasattr(obj, "_phys_vel"):
            try:
                delattr(obj, "_phys_vel")
            except AttributeError:
                pass

    @staticmethod
    def clear_registries() -> None:
        """Limpa registries de colliders (seguro mesmo se as classes não existirem)."""
        for cls_path in (
            ("engine.physics.collider", "BoxCollider"),
            ("engine.physics.collider", "CircleCollider"),
            ("engine.physics.collider", "SphereCollider"),
        ):
            try:
                import importlib
                mod = importlib.import_module(cls_path[0])
                cls = getattr(mod, cls_path[1], None)
                if cls and hasattr(cls, "_registry"):
                    cls._registry.clear()
            except Exception:
                pass

    @staticmethod
    def step(objects: List["GameObject"], dt: float) -> None:
        from engine.physics.rigidbody3d import RigidBody3D
        dt = min(dt, 0.05)

        # --- Integração de velocidade / gravidade ---
        for obj in objects:
            rb = obj.get_component(RigidBody3D)
            if rb:
                try:
                    rb.update(dt)
                except Exception as e:
                    print(f"[PhysicsSim] rb.update erro em '{obj.name}': {e}")
            else:
                if getattr(obj, "is_static", False):
                    continue
                if not hasattr(obj, "_phys_vel"):
                    vy = float(getattr(obj, "initial_velocity_y", 0.0))
                    obj._phys_vel = np.array([0.0, vy, 0.0], dtype=np.float32)
                if getattr(obj, "use_physics", True):
                    obj._phys_vel[1] -= PhysicsSim.GRAVITY * dt
                obj.transform.position += obj._phys_vel * dt
                half_y = obj.transform.scale[1] * 0.5
                if obj.transform.position[1] - half_y < PhysicsSim.FLOOR_Y:
                    obj.transform.position[1] = PhysicsSim.FLOOR_Y + half_y
                    obj._phys_vel[1]  = -obj._phys_vel[1] * PhysicsSim.RESTITUTION
                    obj._phys_vel[0] *= PhysicsSim.FRICTION
                    obj._phys_vel[2] *= PhysicsSim.FRICTION

        # --- Colisões objeto-objeto com AABB ---
        n = len(objects)
        for i in range(n):
            for j in range(i + 1, n):
                a, b = objects[i], objects[j]
                sa = getattr(a, "is_static", False)
                sb = getattr(b, "is_static", False)
                if sa and sb:
                    continue

                he_a = _half_extents(a)
                he_b = _half_extents(b)
                overlapping, result = _aabb_overlap(
                    a.transform.position, he_a,
                    b.transform.position, he_b,
                )
                if not overlapping:
                    continue

                normal, penetration = result
                e = PhysicsSim.OBJ_E

                rb_a = a.get_component(RigidBody3D)
                rb_b = b.get_component(RigidBody3D)

                v_a = (rb_a.velocity.copy() if rb_a else
                       (a._phys_vel.copy() if hasattr(a, "_phys_vel") else np.zeros(3, np.float32)))
                v_b = (rb_b.velocity.copy() if rb_b else
                       (b._phys_vel.copy() if hasattr(b, "_phys_vel") else np.zeros(3, np.float32)))

                if sa:
                    b.transform.position -= normal * penetration
                    vbn = float(np.dot(v_b, normal))
                    if vbn > 0:
                        v_b -= normal * (1 + e) * vbn
                elif sb:
                    a.transform.position += normal * penetration
                    van = float(np.dot(v_a, normal))
                    if van < 0:
                        v_a -= normal * (1 + e) * van
                else:
                    a.transform.position += normal * (penetration * 0.5)
                    b.transform.position -= normal * (penetration * 0.5)
                    rel = v_a - v_b
                    van = float(np.dot(rel, normal))
                    if van < 0:
                        imp = -(1 + e) * van / 2.0
                        v_a += normal * imp
                        v_b -= normal * imp

                if rb_a:
                    rb_a.velocity[:] = v_a
                elif hasattr(a, "_phys_vel"):
                    a._phys_vel[:] = v_a
                if rb_b:
                    rb_b.velocity[:] = v_b
                elif hasattr(b, "_phys_vel"):
                    b._phys_vel[:] = v_b
