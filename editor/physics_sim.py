"""
PhysicsSim — Simulação física 3D para o modo Play do editor.

Integra com RigidBody3D quando o objeto já tem o componente.
Para objetos sem RigidBody3D, usa simulação fallback inline.
Assim o editor é compatível tanto com objetos simples quanto
com objetos que usam o sistema ECS da engine.
"""
from __future__ import annotations
from typing import List, TYPE_CHECKING
import numpy as np

if TYPE_CHECKING:
    from engine.game_object import GameObject


class PhysicsSim:
    GRAVITY: float     = 9.8
    FLOOR_Y: float     = -0.5
    RESTITUTION: float = 0.4
    FRICTION: float    = 0.88
    OBJ_E: float       = 0.5

    @staticmethod
    def attach_rigidbody(obj: "GameObject") -> None:
        """
        Garante que o objeto tenha RigidBody3D antes do Play.
        Se já tiver, só reseta a velocidade.
        """
        from engine.physics.rigidbody3d import RigidBody3D
        rb = obj.get_component(RigidBody3D)
        if rb is None:
            rb = obj.add_component(RigidBody3D(
                use_gravity=getattr(obj, "use_physics", True),
                is_kinematic=getattr(obj, "is_static", False),
            ))
        vy = getattr(obj, "initial_velocity_y", 0.0)
        rb.velocity = np.array([0.0, vy, 0.0], dtype=np.float32)
        rb.use_gravity   = getattr(obj, "use_physics", True)
        rb.is_kinematic  = getattr(obj, "is_static", False)

    @staticmethod
    def detach_rigidbody(obj: "GameObject") -> None:
        """Remove o RigidBody3D ao sair do Play."""
        from engine.physics.rigidbody3d import RigidBody3D
        rb = obj.get_component(RigidBody3D)
        if rb is not None:
            obj.components.remove(rb)

    @staticmethod
    def step(objects: List["GameObject"], dt: float) -> None:
        """
        Avança a simulação um passo.
        Prioriza RigidBody3D; usa fallback para objetos sem o componente.
        """
        from engine.physics.rigidbody3d import RigidBody3D
        dt = min(dt, 0.05)

        # Integração via RigidBody3D (delega para o componente)
        for obj in objects:
            rb = obj.get_component(RigidBody3D)
            if rb:
                rb.update(dt)
            else:
                # Fallback inline para objetos sem RigidBody3D
                if getattr(obj, "is_static", False):
                    continue
                if not hasattr(obj, "_phys_vel"):
                    obj._phys_vel = np.zeros(3, dtype=np.float32)
                    obj._phys_vel[1] = getattr(obj, "initial_velocity_y", 0.0)
                if getattr(obj, "use_physics", True):
                    obj._phys_vel[1] -= PhysicsSim.GRAVITY * dt
                obj.transform.position += obj._phys_vel * dt
                half = obj.transform.scale[1] * 0.5
                if obj.transform.position[1] - half < PhysicsSim.FLOOR_Y:
                    obj.transform.position[1] = PhysicsSim.FLOOR_Y + half
                    obj._phys_vel[1]  = -obj._phys_vel[1] * PhysicsSim.RESTITUTION
                    obj._phys_vel[0] *= PhysicsSim.FRICTION
                    obj._phys_vel[2] *= PhysicsSim.FRICTION

        # Colisões objeto-objeto (esferas aproximadas)
        n = len(objects)
        for i in range(n):
            for j in range(i + 1, n):
                a, b = objects[i], objects[j]
                sa = getattr(a, "is_static", False)
                sb = getattr(b, "is_static", False)
                if sa and sb:
                    continue
                r_a = np.mean(a.transform.scale) * 0.5
                r_b = np.mean(b.transform.scale) * 0.5
                diff = a.transform.position - b.transform.position
                dist = float(np.linalg.norm(diff))
                if dist >= r_a + r_b:
                    continue
                normal  = diff / max(dist, 1e-5)
                overlap = (r_a + r_b) - dist
                e = PhysicsSim.OBJ_E

                from engine.physics.rigidbody3d import RigidBody3D
                rb_a = a.get_component(RigidBody3D)
                rb_b = b.get_component(RigidBody3D)
                v_a = rb_a.velocity if rb_a else getattr(a, "_phys_vel", np.zeros(3, np.float32))
                v_b = rb_b.velocity if rb_b else getattr(b, "_phys_vel", np.zeros(3, np.float32))

                if sa:
                    b.transform.position -= normal * overlap
                    vbn = float(np.dot(v_b, normal))
                    if vbn > 0:
                        v_b -= normal * (1 + e) * vbn
                elif sb:
                    a.transform.position += normal * overlap
                    van = float(np.dot(v_a, normal))
                    if van < 0:
                        v_a -= normal * (1 + e) * van
                else:
                    a.transform.position += normal * (overlap * 0.5)
                    b.transform.position -= normal * (overlap * 0.5)
                    rel = v_a - v_b
                    van = float(np.dot(rel, normal))
                    if van < 0:
                        imp = -(1 + e) * van / 2.0
                        v_a += normal * imp
                        v_b -= normal * imp
