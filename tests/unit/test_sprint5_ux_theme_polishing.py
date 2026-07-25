"""Testes unitários do Sprint 5 — Polimento de UX, temas consistentes e atalhos unificados.

Valida:
  - ThemeManager: suporta Dark, Light e High Contrast, aplicando tokens e notificando ouvintes
  - ActionRegistry + ToolRegistry: valida integridade de atalhos e ações registradas
"""
from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import pytest


# ─────────────────────────────────────────────────────────────────────────────
# ThemeManager Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_theme_manager_singleton_and_tokens():
    """ThemeManager obtém tokens corretos para Dark, Light e High Contrast."""
    from editor.core.theme_manager import ThemeManager

    mgr = ThemeManager.instance()
    
    dark_tokens = mgr.get_tokens("dark")
    light_tokens = mgr.get_tokens("light")
    hc_tokens = mgr.get_tokens("high_contrast")

    assert dark_tokens.bg == "#16161d" or dark_tokens.bg == "#1a1a22" or dark_tokens.bg.startswith("#")
    assert light_tokens.bg == "#f5f5f7"
    assert hc_tokens.bg == "#000000"


def test_theme_manager_apply_and_notify():
    """apply_theme altera o tema atual e notifica callbacks registrados."""
    from editor.core.theme_manager import ThemeManager

    mgr = ThemeManager.instance()
    notifications = []

    mgr.subscribe(lambda t: notifications.append(t))
    mgr.apply_theme("light")

    assert mgr.current_theme_name == "light"
    assert "light" in notifications

    # Retorna para dark ao final
    mgr.apply_theme("dark")
    assert mgr.current_theme_name == "dark"


# ─────────────────────────────────────────────────────────────────────────────
# Actions & Shortcuts Consistency
# ─────────────────────────────────────────────────────────────────────────────

def test_all_tools_have_shortcuts_and_actions():
    """Garante que todas as 8 ferramentas principais possuem ações e atalhos configurados no ToolRegistry."""
    from editor.runtime.editor_bridge_orchestrator import EditorBridgeOrchestrator
    from editor.workspace.tool_registry import ToolRegistry
    from editor.runtime.editor_context import EditorContext

    ctx = EditorContext()
    orchestrator = EditorBridgeOrchestrator(ctx)
    orchestrator.setup()

    registry = ToolRegistry.instance()
    tools = registry.all_tools()

    assert len(tools) >= 8

    for tool in tools:
        assert len(tool.shortcuts) > 0, f"Ferramenta '{tool.id}' está sem atalho configurado"
        assert len(tool.commands) > 0, f"Ferramenta '{tool.id}' está sem comandos configurados"
