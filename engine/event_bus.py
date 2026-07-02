"""
EventBus — sistema de pub/sub desacoplado para comunicação interna.

Permite que sistemas da engine e scripts de jogo se comuniquem sem
referências diretas uns aos outros.

Uso:
    bus = EventBus()

    # Subscreve
    bus.subscribe("player_died", my_callback)

    # Publica
    bus.publish("player_died", score=0)

    # Remove subscrição
    bus.unsubscribe("player_died", my_callback)

O método publish() chama todos os handlers registrados para o evento
naquele instante (dispatch síncrono). Erros em handlers são isolados e
logados sem derrubar os demais handlers.
"""
from __future__ import annotations
import traceback
from collections import defaultdict
from typing import Any, Callable, DefaultDict


Handler = Callable[..., None]


class EventBus:
    """Barramento de eventos pub/sub gerenciado pela Application."""

    def __init__(self) -> None:
        self._handlers: DefaultDict[str, list[Handler]] = defaultdict(list)

    # ------------------------------------------------------------------ #
    # Subscrição
    # ------------------------------------------------------------------ #

    def subscribe(self, event: str, handler: Handler) -> None:
        """Registra `handler` para o evento `event`."""
        if handler not in self._handlers[event]:
            self._handlers[event].append(handler)

    def unsubscribe(self, event: str, handler: Handler) -> None:
        """Remove `handler` do evento `event`. No-op se não existir."""
        try:
            self._handlers[event].remove(handler)
        except ValueError:
            pass

    def unsubscribe_all(self, event: str) -> None:
        """Remove todos os handlers de um evento."""
        self._handlers.pop(event, None)

    def clear(self) -> None:
        """Remove todos os handlers de todos os eventos."""
        self._handlers.clear()

    # ------------------------------------------------------------------ #
    # Publicação
    # ------------------------------------------------------------------ #

    def publish(self, event: str, **kwargs: Any) -> None:
        """
        Dispara o evento `event` para todos os handlers registrados.
        Cada handler recebe os kwargs como argumentos nomeados.
        Erros em um handler não impedem a execução dos demais.
        """
        for handler in list(self._handlers.get(event, [])):
            try:
                handler(**kwargs)
            except Exception:  # noqa: BLE001
                traceback.print_exc()

    # ------------------------------------------------------------------ #
    # Utilitários
    # ------------------------------------------------------------------ #

    def has_subscribers(self, event: str) -> bool:
        return bool(self._handlers.get(event))

    def subscribers_count(self, event: str) -> int:
        return len(self._handlers.get(event, []))
