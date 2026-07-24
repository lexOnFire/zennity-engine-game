"""
engine/component.py  —  SHIM de compatibilidade
────────────────────────────────────────────────────────────────
Este arquivo é mantido apenas para retrocompatibilidade.
Todo código novo deve importar de engine.core:

    from engine.core import Component, Transform   # correto
    from engine.component import Component         # legado (ainda funciona)
"""
import warnings as _warnings
_warnings.warn(
    "engine.component está deprecado. "
    "Use: from engine.core import Component, Transform",
    DeprecationWarning,
    stacklevel=2,
)

from engine.core.component import Component, Transform  # noqa: F401, E402

__all__ = ["Component", "Transform"]
