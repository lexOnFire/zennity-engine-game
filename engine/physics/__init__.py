"""
engine/physics/__init__.py
──────────────────────────────────────────────────────────────────────
Re-exporta os símbolos públicos do subsistema de física.

USO:
    from engine.physics import RigidBody
    from engine.physics import BoxCollider, CircleCollider, CollisionInfo
    from engine.physics.collider import BoxCollider, CircleCollider, CollisionInfo  # também funciona

IMPORTANTE: lazy import via __getattr__ para não executar imports de
sub-módulos no momento do 'import engine.physics'. Isso preserva os
stubs de sys.modules usados pelos testes unitários.
"""

__all__ = [
    "RigidBody",
    "BoxCollider",
    "CircleCollider",
    "CollisionInfo",
]

_EXPORTS = {
    "RigidBody":      ("engine.physics.rigidbody", "RigidBody"),
    "BoxCollider":    ("engine.physics.collider",  "BoxCollider"),
    "CircleCollider": ("engine.physics.collider",  "CircleCollider"),
    "CollisionInfo":  ("engine.physics.collider",  "CollisionInfo"),
}


def __getattr__(name: str):
    if name in _EXPORTS:
        module_path, attr = _EXPORTS[name]
        import importlib
        mod = importlib.import_module(module_path)
        return getattr(mod, attr)
    raise AttributeError(f"module 'engine.physics' has no attribute {name!r}")
