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
    from engine.core import EventBus, GameObject, Scene, Engine

Imports legados (ainda funcionam via shim):

    from engine.application import Application   # shim
    from engine.system import System             # shim
    from engine.time import Time                 # shim
    from engine.logger import Logger             # shim
    from engine.event_bus import EventBus        # shim
    from engine.game_object import GameObject    # shim
    from engine.core import Scene                # shim (engine/core.py legado)
    from engine.core import Engine               # shim (engine/core.py legado)

Mapa de migração pendente:
    engine/component.py                     →  engine/core/component.py  [Sprint 1.3]
    engine/scene_manager.py                 →  engine/core/scene_manager.py [Sprint 1.3]
"""
from engine.application import Application          # noqa: F401
from engine.system      import System               # noqa: F401
from engine.system      import SystemPriority       # noqa: F401
from engine.system      import SystemRegistry       # noqa: F401
from engine.time        import Time                 # noqa: F401
from engine.logger      import Logger               # noqa: F401
from engine.event_bus   import EventBus             # noqa: F401
from engine.game_object import GameObject           # noqa: F401
from engine.core.scene  import Scene                # noqa: F401

# Engine permanece no legado engine/core.py até extração completa do SceneManager
try:
    from engine.core_legacy import Engine           # noqa: F401
except ImportError:
    pass  # engine/core_legacy.py ainda não existe — ignorar

__all__ = [
    "Application",
    "System",
    "SystemPriority",
    "SystemRegistry",
    "Time",
    "Logger",
    "EventBus",
    "GameObject",
    "Scene",
    "Engine",
]
