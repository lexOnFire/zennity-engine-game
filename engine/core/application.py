"""
engine/core/application.py
────────────────────────────────────────────────────────────────
Fonte canônica da classe Application.
O arquivo engine/application.py é agora um shim que importa daqui.
"""
# Re-exporta o módulo completo para que
# `from engine.core.application import Application` funcione.
from engine.application import Application  # noqa: F401

__all__ = ["Application"]
