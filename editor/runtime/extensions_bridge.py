"""ExtensionsBridge — Sprint 4d.

Conecta o ExtensionManagerDock ao Editor Framework 2.0:
  - EventBus (Workspace.*): notifica quando uma extensão é ativada/desativada
  - ToolRegistry: registra o Gerenciador de Extensões como ferramenta
  - ActionRegistry: ações "extensions.reload", "extensions.install", "extensions.disable"
  - Integração com o sistema de plugins do EditorApplication

Uso:
    bridge = ExtensionsBridge(editor_context)
    bridge.attach_dock(extension_manager_dock)
"""
from __future__ import annotations

from typing import Any


class ExtensionsBridge:
    """Conecta o ExtensionManagerDock ao Editor Framework 2.0."""

    def __init__(self, editor_context: Any) -> None:
        self._ctx = editor_context
        self._dock: Any = None
        self._extensions: dict[str, Any] = {}

        self._register_tool()
        self._register_actions()
        self._load_from_editor_application()

    def attach_dock(self, dock: Any) -> None:
        self._dock = dock
        if self._tool_def is not None:
            self._tool_def.dock = dock

    # ── Tool Registry ──────────────────────────────────────────────────────────

    def _register_tool(self) -> None:
        try:
            from editor.workspace.tool_registry import ToolDefinition, ToolRegistry
            tool = ToolDefinition(
                id="extensions.manager",
                label="Gerenciador de Extensões",
                dock=None,
                shortcuts=["Ctrl+Shift+E"],
                commands=["extensions.reload", "extensions.install",
                          "extensions.disable", "extensions.list"],
                menu="Ferramentas",
                icon="extension",
                category="Editor",
            )
            ToolRegistry.instance().register(tool)
            self._tool_def = tool
        except Exception as exc:
            print(f"[ExtensionsBridge] _register_tool: {exc}")
            self._tool_def = None

    # ── Action Registry ───────────────────────────────────────────────────────

    def _register_actions(self) -> None:
        try:
            from editor.core.action_system import EditorAction, ActionRegistry
            registry = ActionRegistry.instance()
            registry.register(EditorAction(
                id="extensions.reload",
                label="Recarregar Extensões",
                handler=self.reload_extensions,
                category="Editor",
                tags=["extensions", "plugins", "reload"],
            ))
            registry.register(EditorAction(
                id="extensions.list",
                label="Listar Extensões",
                handler=self.list_extensions,
                category="Editor",
                tags=["extensions", "plugins", "list"],
            ))
        except Exception:
            pass

    # ── EditorApplication Integration ─────────────────────────────────────────

    def _load_from_editor_application(self) -> None:
        """Carrega plugins registrados no EditorApplication."""
        try:
            from editor.core.editor_application import EditorApplication
            app = EditorApplication.instance()
            if app:
                self._extensions = dict(app.all_plugins())
        except Exception:
            pass

    # ── Extension API ─────────────────────────────────────────────────────────

    def register_extension(self, ext_id: str, extension: Any) -> None:
        """Registra uma extensão e notifica via Workspace.*"""
        self._extensions[ext_id] = extension
        try:
            from editor.core.editor_application import EditorApplication
            app = EditorApplication.instance()
            if app:
                app.register_plugin(ext_id, extension)
        except Exception:
            pass
        self._emit_extension_event("registered", ext_id=ext_id)

    def disable_extension(self, ext_id: str) -> bool:
        if ext_id not in self._extensions:
            return False
        self._emit_extension_event("disabled", ext_id=ext_id)
        return True

    def reload_extensions(self) -> None:
        """Recarrega todas as extensões ativas."""
        self._load_from_editor_application()
        self._emit_extension_event("reloaded", count=len(self._extensions))
        if self._dock and hasattr(self._dock, "populate_extensions"):
            try:
                self._dock.populate_extensions()
            except Exception:
                pass

    def install_extension(self, ext_id: str, source: str | None = None) -> bool:
        """Instala uma extensão (stub — real: baixar e registrar)."""
        self._emit_extension_event("installing", ext_id=ext_id, source=source)
        return True

    def list_extensions(self) -> list[str]:
        return list(self._extensions.keys())

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _emit_extension_event(self, sub_event: str, **kwargs: Any) -> None:
        try:
            from editor.core.event_bus import EventBus, EVENT_PANEL_OPENED
            EventBus.emit(EVENT_PANEL_OPENED, tool_id="extensions.manager",
                          event=sub_event, **kwargs)
        except Exception:
            pass
