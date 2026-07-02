"""
engine/core
────────────────────────────────────────────────────────────────
Pacote canônico do núcleo da Zennity Engine (FASE 1).

Toda evolução futura ocorre NESTE pacote.
Os arquivos em engine/*.py são shims de compatibilidade
que re-exportam daqui — não os evolua mais.

Imports recomendados (novos projetos):

    from engine.core import Application, Time, Logger
    from engine.core import System, SystemPriority, SystemRegistry
    from engine.core import EventBus, GameObject

Imports legados (ainda funcionam via shim):

    from engine.application import Application   # shim → engine.core.application
    from engine.system import System             # shim → engine.core.system
    from engine.time import Time                 # shim → engine.core.time
    from engine.logger import Logger             # shim → engine.core.logger
    from engine.event_bus import EventBus        # shim → engine.core.event_bus
    from engine.game_object import GameObject    # shim → engine.core.game_object

Mapa de migração pendente:
    engine/core.py  (Scene, Engine legado)  →  engine/core/scene.py   [Sprint 1.2]
    engine/component.py                     →  engine/core/component.py [Sprint 1.2]
    engine/scene_manager.py                 →  engine/core/scene_manager.py [Sprint 1.2]
"""
from engine.application import Application          # noqa: F401
from engine.system      import System               # noqa: F401
from engine.system      import SystemPriority       # noqa: F401
from engine.system      import SystemRegistry       # noqa: F401
from engine.time        import Time                 # noqa: F401
from engine.logger      import Logger               # noqa: F401
from engine.event_bus   import EventBus             # noqa: F401
from engine.game_object import GameObject           # noqa: F401

__all__ = [
    "Application",
    "System",
    "SystemPriority",
    "SystemRegistry",
    "Time",
    "Logger",
    "EventBus",
    "GameObject",
]
