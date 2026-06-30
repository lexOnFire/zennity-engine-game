"""Simulação física simples usada pelo modo Play do editor."""
from typing import List, TYPE_CHECKING
import numpy as np

if TYPE_CHECKING:
    from engine.game_object import GameObject


class PhysicsSim:
    """
    Simulação de física standalone para o editor.
    Independente do sistema engine/physics/ para não impactar o ECS.
    Aplica gravidade, colisão com chão e colisão esfera-esfera aproximada.
    """
    GRAVITY: float = 9.8
    FLOOR_Y: float = -0.5
    RESTITUTION: float = 0.4   # elasticidade chão
    FRICTION: float = 0.9      # fricção lateral
    OBJ_RESTITUTION: float = 0.5  # elasticidade obj-obj

    @staticmethod
    def step(objects: List["GameObject"], dt: float) -> None:
        dt = min(0.05, dt)

        # Integração
        for obj in objects:
            if getattr(obj, "is_static", False):
                continue
            if not hasattr(obj, "physics_velocity"):
                obj.physics_velocity = np.zeros(3, dtype=np.float32)
            if getattr(obj, "use_physics", True):
                obj.physics_velocity[1] -= PhysicsSim.GRAVITY * dt
            obj.transform.position += obj.physics_velocity * dt

        # Colisão com chão
        for obj in objects:
            if getattr(obj, "is_static", False):
                continue
            bottom = obj.transform.position[1] - obj.transform.scale[1] * 0.5
            if bottom < PhysicsSim.FLOOR_Y:
                obj.transform.position[1] = PhysicsSim.FLOOR_Y + obj.transform.scale[1] * 0.5
                v = getattr(obj, "physics_velocity", None)
                if v is not None:
                    v[1] = -v[1] * PhysicsSim.RESTITUTION
                    v[0] *= PhysicsSim.FRICTION
                    v[2] *= PhysicsSim.FRICTION

        # Colisão objeto-objeto (esferas aproximadas)
        n = len(objects)
        for i in range(n):
            for j in range(i + 1, n):
                a, b = objects[i], objects[j]
                if getattr(a, "is_static", False) and getattr(b, "is_static", False):
                    continue
                r_a = np.mean(a.transform.scale) * 0.5
                r_b = np.mean(b.transform.scale) * 0.5
                diff = a.transform.position - b.transform.position
                dist = np.linalg.norm(diff)
                min_dist = r_a + r_b
                if dist >= min_dist:
                    continue
                normal = diff / max(dist, 1e-5)
                overlap = min_dist - dist
                v_a = getattr(a, "physics_velocity", np.zeros(3, dtype=np.float32))
                v_b = getattr(b, "physics_velocity", np.zeros(3, dtype=np.float32))
                static_a = getattr(a, "is_static", False)
                static_b = getattr(b, "is_static", False)
                e = PhysicsSim.OBJ_RESTITUTION
                if static_a:
                    b.transform.position -= normal * overlap
                    vbn = np.dot(v_b, normal)
                    if vbn > 0:
                        v_b -= normal * (1 + e) * vbn
                elif static_b:
                    a.transform.position += normal * overlap
                    van = np.dot(v_a, normal)
                    if van < 0:
                        v_a -= normal * (1 + e) * van
                else:
                    a.transform.position += normal * (overlap * 0.5)
                    b.transform.position -= normal * (overlap * 0.5)
                    rel = v_a - v_b
                    van = np.dot(rel, normal)
                    if van < 0:
                        impulse = -(1 + e) * van / 2.0
                        v_a += normal * impulse
                        v_b -= normal * impulse
