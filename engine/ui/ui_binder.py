"""
UIBinder — Componente para sincronização automática de dados com UI.

Vincula uma propriedade de um objeto a um elemento de UI (Label, ProgressBar, etc).
Suporta dois modos:
  - "auto": Sincroniza a cada frame (polling)
  - "event": Sincroniza apenas quando evento é emitido (reativo)

Exemplo:
    # Setup automático
    go.add_component(UIBinder(
        source_path="player.health",
        ui_element_name="HealthLabel",
        bind_mode="auto",
        format_string="{value}/100"
    ))
"""

from __future__ import annotations
from typing import Any, Optional, Callable, TYPE_CHECKING
from engine.core.component import Component

if TYPE_CHECKING:
    from engine.game_object import GameObject


class UIBinder(Component):
    """Sincroniza propriedades de objetos com elementos UI."""

    UNIQUE = False
    component_type = "UIBinder"

    def __init__(
        self,
        source_path: str = "",
        ui_element_name: str = "",
        bind_mode: str = "auto",
        format_string: str = "{value}",
        precision: int = 0,
        event_name: Optional[str] = None,
    ):
        """
        Parameters
        ----------
        source_path : str
            Caminho para a propriedade (ex: "player.health", "game.score")
        ui_element_name : str
            Nome do elemento UI no canvas para atualizar
        bind_mode : str
            "auto" para polling em update(), "event" para event-driven
        format_string : str
            String de formatação Python (ex: "{value}/100", "HP: {value:.1f}")
        precision : int
            Casas decimais para formatação automática (só se format não tiver .Nf)
        event_name : str, optional
            Nome do evento a escutar (usado em bind_mode="event")
        """
        super().__init__()
        self.source_path = source_path
        self.ui_element_name = ui_element_name
        self.bind_mode = bind_mode
        self.format_string = format_string
        self.precision = precision
        self.event_name = event_name or f"{source_path}_changed"

        self._last_value: Any = None
        self._ui_element: Any = None
        self._on_value_changed: Optional[Callable] = None

    def start(self) -> None:
        """Inicializa o binding e busca o elemento UI."""
        self._find_ui_element()

        if self.bind_mode == "auto":
            self._setup_auto_binding()
        elif self.bind_mode == "event":
            self._setup_event_binding()

    def update(self, dt: float) -> None:
        """Se auto mode, sincroniza a cada frame."""
        if self.bind_mode != "auto" or self._ui_element is None:
            return

        value = self._resolve_value()
        if value is not None and value != self._last_value:
            self._on_value_changed_internal(value)

    def _find_ui_element(self) -> None:
        """Procura pelo elemento UI no canvas."""
        if not self.ui_element_name:
            return

        # Procura na cena por um objeto com este nome
        scene = getattr(self.game_object, "scene", None)
        if scene is None:
            return

        # Procura em editable_objects
        for obj in getattr(scene, "editable_objects", []):
            if getattr(obj, "name", "") == self.ui_element_name:
                self._ui_element = obj
                return

    def _setup_auto_binding(self) -> None:
        """Setup para modo automático (polling)."""
        # Nada especial, update() fará o polling
        pass

    def _setup_event_binding(self) -> None:
        """Setup para modo event-driven."""
        # Registra listener no event bus
        try:
            from engine.logic.event_bus import EventBus

            EventBus.subscribe(self.event_name, self._on_value_changed_internal)
        except ImportError:
            pass

    def _resolve_value(self) -> Any:
        """
        Resolve o caminho source_path até o valor atual.

        Exemplos:
            "player.health"      → game_object.player.health
            "game.score"         → scene.game.score
            "self.current_value" → self.game_object.current_value
        """
        if not self.source_path:
            return None

        path_parts = self.source_path.split(".")
        if not path_parts:
            return None

        # Começa pelo primeiro nível
        first = path_parts[0]
        if first == "self":
            obj = self.game_object
        else:
            # Procura como atributo do game_object
            obj = getattr(self.game_object, first, None)

        if obj is None:
            return None

        # Segue o caminho restante
        for part in path_parts[1:]:
            obj = getattr(obj, part, None)
            if obj is None:
                return None

        return obj

    def _on_value_changed_internal(self, value: Any) -> None:
        """Chamado quando o valor muda (auto ou event mode)."""
        self._last_value = value
        self._update_ui(value)

    def _update_ui(self, value: Any) -> None:
        """Atualiza o elemento UI com o novo valor."""
        if self._ui_element is None:
            return

        formatted = self._format_value(value)

        # Tenta chamar setter método
        if hasattr(self._ui_element, "set_text"):
            self._ui_element.set_text(str(formatted))
        elif hasattr(self._ui_element, "text"):
            self._ui_element.text = str(formatted)

        # Se for ProgressBar ou similar, tenta atualizar valor numérico
        if hasattr(self._ui_element, "set_value"):
            try:
                self._ui_element.set_value(float(value))
            except (TypeError, ValueError):
                pass

    def _format_value(self, value: Any) -> str:
        """Formata o valor usando format_string."""
        try:
            # Tenta usar format_string
            return self.format_string.format(value=value)
        except (KeyError, ValueError, TypeError):
            # Fallback: converter para string
            if isinstance(value, float) and self.precision > 0:
                return f"{value:.{self.precision}f}"
            return str(value)

    def set_on_value_changed(self, callback: Callable[[Any], None]) -> None:
        """Registra callback quando valor muda."""
        self._on_value_changed = callback

    def serialize(self) -> dict:
        """Serializa o componente para save/load."""
        data = super().serialize()
        data["source_path"] = self.source_path
        data["ui_element_name"] = self.ui_element_name
        data["bind_mode"] = self.bind_mode
        data["format_string"] = self.format_string
        data["precision"] = self.precision
        data["event_name"] = self.event_name
        return data

    def deserialize(self, data: dict) -> None:
        """Desserializa o componente após load."""
        super().deserialize(data)
        self.source_path = data.get("source_path", "")
        self.ui_element_name = data.get("ui_element_name", "")
        self.bind_mode = data.get("bind_mode", "auto")
        self.format_string = data.get("format_string", "{value}")
        self.precision = data.get("precision", 0)
        self.event_name = data.get("event_name", f"{self.source_path}_changed")
