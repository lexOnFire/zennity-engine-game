"""
engine/component.py  —  SHIM de compatibilidade
────────────────────────────────────────────────────────────────
Este arquivo é mantido apenas para retrocompatibilidade.
Todo código novo deve importar de engine.core:

    from engine.core import Component, Transform   # correto
    from engine.core import Component         # legado (ainda funciona)
"""
import traceback
import warnings

print("=" * 80)
print("engine.component foi importado por:")
traceback.print_stack(limit=12)
print("=" * 80)

warnings.warn(
    "engine.component está deprecado. "
    "Use: from engine.core import Component, Transform",
    DeprecationWarning,
    stacklevel=2,
)