"""
engine/core
────────────────────────────────────────────────────────────────
Pacote canônico do núcleo da Zennity Engine (FASE 1).

Toda evolução futura ocorre NESTE pacote.
Os arquivos em engine/*.py são shims de compatibilidade.

Imports recomendados (novos projetos):

    from engine.core import Application, Time, Logger
    from engine.core import System, SystemPriority, SystemRegistry
    from engine.core import EventBus, GameObject, Scene
    from engine.core import Component, Transform

Mapa de migração pendente:
    engine/scene_manager.py  →  engine/core/scene_manager.py  [Sprint 1.3b]
    engine/core.py (Engine)  →  engine/core/engine.py (direto) [Sprint 1.4]
"""
from engine.application          import Application       # noqa: F401
from engine.system               import System            # noqa: F401
from engine.system               import SystemPriority    # noqa: F401
from engine.system               import SystemRegistry    # noqa: F401
from engine.time                 import Time              # noqa: F401
from engine.logger               import Logger            # noqa: F401
from engine.event_bus            import EventBus          # noqa: F401
from engine.game_object          import GameObject        # noqa: F401
from engine.core.scene           import Scene             # noqa: F401
from engine.core.component       import Component         # noqa: F401
from engine.core.component       import Transform         # noqa: F401

__all__ = [
    "Application",
    "System", "SystemPriority", "SystemRegistry",
    "Time",
    "Logger",
    "EventBus",
    "GameObject",
    "Scene",
    "Component",
    "Transform",
]
