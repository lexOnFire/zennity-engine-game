from __future__ import annotations

from pathlib import Path

from editor.runtime.command_manager import CommandManager
from editor.runtime.editor_state import EditorState
from editor.runtime.selection_manager import SelectionManager
from editor.runtime.tool_manager import ToolManager
from engine.runtime import RuntimeManager
from engine.runtime.runtime_manager import RuntimeState


class EditorContext:
    """Container explícito dos serviços de runtime do editor.

    Fonte única de verdade para:
    - Estado do editor (EditorState)
    - Seleção ativa (SelectionManager)
    - Comandos undo/redo (CommandManager)
    - Ferramentas ativas (ToolManager)
    - Play Mode (RuntimeManager)
    """

    def __init__(self, project_root: str | Path | None = None) -> None:
        self.project_root = Path(project_root or Path.cwd()).resolve()
        self.state = EditorState()
        self.selection = SelectionManager()
        self.tools = ToolManager()
        self.commands = CommandManager()
        self.runtime = RuntimeManager()
        self.runtime.subscribe_state(self._on_runtime_state_changed)

    def _on_runtime_state_changed(self, state: RuntimeState) -> None:
        self.state.is_playing = state == RuntimeState.PLAYING

    def reset_scene_state(self) -> None:
        """Para o Play Mode e reseta todo o estado do editor para a cena.

        Fonte única de verdade para reset — não duplicar em widgets.
        """
        # Para o runtime (idempotente)
        self.runtime.stop_play()

        # Reprojeta o estado canônico mesmo se o runtime já estava parado.
        self._on_runtime_state_changed(self.runtime.state)

        # Limpa seleção e histórico de comandos.
        self.selection.clear()
        self.commands.clear()
