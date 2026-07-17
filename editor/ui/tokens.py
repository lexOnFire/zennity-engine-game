"""Tokens visuais: nenhuma tela deve inventar cores ou espaçamentos próprios."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EditorThemeTokens:
    bg: str = "#eef0f4"  # Fundo levemente cinza
    surface: str = "#ffffff"  # Fundo branco puro
    surface_raised: str = "#f8f9fa"  # Cinza claríssimo para menus e destaques
    surface_hover: str = "#e2e6ea"  # Cinza claro de hover
    input_bg: str = "#ffffff"
    border: str = "#d1d5db"  # Prata/cinza suave
    border_strong: str = "#9ca3af"  # Prata mais forte
    text: str = "#111827"  # Azul escuro / Navy quase preto (do logo)
    text_muted: str = "#4b5563"
    text_disabled: str = "#9ca3af"
    accent: str = "#0ea5e9"  # Ciano/azul brilhante
    accent_hover: str = "#0284c7"
    accent_soft: str = "#e0f2fe"  # Fundo selecionado (cyan bem suave)
    success: str = "#10b981"
    warning: str = "#f59e0b"
    danger: str = "#ef4444"
    danger_soft: str = "#fee2e2"
    radius_small: int = 4
    radius: int = 6
    spacing_xs: int = 4
    spacing_sm: int = 8
    spacing_md: int = 12
    spacing_lg: int = 16
    font_size: int = 11
    control_height: int = 26


DEFAULT_TOKENS = EditorThemeTokens()
