"""
engine/physics/__init__.py
──────────────────────────────────────────────────────────────────────
Re-exporta os símbolos públicos do subsistema de física.

Importe via:
    from engine.physics import RigidBody, BoxCollider, CircleCollider, CollisionInfo
    from engine.physics.collider import BoxCollider, CircleCollider, CollisionInfo
"""
from engine.physics.rigidbody   import RigidBody
from engine.physics.collider    import BoxCollider, CircleCollider, CollisionInfo

__all__ = [
    "RigidBody",
    "BoxCollider",
    "CircleCollider",
    "CollisionInfo",
]
