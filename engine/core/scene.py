"""
engine/core/scene.py
────────────────────────────────────────────────────────────────
Fonte canônica da classe Scene.
Extraid de engine/core.py (legado) e expandida.

Conceito:
  Uma Scene é um contêiner de GameObjects com um ciclo de vida definido.
  Ela não conhece janela, clock, eventos globais nem renderer — esses
  detalhes pertencem à Engine e à Application.

Ciclo de vida:
    start()         ← chamado uma vez quando a cena se torna ativa
    update(dt)      ← chamado todo frame (lógica)
    draw(screen)    ← chamado todo frame (renderização)
    handle_event()  ← chamado para cada evento Pygame
    on_exit()       ← chamado quando a cena é substituída

Uso:
    from engine.core import Scene, GameObject

    class GameScene(Scene):
        def start(self):
            self.player = GameObject("Player", tag="Player")
            self.add_game_object(self.player)

        def update(self, dt):
            super().update(dt)   # propaga update para todos os GOs

        def draw(self, screen):
            screen.fill((30, 30, 30))
            super().draw(screen)  # propaga draw para todos os GOs
"""
from __future__ import annotations

from typing import List, Optional, TYPE_CHECKING

import pygame

if TYPE_CHECKING:
    from engine.core.engine import Engine
    from engine.game_object import GameObject


class Scene:
    """
    Contêiner de GameObjects. Base de todas as cenas da engine.

    Atributos públicos:
        engine       : referência à Engine que executa esta cena
        game_objects : lista flat de GOs raiz (sem filhos duplicados)
        name         : nome da cena para debug e logs
    """

    def __init__(self, name: str = "Scene") -> None:
        self.name:         str            = name
        self.engine:       Optional["Engine"] = None
        self.game_objects: List["GameObject"] = []

    # ------------------------------------------------------------------ #
    # Gerenciamento de GameObjects                                        #
    # ------------------------------------------------------------------ #

    def add_game_object(self, go: "GameObject") -> "GameObject":
        """
        Adiciona um GO à cena e aciona seu ciclo de inicialização.
        Seguro para chamar antes ou depois de start().
        """
        if go not in self.game_objects:
            self.game_objects.append(go)
        # O setter .scene dispara comp.start() nos componentes,
        # garantindo exatamente uma inicialização.
        go.scene = self
        return go

    def remove_game_object(self, go: "GameObject") -> None:
        """Remove o GO da cena sem destruí-lo."""
        if go in self.game_objects:
            self.game_objects.remove(go)
            go.scene = None

    def find(self, name: str) -> Optional["GameObject"]:
        """Busca o primeiro GO com o nome dado (busca linear)."""
        for go in self.game_objects:
            if go.name == name:
                return go
        return None

    def find_by_tag(self, tag: str) -> List["GameObject"]:
        """Retorna todos os GOs com a tag dada."""
        return [go for go in self.game_objects if go.tag == tag]

    def find_by_id(self, uid: str) -> Optional["GameObject"]:
        """Busca pelo UUID4 completo ou short_id (8 chars)."""
        for go in self.game_objects:
            if go.id == uid or go.short_id == uid:
                return go
        return None

    # ------------------------------------------------------------------ #
    # Ciclo de vida                                                       #
    # ------------------------------------------------------------------ #

    def start(self) -> None:
        """Chamado uma vez quando a cena se torna ativa."""

    def update(self, dt: float) -> None:
        """Propaga update para todos os GOs ativos."""
        for go in list(self.game_objects):
            go.update(dt)

    def draw(self, screen: pygame.Surface) -> None:
        """Propaga draw para todos os GOs ativos."""
        for go in list(self.game_objects):
            go.draw(screen)

    def handle_event(self, event: pygame.event.Event) -> None:
        """Propaga eventos Pygame. Subclasses podem sobrescrever."""

    def on_exit(self) -> None:
        """Chamado quando esta cena é substituída por outra."""

    # ------------------------------------------------------------------ #
    # repr                                                                #
    # ------------------------------------------------------------------ #

    def __repr__(self) -> str:
        return f"<Scene '{self.name}' objects={len(self.game_objects)}>"
