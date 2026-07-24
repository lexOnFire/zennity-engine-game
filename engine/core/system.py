"""
engine/core/system.py
────────────────────────────────────────────────────────────────
Fonte canônica de System, SystemPriority, SystemRegistry.
O arquivo engine/system.py é agora um shim que importa daqui.
"""
from engine.system import System, SystemPriority, SystemRegistry  # noqa: F401

__all__ = ["System", "SystemPriority", "SystemRegistry"]
