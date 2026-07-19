"""Tokens visuais: nenhuma tela deve inventar cores ou espaçamentos próprios."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EditorThemeTokens:
    bg: str = "#121317"  # Slate dark background
    surface: str = "#181a20"  # Dark panel background
    surface_raised: str = "#22252e"  # Slightly raised dark grey for buttons/tabs
    surface_hover: str = "#2c303c"  # Highlight color for hovered items
    input_bg: str = "#0f1013"  # Deep black for input boxes
    border: str = "#2b2e3a"  # Subtle dark borders
    border_strong: str = "#3f4456"  # Visible boundaries
    text: str = "#e3e6ed"  # High contrast crisp light grey text
    text_muted: str = "#8b949e"  # Muted grey text for captions/hints
    text_disabled: str = "#484f58"  # Dark grey for disabled actions
    accent: str = "#00adb5"  # Vibrant neon cyan for selection highlights
    accent_hover: str = "#00cbd3"  # Hover highlight ciano
    accent_soft: str = "#142c33"  # Translucent neon selection overlay
    success: str = "#10b981"
    warning: str = "#f59e0b"
    danger: str = "#ef4444"
    danger_soft: str = "#3c1e22"
    radius_small: int = 4
    radius: int = 6
    spacing_xs: int = 4
    spacing_sm: int = 8
    spacing_md: int = 12
    spacing_lg: int = 16
    font_size: int = 11
    control_height: int = 26


DEFAULT_TOKENS = EditorThemeTokens()
