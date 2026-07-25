"""EditorApplication — camada mais alta do Zennity Studio.

Independente de cena ou projeto. Gerencia estado global da aplicação:
plugins, tema, preferências do usuário e workspaces persistidos.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from PySide6.QtCore import QSettings


class EditorApplication:
    """Camada global do editor. Não conhece cenas nem seleções.

    Responsável por:
    - Plugins globais (extensões de aplicação)
    - Tema e aparência
    - Workspaces salvos pelo usuário
    - Preferências persistentes
    """

    _instance: EditorApplication | None = None

    def __init__(self, app_name: str = "ZennityStudio") -> None:
        self.app_name = app_name
        self.settings = QSettings("ZennityEngine", app_name)
        self._plugins: dict[str, Any] = {}
        self._user_workspaces: dict[str, dict] = {}
        self._theme: str = "dark"
        self._load_user_workspaces()
        EditorApplication._instance = self

    @classmethod
    def instance(cls) -> EditorApplication | None:
        return cls._instance

    # ── Tema ──────────────────────────────────────────────────────────────────

    @property
    def theme(self) -> str:
        return self._theme

    def set_theme(self, theme: str) -> None:
        self._theme = theme
        self.settings.setValue("theme", theme)

    # ── Plugins Globais ───────────────────────────────────────────────────────

    def register_plugin(self, plugin_id: str, plugin: Any) -> None:
        self._plugins[plugin_id] = plugin

    def get_plugin(self, plugin_id: str) -> Any | None:
        return self._plugins.get(plugin_id)

    def all_plugins(self) -> dict[str, Any]:
        return dict(self._plugins)

    # ── Workspaces do Usuário ─────────────────────────────────────────────────

    def save_user_workspace(self, name: str, layout_data: dict) -> None:
        """Salva um workspace personalizado pelo usuário com estado completo."""
        self._user_workspaces[name] = layout_data
        self._persist_user_workspaces()

    def load_user_workspace(self, name: str) -> dict | None:
        return self._user_workspaces.get(name)

    def delete_user_workspace(self, name: str) -> bool:
        if name in self._user_workspaces:
            del self._user_workspaces[name]
            self._persist_user_workspaces()
            return True
        return False

    def list_user_workspaces(self) -> list[str]:
        return list(self._user_workspaces.keys())

    def _load_user_workspaces(self) -> None:
        import json
        raw = self.settings.value("user_workspaces", "{}")
        try:
            self._user_workspaces = json.loads(raw) if isinstance(raw, str) else {}
        except Exception:
            self._user_workspaces = {}

    def _persist_user_workspaces(self) -> None:
        import json
        self.settings.setValue("user_workspaces", json.dumps(self._user_workspaces))
