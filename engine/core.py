"""
engine/core.py  —  SHIM de compatibilidade
────────────────────────────────────────────────────────────────
Este arquivo era o núcleo da engine até a Sprint 1.4.
Agora é um shim puro que re-exporta de engine/core/ (pacote).

Todo código novo deve importar de engine.core (pacote):

    from engine.core import Scene, Engine, SceneManager     # correto
    from engine.core import Component, Transform            # correto
    from engine.core import Application, Time, EventBus    # correto

    # legado (ainda funciona, sem aviso):
    from engine.core import Scene    # este arquivo re-exporta
    from engine.core import Engine   # este arquivo re-exporta

Nota: Python resolve `engine.core` para o PACOTE (engine/core/__init__.py)
automaticamente quando o diretório engine/core/ existe. Este arquivo
funciona como fallback caso o pacote não esteja no path, mas na
instalação normal ele não será executado.
"""
# Re-exporta tudo que este arquivo já exportava, agora vindo do pacote.
from engine.core.scene          import Scene                        # noqa: F401
from engine.core.engine         import Engine                       # noqa: F401
from engine.core.engine         import UpdateSystem, RenderSystem   # noqa: F401
from engine.core.engine         import _builtin_physics_system      # noqa: F401
from engine.core.scene_manager  import SceneManager                 # noqa: F401

__all__ = [
    "Scene",
    "Engine",
    "UpdateSystem",
    "RenderSystem",
    "_builtin_physics_system",
    "SceneManager",
]
