"""
engine/event_bus.py
────────────────────────────────────────────────────────────────
Barramento central de eventos da Zennity Engine.

Conceito:
  O EventBus é a espinha dorsal de comunicação entre sistemas.
  Nenhum sistema precisa importar outro — eles apenas publicam e escutam
  eventos nomeados.

Modos de despacho:
  emit() / publish()  → síncrono: listeners chamados imediatamente.
  emit_deferred()     → adiado: entra na fila, despachado em flush().

Uso básico:

    from engine.event_bus import EventBus

    # Inscrição
    def on_death(killer: str, victim: str):
        print(f"{victim} morreu para {killer}")

    EventBus.subscribe("player.death", on_death)

    # Emissão síncrona
    EventBus.emit("player.death", killer="spike", victim="player")

    # Emissão adiada (despachada no flush())
    EventBus.emit_deferred("enemy.spawn", pos=(100, 200), type="slime")

    # Uma só vez
    EventBus.once("game.start", lambda: print("Começou!"))

    # Cancelar
    EventBus.unsubscribe("player.death", on_death)

    # Limpar um evento
    EventBus.clear("player.death")

    # Limpar tudo
    EventBus.clear()

Integração com Application:
  Application.run() chama EventBus.flush() ao final de cada frame.

    # publish() mantido como alias para retrocompatibilidade.
"""
from __future__ import annotations

import traceback
from collections import defaultdict, deque
from typing import Any, Callable, DefaultDict, Deque, Dict, List, Optional, Tuple

_Callback = Callable[..., None]
_Event    = str


class EventBus:
    """
    Barramento global de eventos.

    Todos os métodos são @classmethod — não instanciar.
    (Instâncias pré-existentes continuam funcionando via alias publish().)
    """

    # ----- estado de classe (global) ----------------------------------- #
    _listeners: DefaultDict[_Event, List[_Callback]] = defaultdict(list)
    _once:      DefaultDict[_Event, List[_Callback]] = defaultdict(list)
    _queue:     Deque[Tuple[_Event, Dict[str, Any]]] = deque()

    # ----- estado de instância (retrocompat) --------------------------- #
    def __init__(self) -> None:
        # Instâncias delegam para o estado global de classe.
        pass

    # ------------------------------------------------------------------ #
    # Inscrição                                                           #
    # ------------------------------------------------------------------ #

    @classmethod
    def subscribe(cls, event: _Event, callback: _Callback) -> None:
        """Inscreve callback no evento. Ignora duplicatas."""
        if callback not in cls._listeners[event]:
            cls._listeners[event].append(callback)

    @classmethod
    def once(cls, event: _Event, callback: _Callback) -> None:
        """Inscreve callback que se auto-remove após a primeira chamada."""
        cls._once[event].append(callback)
        cls.subscribe(event, callback)

    @classmethod
    def unsubscribe(cls, event: _Event, callback: _Callback) -> None:
        """Remove callback do evento. Sem efeito se não estiver inscrito."""
        listeners = cls._listeners.get(event)
        if listeners and callback in listeners:
            listeners.remove(callback)
        once = cls._once.get(event)
        if once and callback in once:
            once.remove(callback)

    # ------------------------------------------------------------------ #
    # Emissão                                                             #
    # ------------------------------------------------------------------ #

    @classmethod
    def emit(cls, event: _Event, **kwargs: Any) -> None:
        """
        Despacha o evento imediatamente (síncrono).
        Exceções em listeners são capturadas sem interromper os demais.
        """
        for callback in list(cls._listeners.get(event, [])):
            try:
                callback(**kwargs)
            except Exception:
                traceback.print_exc()
        # Remove callbacks "once"
        for cb in list(cls._once.get(event, [])):
            cls.unsubscribe(event, cb)

    @classmethod
    def emit_deferred(cls, event: _Event, **kwargs: Any) -> None:
        """Enfileira o evento para despacho no próximo flush()."""
        cls._queue.append((event, kwargs))

    @classmethod
    def flush(cls) -> None:
        """
        Despacha todos os eventos adiados da fila.
        Chamado por Application.run() ao final de cada frame.
        """
        while cls._queue:
            event, kwargs = cls._queue.popleft()
            cls.emit(event, **kwargs)

    # ------------------------------------------------------------------ #
    # Limpeza                                                             #
    # ------------------------------------------------------------------ #

    @classmethod
    def clear(cls, event: Optional[_Event] = None) -> None:
        """
        clear("player.death") → remove listeners deste evento.
        clear()               → remove tudo.
        """
        if event is not None:
            cls._listeners.pop(event, None)
            cls._once.pop(event, None)
        else:
            cls._listeners.clear()
            cls._once.clear()
            cls._queue.clear()

    # Alias retrocompat (instâncias pré-existentes)
    def unsubscribe_all(self, event: _Event) -> None:
        EventBus.clear(event)

    # ------------------------------------------------------------------ #
    # Inspecão                                                            #
    # ------------------------------------------------------------------ #

    @classmethod
    def listener_count(cls, event: _Event) -> int:
        return len(cls._listeners.get(event, []))

    @classmethod
    def has_listeners(cls, event: _Event) -> bool:
        return cls.listener_count(event) > 0

    @classmethod
    def pending_count(cls) -> int:
        """Número de eventos adiados aguardando flush()."""
        return len(cls._queue)

    # ------------------------------------------------------------------ #
    # Alias retrocompat: publish() → emit()                              #
    # ------------------------------------------------------------------ #

    def publish(self, event: _Event, **kwargs: Any) -> None:
        """Alias de emit() mantido para retrocompatibilidade."""
        EventBus.emit(event, **kwargs)

    def has_subscribers(self, event: _Event) -> bool:
        return EventBus.has_listeners(event)

    def subscribers_count(self, event: _Event) -> int:
        return EventBus.listener_count(event)
