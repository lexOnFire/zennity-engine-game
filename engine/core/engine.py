"""
engine/core/engine.py
────────────────────────────────────────────────────────────────
Fonte canônica da classe Engine.
Extraid de engine/core.py (legado).

O engine/core.py legado re-exporta daqui para retrocompatibilidade.
"""
from engine.core_legacy import Engine, UpdateSystem, RenderSystem, _builtin_physics_system  # noqa: F401

__all__ = ["Engine", "UpdateSystem", "RenderSystem", "_builtin_physics_system"]
