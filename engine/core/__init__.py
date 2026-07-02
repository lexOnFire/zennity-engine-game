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
from engine.application          import Application               # noqa: F401
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
