"""ThemeManager — Gerenciamento unificado de temas e polimento de UX (Sprint 5).

Responsável por:
- Fornecer suporte aos temas Dark, Light e High Contrast.
- Aplicação consistente de QSS em todas as docks e janelas do editor.
- Troca em tempo real de temas integrada com EditorApplication.
"""
from __future__ import annotations

from typing import Any, Callable
from PySide6.QtWidgets import QApplication, QWidget

from editor.core.editor_application import EditorApplication
from editor.ui.theme import build_editor_stylesheet
from editor.ui.tokens import (
    DEFAULT_TOKENS,
    EditorThemeTokens,
)

DARK_TOKENS = DEFAULT_TOKENS

LIGHT_TOKENS = EditorThemeTokens(
    bg="#f5f5f7",
    surface="#ffffff",
    surface_raised="#e8e8ed",
    surface_hover="#d8d8de",
    input_bg="#ffffff",
    border="#d1d1d6",
    border_strong="#a1a1a6",
    text="#1c1c1e",
    text_muted="#6c6c70",
    text_disabled="#aeae42",
    accent="#007aff",
    accent_hover="#0056b3",
    accent_soft="#e5f1ff",
    success="#34c759",
    warning="#ff9500",
    danger="#ff3b30",
    danger_soft="#ffe5e5",
    radius_small=4,
    radius=6,
    spacing_xs=4,
    spacing_sm=8,
    spacing_md=12,
    spacing_lg=16,
    font_size=11,
    control_height=26,
)

HIGH_CONTRAST_TOKENS = EditorThemeTokens(
    bg="#000000",
    surface="#000000",
    surface_raised="#1c1c1c",
    surface_hover="#333333",
    input_bg="#000000",
    border="#ffffff",
    border_strong="#ffffff",
    text="#ffffff",
    text_muted="#dddddd",
    text_disabled="#666666",
    accent="#ffff00",
    accent_hover="#ffff66",
    accent_soft="#333300",
    success="#00ff00",
    warning="#ff9900",
    danger="#ff0000",
    danger_soft="#330000",
    radius_small=0,
    radius=0,
    spacing_xs=4,
    spacing_sm=8,
    spacing_md=12,
    spacing_lg=16,
    font_size=12,
    control_height=28,
)


class ThemeManager:
    """Gerenciador central de temas do editor."""

    _instance: ThemeManager | None = None

    def __init__(self) -> None:
        self._current_theme_name: str = "dark"
        self._listeners: list[Callable[[str], None]] = []

    @classmethod
    def instance(cls) -> ThemeManager:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @property
    def current_theme_name(self) -> str:
        return self._current_theme_name

    def get_tokens(self, theme_name: str | None = None) -> EditorThemeTokens:
        name = (theme_name or self._current_theme_name).lower()
        if name == "light":
            return LIGHT_TOKENS
        elif name == "high_contrast":
            return HIGH_CONTRAST_TOKENS
        return DARK_TOKENS

    def apply_theme(self, theme_name: str, app_or_widget: Any = None) -> None:
        """Aplica o stylesheet do tema à aplicação ou widget especificado."""
        self._current_theme_name = theme_name.lower()
        tokens = self.get_tokens(self._current_theme_name)
        qss = build_editor_stylesheet(tokens)

        target = app_or_widget or QApplication.instance()
        if target and hasattr(target, "setStyleSheet"):
            target.setStyleSheet(qss)

        # Atualiza a preferência no EditorApplication se presente
        app = EditorApplication.instance()
        if app:
            app.set_theme(self._current_theme_name)

        self._notify_listeners()

    def subscribe(self, callback: Callable[[str], None]) -> None:
        if callback not in self._listeners:
            self._listeners.append(callback)

    def _notify_listeners(self) -> None:
        for listener in list(self._listeners):
            try:
                listener(self._current_theme_name)
            except Exception:
                pass
