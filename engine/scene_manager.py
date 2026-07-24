"""
engine/scene_manager.py  —  SHIM de compatibilidade
────────────────────────────────────────────────────────────────
Este arquivo é mantido apenas para retrocompatibilidade.
Todo código novo deve importar de engine.core:

    from engine.core import SceneManager               # correto
    from engine.scene_manager import SceneManager      # legado (ainda funciona)
"""
import warnings as _warnings
_warnings.warn(
    "engine.scene_manager está deprecado. "
    "Use: from engine.core import SceneManager",
    DeprecationWarning,
    stacklevel=2,
)

from engine.core.scene_manager import SceneManager  # noqa: F401, E402

__all__ = ["SceneManager"]
