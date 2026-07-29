"""
engine/component.py  —  SHIM de compatibilidade
────────────────────────────────────────────────────────────────
Este arquivo é mantido apenas para retrocompatibilidade.
Todo código novo deve importar de engine.core:

    from engine.core import Component, Transform   # correto
    from engine.core import Component         # legado (ainda funciona)
"""
import warnings

from engine.core import Component, Transform


warnings.warn(
    "engine.component está deprecado. "
    "Use: from engine.core import Component, Transform",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = ["Component", "Transform"]
