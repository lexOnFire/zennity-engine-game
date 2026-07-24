"""
engine/system.py
────────────────────────────────────────────────────────────────
Classe base de todos os sistemas da Zennity Engine.

Conceito:
  Um System é um processador global que opera sobre a cena ativa.
  Ele é diferente de um Component (que vive num GameObject):
    - Component  → lógica de um objeto específico
    - System     → lógica que afeta toda a cena (física, render, audio...)

Ciclo de vida:
    start()              ← chamado uma vez quando o sistema é adicionado
    update(scene, dt)    ← chamado todo frame, antes do render
    render(scene, screen)← chamado todo frame, após update
    shutdown()           ← chamado quando a Application encerra

Prioridade:
    Sistemas são executados em ordem crescente de prioridade.
    Use SystemPriority como referência:

        PHYSICS    = 100   (primeiro: move e resolve colisões)
        ANIMATION  = 200   (segundo: atualiza poses)
        RENDER     = 300   (terceiro: desenha)
        AUDIO      = 400   (quarto: toca sons)
        UI         = 500   (quinto: UI por cima de tudo)
        CUSTOM     = 1000  (livre para sistemas de jogo)

Uso básico:

    from engine.system import System, SystemPriority

    class MySystem(System):
        priority = SystemPriority.CUSTOM

        def start(self):
            Logger.info("MySystem started")

        def update(self, scene, dt):
            for go in scene.game_objects:
                ...

    # Registro na Application
    app.systems.add(MySystem())

Acessando um sistema registrado:

    my = app.systems.get(MySystem)
    my.enabled = False   # pausa sem remover
"""
from __future__ import annotations

import traceback
from typing import Dict, List, Optional, Type, TypeVar

import pygame

S = TypeVar("S", bound="System")


# ============================================================== #
#  Prioridades padrão                                            #
# ============================================================== #

class SystemPriority:
    """
    Constantes de prioridade de execução.
    Menor valor = executa primeiro.
    """
    PHYSICS   = 100
    ANIMATION = 200
    RENDER    = 300
    AUDIO     = 400
    UI        = 500
    CUSTOM    = 1000


# ============================================================== #
#  System — classe base                                          #
# ============================================================== #

class System:
    """
    Contrato base de todo sistema da engine.

    Subclasses devem sobrescrever apenas os métodos relevantes.
    Métodos não sobrescritos são no-op por padrão.
    """

    #: Ordem de execução. Menor = primeiro.
    priority: int = SystemPriority.CUSTOM

    def __init__(self) -> None:
        #: Desabilitar pausa update/render sem remover do registry.
        self.enabled: bool = True

    # ------------------------------------------------------------------ #
    # Ciclo de vida                                                       #
    # ------------------------------------------------------------------ #

    def start(self) -> None:
        """Chamado uma vez quando o sistema é adicionado ao SystemRegistry."""

    def update(self, scene, dt: float) -> None:
        """Chamado todo frame antes do render. scene = cena ativa."""

    def render(self, scene, screen: pygame.Surface) -> None:
        """Chamado todo frame após update. screen = surface da janela."""

    def shutdown(self) -> None:
        """Chamado quando a Application encerra."""

    # ------------------------------------------------------------------ #
    # Identidade                                                          #
    # ------------------------------------------------------------------ #

    @property
    def name(self) -> str:
        """Nome do sistema (padrão: nome da classe)."""
        return self.__class__.__name__

    def __repr__(self) -> str:
        return f"<{self.name} priority={self.priority} enabled={self.enabled}>"


# ============================================================== #
#  SystemRegistry — gerenciado pela Application                  #
# ============================================================== #

class SystemRegistry:
    """
    Registro ordenado de sistemas.
    Pertence à Application: app.systems

    Sistemas são armazenados em ordem crescente de priority.
    """

    def __init__(self) -> None:
        self._systems: List[System] = []
        self._index:   Dict[Type[System], System] = {}

    # ------------------------------------------------------------------ #
    # Registro                                                            #
    # ------------------------------------------------------------------ #

    def add(self, system: System) -> "SystemRegistry":
        """
        Adiciona um sistema ao registry e chama start().
        Retorna self para encadeamento:
            app.systems.add(PhysicsSystem()).add(RenderSystem())
        """
        t = type(system)
        if t in self._index:
            raise ValueError(
                f"Sistema '{system.name}' já registrado. "
                f"Remova-o antes de adicionar novamente."
            )
        self._systems.append(system)
        self._systems.sort(key=lambda s: s.priority)
        self._index[t] = system
        try:
            system.start()
        except Exception:
            traceback.print_exc()
        return self

    def remove(self, system_type: Type[S]) -> None:
        """
        Remove um sistema pelo tipo e chama shutdown().
        Sem efeito se o sistema não estiver registrado.
        """
        system = self._index.pop(system_type, None)
        if system is None:
            return
        try:
            system.shutdown()
        except Exception:
            traceback.print_exc()
        self._systems.remove(system)

    def get(self, system_type: Type[S]) -> Optional[S]:
        """Retorna o sistema pelo tipo, ou None se não registrado."""
        return self._index.get(system_type)  # type: ignore[return-value]

    def has(self, system_type: Type[System]) -> bool:
        return system_type in self._index

    # ------------------------------------------------------------------ #
    # Execução                                                            #
    # ------------------------------------------------------------------ #

    def run_update(self, scene, dt: float) -> None:
        """Executa update() em todos os sistemas habilitados, em ordem."""
        for system in self._systems:
            if not system.enabled:
                continue
            try:
                system.update(scene, dt)
            except Exception:
                traceback.print_exc()

    def run_render(self, scene, screen: pygame.Surface) -> None:
        """Executa render() em todos os sistemas habilitados, em ordem."""
        for system in self._systems:
            if not system.enabled:
                continue
            try:
                system.render(scene, screen)
            except Exception:
                traceback.print_exc()

    def shutdown_all(self) -> None:
        """Chama shutdown() em todos os sistemas (usado pelo Application)."""
        for system in reversed(self._systems):
            try:
                system.shutdown()
            except Exception:
                traceback.print_exc()
        self._systems.clear()
        self._index.clear()

    # ------------------------------------------------------------------ #
    # Inspecao                                                            #
    # ------------------------------------------------------------------ #

    def __len__(self) -> int:
        return len(self._systems)

    def __iter__(self):
        return iter(self._systems)

    def __repr__(self) -> str:
        names = ", ".join(s.name for s in self._systems)
        return f"<SystemRegistry [{names}]>"
