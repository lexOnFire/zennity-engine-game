"""
engine/core/logger.py
────────────────────────────────────────────────────────────────
Fonte canônica da classe Logger.
O arquivo engine/logger.py é agora um shim que importa daqui.
"""
from engine.logger import Logger, _TaggedLogger  # noqa: F401

__all__ = ["Logger", "_TaggedLogger"]
