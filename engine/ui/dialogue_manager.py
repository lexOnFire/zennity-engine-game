"""
DialogueManager — Sistema de diálogos com ramificações, flags e UI automática.

Wrapper amigável ao redor de DialogueSession que oferece:
  - Carregamento automático de arquivos .zdialogue
  - Gerenciamento de UI (texto, botões de escolha)
  - Flags de estado persistentes
  - Callbacks em eventos
  - Integração com eventos da engine

Exemplo:
    go.add_component(DialogueManager(
        dialogue_file="Assets/Dialogues/merchant.zdialogue",
        speaker_name="merchant",
        auto_start=False
    ))

    # Quando iniciado:
    manager = go.get_component(DialogueManager)
    manager.start()

    # Avança diálogo ou escolhe opção:
    manager.advance()
    manager.choose_option(0)
"""

from __future__ import annotations
from typing import Any, Optional, Callable, TYPE_CHECKING
from pathlib import Path
import json

from engine.core.component import Component
from engine.dialogue.runtime import DialogueSession

if TYPE_CHECKING:
    from engine.game_object import GameObject


class DialogueManager(Component):
    """Gerenciador de diálogos com suporte a ramificações e flags."""

    UNIQUE = False
    component_type = "DialogueManager"

    def __init__(
        self,
        dialogue_file: str = "",
        speaker_name: str = "",
        auto_start: bool = False,
        ui_text_element: str = "",
        ui_options_container: str = "",
        continue_on_advance: bool = False,
    ):
        """
        Parameters
        ----------
        dialogue_file : str
            Caminho para arquivo .zdialogue (ex: "Assets/Dialogues/merchant.zdialogue")
        speaker_name : str
            Nome do NPC/personagem que está falando
        auto_start : bool
            Se True, inicia diálogo automaticamente ao entrar na cena
        ui_text_element : str
            Nome do elemento UI que exibe o texto do diálogo
        ui_options_container : str
            Nome do container que exibe os botões de opção
        continue_on_advance : bool
            Se True, avança automaticamente quando não há escolhas
        """
        super().__init__()
        self.dialogue_file = dialogue_file
        self.speaker_name = speaker_name
        self.auto_start = auto_start
        self.ui_text_element = ui_text_element
        self.ui_options_container = ui_options_container
        self.continue_on_advance = continue_on_advance

        self._session: Optional[DialogueSession] = None
        self._is_active = False
        self._dialogue_data: Optional[dict] = None

        # Callbacks
        self._on_dialogue_start: Optional[Callable] = None
        self._on_dialogue_choice: Optional[Callable[[int], None]] = None
        self._on_dialogue_end: Optional[Callable] = None
        self._on_event: Optional[Callable[[str, Any], None]] = None

    def start(self) -> None:
        """Inicializa o gerenciador de diálogos."""
        self._load_dialogue_file()

        if self.auto_start:
            self.begin_dialogue()

    def begin_dialogue(self) -> None:
        """Inicia um novo diálogo."""
        if self._session is None:
            self._load_dialogue_file()

        if self._session is None:
            return

        snapshot = self._session.start()
        self._is_active = snapshot.get("active", False)

        if self._on_dialogue_start:
            self._on_dialogue_start()

        self._update_ui(snapshot)

    def advance(self) -> None:
        """Avança para o próximo nó do diálogo."""
        if self._session is None or not self._is_active:
            return

        snapshot = self._session.advance()
        self._is_active = snapshot.get("active", False)

        self._update_ui(snapshot)

        # Se chegou ao fim, dispara callback
        if not self._is_active and self._on_dialogue_end:
            self._on_dialogue_end()

    def choose_option(self, option_index: int) -> None:
        """
        Escolhe uma opção no diálogo.

        Parameters
        ----------
        option_index : int
            Índice da opção (0, 1, 2, ...)
        """
        if self._session is None or not self._is_active:
            return

        try:
            snapshot = self._session.choose(option_index)
            self._is_active = snapshot.get("active", False)

            if self._on_dialogue_choice:
                self._on_dialogue_choice(option_index)

            self._update_ui(snapshot)

            # Se chegou ao fim, dispara callback
            if not self._is_active and self._on_dialogue_end:
                self._on_dialogue_end()

        except RuntimeError:
            pass

    def set_flag(self, flag_name: str, value: Any) -> None:
        """Define uma flag/variável para usar em condições."""
        if self._session is not None:
            self._session.set_variable(flag_name, value)

    def get_flag(self, flag_name: str, default: Any = None) -> Any:
        """Obtém o valor de uma flag/variável."""
        if self._session is None:
            return default
        return self._session.variables.get(flag_name, default)

    def is_active(self) -> bool:
        """Retorna se um diálogo está ativo."""
        return self._is_active

    def get_current_snapshot(self) -> dict:
        """Retorna o estado atual do diálogo."""
        if self._session is None:
            return {}
        return self._session.snapshot()

    def on_dialogue_start(self, callback: Callable) -> None:
        """Registra callback quando diálogo inicia."""
        self._on_dialogue_start = callback

    def on_dialogue_choice(self, callback: Callable[[int], None]) -> None:
        """Registra callback quando escolha é feita."""
        self._on_dialogue_choice = callback

    def on_dialogue_end(self, callback: Callable) -> None:
        """Registra callback quando diálogo termina."""
        self._on_dialogue_end = callback

    def on_event(self, callback: Callable[[str, Any], None]) -> None:
        """Registra callback para eventos do diálogo."""
        self._on_event = callback

    # ======================================================================
    # Métodos internos
    # ======================================================================

    def _load_dialogue_file(self) -> None:
        """Carrega arquivo .zdialogue."""
        if not self.dialogue_file or self._session is not None:
            return

        try:
            # Resolve caminho relativo ao projeto
            dialogue_path = Path(self.dialogue_file)
            if not dialogue_path.is_absolute():
                # Tenta relativo ao diretório do projeto
                from engine.core.asset_loader import AssetLoader

                dialogue_path = AssetLoader.resolve_asset_path(self.dialogue_file)

            if not dialogue_path.exists():
                return

            # Carrega arquivo JSON
            self._dialogue_data = json.loads(dialogue_path.read_text(encoding="utf-8"))

            # Cria sessão com event_sink
            def handle_event(event_name: str, payload: Any) -> None:
                if self._on_event:
                    self._on_event(event_name, payload)

            self._session = DialogueSession(
                self._dialogue_data,
                variables={},
                event_sink=handle_event,
            )
        except Exception as e:
            # Silencia erros de carregamento
            pass

    def _update_ui(self, snapshot: dict) -> None:
        """Atualiza elementos UI com dados do diálogo."""
        if not snapshot:
            return

        # Atualiza texto do diálogo
        text = snapshot.get("text", "")
        speaker = snapshot.get("speaker", self.speaker_name)

        if speaker and text:
            display_text = f"{speaker}: {text}"
        else:
            display_text = text

        if self.ui_text_element:
            self._set_ui_text(self.ui_text_element, display_text)

        # Atualiza opções de escolha
        options = snapshot.get("options", [])
        self._update_options_ui(options)

    def _set_ui_text(self, element_name: str, text: str) -> None:
        """Define texto em um elemento UI."""
        scene = getattr(self.game_object, "scene", None)
        if scene is None:
            return

        for obj in getattr(scene, "editable_objects", []):
            if getattr(obj, "name", "") == element_name:
                # Tenta chamar set_text
                if hasattr(obj, "set_text"):
                    obj.set_text(text)
                elif hasattr(obj, "text"):
                    obj.text = text
                return

    def _update_options_ui(self, options: list) -> None:
        """Atualiza botões de opção na UI."""
        # Implementação simplificada
        # Em um sistema real, criaria botões dinamicamente
        pass

    def serialize(self) -> dict:
        """Serializa o componente."""
        data = super().serialize()
        data["dialogue_file"] = self.dialogue_file
        data["speaker_name"] = self.speaker_name
        data["auto_start"] = self.auto_start
        data["ui_text_element"] = self.ui_text_element
        data["ui_options_container"] = self.ui_options_container
        data["continue_on_advance"] = self.continue_on_advance
        # Salva flags atuais
        if self._session:
            data["variables"] = dict(self._session.variables)
        return data

    def deserialize(self, data: dict) -> None:
        """Desserializa o componente."""
        super().deserialize(data)
        self.dialogue_file = data.get("dialogue_file", "")
        self.speaker_name = data.get("speaker_name", "")
        self.auto_start = data.get("auto_start", False)
        self.ui_text_element = data.get("ui_text_element", "")
        self.ui_options_container = data.get("ui_options_container", "")
        self.continue_on_advance = data.get("continue_on_advance", False)
