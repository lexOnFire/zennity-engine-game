"""
engine/core
────────────────────────────────────────────────────────────────
Pacote canônico do núcleo da Zennity Engine.
FASE 1 concluída: toda evolução ocorre AQUI.

Imports recomendados (novos projetos):

    from engine.core import Application, Time, Logger
    from engine.core import System, SystemPriority, SystemRegistry
    from engine.core import EventBus, GameObject
    from engine.core import Scene, Component, Transform
    from engine.core import SceneManager, Engine
    from engine.core import UpdateSystem, RenderSystem
    from engine.core import _builtin_physics_system

Arquivos legados (shims, ainda funcionam):
    engine/component.py      →  DeprecationWarning
    engine/scene_manager.py  →  DeprecationWarning
    engine/core.py           →  re-exporta silenciosamente
"""
# ── Core types must be imported FIRST ────────────────────────────────────────
# Application (engine/application.py) depends on Scene and Engine.
# If Application is imported before these types are registered in sys.modules,
# Python raises: ImportError: cannot import name 'Scene' from partially
# initialized module 'engine.core' (circular import).
# Rule: anything that imports FROM engine.core must come AFTER engine.core types.
from engine.system               import System                    # noqa: F401
from engine.system               import SystemPriority            # noqa: F401
from engine.system               import SystemRegistry            # noqa: F401
from engine.time                 import Time                      # noqa: F401
from engine.logger               import Logger                    # noqa: F401
from engine.event_bus            import EventBus                  # noqa: F401
from engine.game_object          import GameObject                # noqa: F401
from engine.core.scene           import Scene                     # noqa: F401
from engine.core.component       import Component                 # noqa: F401
from engine.core.component       import Transform                 # noqa: F401
from engine.core.scene_manager   import SceneManager              # noqa: F401
from engine.core.engine          import Engine                    # noqa: F401
from engine.core.engine          import UpdateSystem, RenderSystem  # noqa: F401
from engine.core.engine          import _builtin_physics_system   # noqa: F401

# ── Application LAST — it imports Scene and Engine from this very module ─────
from engine.application          import Application               # noqa: F401

__all__ = [
    # Application layer
    "Application",
    # Systems
    "System", "SystemPriority", "SystemRegistry",
    # Utilities
    "Time", "Logger", "EventBus",
    # ECS core
    "GameObject", "Scene", "Component", "Transform",
    # Runtime
    "SceneManager", "Engine",
    "UpdateSystem", "RenderSystem",
    "_builtin_physics_system",
]
