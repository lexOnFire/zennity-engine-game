"""
engine/core/event_bus.py
────────────────────────────────────────────────────────────────
Fonte canônica da classe EventBus.
O arquivo engine/event_bus.py é agora um shim que importa daqui.
"""
from engine.event_bus import EventBus  # noqa: F401

__all__ = ["EventBus"]
