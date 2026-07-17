"""Tokens visuais: nenhuma tela deve inventar cores ou espaçamentos próprios."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EditorThemeTokens:
    bg: str = "#101217"
    surface: str = "#171a21"
    surface_raised: str = "#1d212a"
    surface_hover: str = "#252a35"
    input_bg: str = "#11141a"
    border: str = "#2b303b"
    border_strong: str = "#3a414f"
    text: str = "#e7eaf0"
    text_muted: str = "#929aa9"
    text_disabled: str = "#5d6470"
    accent: str = "#5b8cff"
    accent_hover: str = "#729cff"
    accent_soft: str = "#263a63"
    success: str = "#58c878"
    warning: str = "#e1b755"
    danger: str = "#ef6a6a"
    danger_soft: str = "#4b292d"
    radius_small: int = 4
    radius: int = 6
    spacing_xs: int = 4
    spacing_sm: int = 8
    spacing_md: int = 12
    spacing_lg: int = 16
    font_size: int = 11
    control_height: int = 26


DEFAULT_TOKENS = EditorThemeTokens()
