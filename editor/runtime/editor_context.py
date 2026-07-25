"""EditorContext — contexto de projeto e cena do Zennity Studio.

Parte da hierarquia EditorApplication → EditorContext → SceneContext.
Não é um God Object: delega responsabilidades específicas para SceneContext.

Responsável por:
  - Projeto ativo (caminho raiz)
  - SceneContext da cena aberta
  - SelectionService (unificado para todos os editores)
  - CommandManager (undo/redo)
  - ToolManager (ferramenta ativa global)
  - RuntimeManager (play/pause/stop)
  - Referência ao WorkspaceManager (opcional, injetada pelo editor)
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from editor.runtime.command_manager import CommandManager
from editor.runtime.editor_state import EditorState
from editor.runtime.selection_manager import SelectionManager, SelectionService
from editor.runtime.tool_manager import ToolManager
from engine.runtime import RuntimeManager
from engine.runtime.runtime_manager import RuntimeState


class EditorContext:
    """Contexto de projeto/cena do editor (Editor Framework 2.0).

    Hierarquia:
        EditorApplication   ← plugins, tema, workspaces do usuário
            ↓
        EditorContext       ← projeto, cena, seleção, ferramenta      [ESTA CLASSE]
            ↓
        SceneContext        ← viewport, câmera, gizmos, objetos
    """

    def __init__(self, project_root: str | Path | None = None) -> None:
        self.project_root = Path(project_root or Path.cwd()).resolve()
        self.state = EditorState()
        self.selection = SelectionService()
        self.tools = ToolManager()
        self.commands = CommandManager()
        self.runtime = RuntimeManager()

        # Injetados externamente após a criação
        self.workspace: Any = None          # WorkspaceManager
        self._scene_context: Any = None     # SceneContext

        self.runtime.subscribe_state(self._on_runtime_state_changed)

    # ── SceneContext ───────────────────────────────────────────────────────────

    def open_scene(self, scene: Any) -> Any:
        """Cria e associa um novo SceneContext para a cena aberta."""
        from editor.runtime.scene_context import SceneContext
        self._scene_context = SceneContext(scene)
        return self._scene_context

    @property
    def scene_context(self) -> Any:
        return self._scene_context

    # ── Workspace ─────────────────────────────────────────────────────────────

    def attach_workspace(self, workspace_manager: Any) -> None:
        """Injeta o WorkspaceManager. Chamado pela MainWindow após criação."""
        self.workspace = workspace_manager

    # ── Runtime ───────────────────────────────────────────────────────────────

    def _on_runtime_state_changed(self, state: RuntimeState) -> None:
        self.state.is_playing = state == RuntimeState.PLAYING
        try:
            from editor.core.event_bus import EventBus, EVENT_PLAY_STATE_CHANGED
            EventBus.emit(EVENT_PLAY_STATE_CHANGED, state=state.name.lower())
        except Exception:
            pass

    def reset_scene_state(self) -> None:
        """Para o Play Mode e reseta todo o estado do editor para a cena.

        Fonte única de verdade para reset — não duplicar em widgets.
        """
        self.runtime.stop_play()
        self._on_runtime_state_changed(self.runtime.state)
        self.selection.clear_selection()
        self.commands.clear()

        if self._scene_context is not None:
            from editor.runtime.scene_context import SceneContext
            self._scene_context = SceneContext(getattr(self._scene_context, "scene", None))
